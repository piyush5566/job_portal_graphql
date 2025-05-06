from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from models import db, Job, Application
from utils import logger, upload_to_gcs, allowed_file
from blueprints.auth.routes import login_required, role_required
from forms import ApplicationForm

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/list')
def jobs_list():
    location = request.args.get('location')
    category = request.args.get('category')
    company = request.args.get('company')

    logger.info(f"Jobs page accessed with filters - location: {location}, category: {category}, company: {company}")

    # Use GraphQL resolver directly instead of making an HTTP request
    from graphql_api.resolvers.job_resolvers import resolve_jobs
    from ariadne import graphql_sync
    from graphql_api.schema import type_defs
    from graphql_api.resolvers import resolvers
    from ariadne import make_executable_schema

    # Get jobs using the resolver directly
    jobs = resolve_jobs(None, None, location=location, category=category, company=company)

    logger.info(f"Found {len(jobs)} jobs matching the criteria via GraphQL resolver")
    return render_template('jobs.html', jobs=jobs)

# REST API endpoint for job search has been replaced with GraphQL
# Frontend now uses the GraphQL API endpoint at /graphql
# See static/js/search.js for the implementation
# and graphql_api/resolvers/job_resolvers.py for the resolver

@jobs_bp.route('/<int:job_id>')
def job_detail(job_id):
    """
    Display detailed information about a specific job.

    Args:
        job_id: ID of the job to display

    Returns:
        Rendered template with job details

    Side Effects:
        - Logs job detail page access
        - For admin users, logs application count
        - For job seekers, checks and logs application status

    Example:
        /jobs/42
    """
    logger.info(f"Job detail page accessed for job_id: {job_id}")

    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.job_resolvers import resolve_job

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    # Log application count for admin users
    if session.get('role') == 'admin':
        logger.info(f"Admin viewing job {job_id} with {len(job.applications)} applications")

    # Check if the current user has already applied
    has_applied = False
    if session.get('user_id') and session.get('role') == 'job_seeker':
        # Use GraphQL resolver to check if user has applied
        from graphql_api.resolvers.application_resolvers import resolve_my_applications
        my_applications = resolve_my_applications(None, None)
        has_applied = any(app.job_id == int(job_id) for app in my_applications)
        logger.info(f"User {session['user_id']} has {'already applied' if has_applied else 'not applied'} to job {job_id}")

    return render_template('job_detail.html', job=job, has_applied=has_applied)

@jobs_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('job_seeker')
def apply_job(job_id):
    """
    Handle job application submissions.

    Args:
        job_id: ID of the job being applied to

    Returns:
        Rendered form (GET) or redirect (POST)

    Side Effects:
        - Validates and saves resume file
        - Creates application record
        - Prevents duplicate applications
        - Logs application attempts and results
        - Flashes success/error messages

    Example:
        /jobs/apply/42
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.job_resolvers import resolve_job
    from graphql_api.resolvers.application_resolvers import resolve_create_application, resolve_my_applications

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    form = ApplicationForm()

    # Check if already applied using GraphQL resolver
    my_applications = resolve_my_applications(None, None)
    already_applied = any(app.job_id == int(job_id) for app in my_applications)

    if already_applied:
        flash('You have already applied to this job.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    if form.validate_on_submit():
        resume_path_for_db = None # Will store GCS object name or None
        gcs_upload_successful = True # Assume success if no file or GCS disabled
        try:
            # --- Handle Resume Upload ---
            resume_file = form.resume.data
            if resume_file:
                # Check config if GCS should be used
                enable_gcs = current_app.config.get('ENABLE_GCS_UPLOAD', False)
                gcs_bucket_name = current_app.config.get('GCS_BUCKET_NAME')

                if enable_gcs and gcs_bucket_name:
                    logger.info(f"Attempting GCS upload for application to job {job_id} by user {session['user_id']}")
                    # Attempt direct upload to GCS
                    gcs_object_name = upload_to_gcs(
                        file_storage=resume_file,
                        user_id=session['user_id'],
                        gcs_bucket_name=gcs_bucket_name
                    )

                    if gcs_object_name:
                        resume_path_for_db = gcs_object_name.removeprefix('resumes/') # Store GCS path
                        logger.info(f"GCS upload successful for job {job_id}, user {session['user_id']}. Path: {resume_path_for_db}")
                    else:
                        # GCS upload failed
                        gcs_upload_successful = False
                        logger.error(f"GCS upload failed for job {job_id}, user {session['user_id']}")
                        flash('There was an error uploading your resume to cloud storage. Please try again.', 'danger')
                else:
                    logger.warning(f"Resume provided for job {job_id}, user {session['user_id']}, but GCS upload is disabled or bucket not configured. Resume not saved.")

            # --- Create Application Record using GraphQL mutation (only if GCS upload was successful or no resume) ---
            if gcs_upload_successful:
                # Prepare input for GraphQL mutation
                application_input = {
                    "jobId": str(job_id),
                    "resumePath": resume_path_for_db
                }

                # Call the GraphQL resolver directly
                result = resolve_create_application(None, None, input=application_input)

                if result.get("application"):
                    logger.info(f"User {session['user_id']} successfully applied to job {job_id} via GraphQL. Resume path: {resume_path_for_db}")
                    flash('Your application has been submitted!', 'success')
                    return redirect(url_for('job_seeker.my_applications'))
                else:
                    # Application creation failed
                    errors = result.get("errors", ["Unknown error"])
                    logger.error(f"Error creating application via GraphQL: {errors}")
                    flash(f'Error submitting application: {", ".join(errors)}', 'danger')
            # else: GCS upload failed, already flashed message, stay on page

        except Exception as e:
            logger.error(f"Error processing application for job {job_id}, user {session['user_id']}: {str(e)}")
            flash('An unexpected error occurred while submitting your application.', 'danger')

    elif request.method == 'POST':
        # Log validation errors if POST request failed validation
        logger.warning(f"Application form validation failed for job {job_id}, user {session['user_id']}: {form.errors}")
        flash('Please correct the errors in the form.', 'warning')

    return render_template('apply_job.html', form=form, job=job)
