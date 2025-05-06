"""Employer Blueprint Routes.

This module contains all routes related to employer functionality including:
- Job posting and management
- Application review
- Employer dashboard
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Job, Application, User
from forms import JobForm
from utils import logger, save_company_logo
from blueprints.auth.routes import login_required, role_required
from werkzeug.utils import secure_filename
import os

employer_bp = Blueprint('employer', __name__)

@employer_bp.route('/post-job-redirect')
@login_required
@role_required('employer', 'admin')
def post_job_redirect():
    """Handle navbar job posting redirect with role-based destination.

    Returns:
        redirect: 
            - Admins: Redirect to admin job management
            - Employers: Redirect to job creation form

    Side Effects:
        - Logs redirect action
        - Flashes info message for admin users

    Example:
        /post-job-redirect
    """
    # This route is just a convenience for the navbar link
    if session['role'] == 'admin':
        # Admins can post jobs but they're redirected to the admin interface
        logger.info(f"Admin {session['user_id']} redirected to admin job creation")
        flash('As an admin, you can create jobs through the admin interface.', 'info')
        return redirect(url_for('admin.admin_jobs'))
    else:
        logger.info(f"Employer {session['user_id']} redirected to job creation form")
        return redirect(url_for('employer.new_job'))

@employer_bp.route('/jobs/new', methods=['GET', 'POST'])
@login_required
@role_required('employer', 'admin')
def new_job():
    """Handle job creation form display and submission.

    Methods:
        GET: Display job creation form
        POST: Process form submission and create new job

    Returns:
        GET: Rendered job creation template
        POST: Redirect to employer dashboard on success

    Side Effects:
        - Creates new Job record in database using GraphQL
        - Handles company logo file upload
        - Logs creation attempts
        - Flashes success/error messages

    Example:
        /jobs/new
    """
    form = JobForm()

    # For admin users, add a dropdown to select which employer posts the job
    if session['role'] == 'admin':
        pass
    else:
        pass

    if form.validate_on_submit():
        try:
            # Validate salary format
            if form.salary.data and not form.salary.data.startswith('$'):
                logger.warning(
                    f"Invalid salary format attempted: {form.salary.data}")
                form.salary.data = '$' + form.salary.data

            # Handle logo upload
            company_logo = 'img/company_logos/default.png'  # Default logo
            if form.company_logo.data:
                logo_filename = save_company_logo(form.company_logo.data)
                if logo_filename:
                    company_logo = f'img/company_logos/{logo_filename}'
                    logger.info(
                        f"Company logo uploaded for new job: {logo_filename}")
                else:
                    logger.error(
                        f"Failed to save company logo for new job")

            # Use GraphQL resolver directly instead of making a database operation
            from graphql_api.resolvers.job_resolvers import resolve_create_job

            # Prepare input for GraphQL mutation
            job_input = {
                "title": form.title.data,
                "company": form.company.data,
                "location": form.location.data,
                "description": form.description.data,
                "salary": form.salary.data,
                "category": form.category.data,
                "companyLogo": company_logo
            }

            # Call the GraphQL resolver directly
            result = resolve_create_job(None, None, input=job_input)

            if result.get("job"):
                job = result["job"]
                logger.info(
                    f"New job created: {job.id} - {job.title} at {job.company} by user {session['user_id']} via GraphQL")
                flash('Job posted successfully!', 'success')
                return redirect(url_for('employer.my_jobs'))
            else:
                # Job creation failed
                errors = result.get("errors", ["Unknown error"])
                logger.error(f"Error creating job via GraphQL: {errors}")
                flash(f'Error creating job: {", ".join(errors)}', 'danger')

        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            flash('An error occurred while posting the job.', 'danger')

    return render_template('new_job.html', form=form)

@employer_bp.route('/my_jobs')
@login_required
@role_required('employer', 'admin')
def my_jobs():
    """Display all jobs posted by the current employer/admin.

    Returns:
        rendered_template: Jobs list page with all jobs posted by user

    Side Effects:
        - Logs access to job list
        - Retrieves jobs from database using GraphQL

    Example:
        /my_jobs
    """
    logger.info(f"User {session['user_id']} accessing their posted jobs")

    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.user_resolvers import resolve_user

    # Get current user using the resolver directly
    user = resolve_user(None, None, id=session['user_id'])

    # Get jobs posted by the user
    jobs = user.jobs_posted if user else []

    logger.info(f"Found {len(jobs)} jobs posted by user {session['user_id']} via GraphQL")
    return render_template('my_jobs.html', jobs=jobs, form=JobForm())

@employer_bp.route('/jobs/<int:job_id>/applications')
@login_required
@role_required('employer', 'admin')
def job_applications(job_id):
    """Display applications for a specific job.

    Args:
        job_id (int): ID of job to view applications for

    Returns:
        rendered_template: Applications list page

    Side Effects:
        - Verifies job ownership (unless admin)
        - Logs access to applications
        - Retrieves applications using GraphQL

    Example:
        /jobs/42/applications
    """
    logger.info(f"User {session['user_id']} accessing applications for job {job_id}")

    # Use GraphQL resolvers directly instead of making database queries
    from graphql_api.resolvers.job_resolvers import resolve_job
    from graphql_api.resolvers.application_resolvers import resolve_job_applications

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    # Only allow access if user is admin or the job poster
    if session['role'] != 'admin' and job.poster_id != session['user_id']:
        logger.warning(f"Unauthorized access attempt: User {session['user_id']} tried to view applications for job {job_id} posted by user {job.poster_id}")
        flash('You do not have permission to view these applications.', 'danger')
        return redirect(url_for('employer.my_jobs'))

    # Get applications using the resolver directly
    applications = resolve_job_applications(None, None, jobId=job_id)

    logger.info(f"Found {len(applications)} applications for job {job_id} via GraphQL")
    return render_template('job_applications.html', job=job, applications=applications)

@employer_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('employer', 'admin')
def delete_job(job_id):
    """Delete a job posting and its applications.

    Args:
        job_id (int): ID of job to delete

    Returns:
        redirect: Back to jobs list with success/error message

    Side Effects:
        - Deletes job and all its applications using GraphQL
        - Logs deletion attempts
        - Flashes confirmation messages

    Example:
        POST /jobs/42/delete
    """
    # Use GraphQL resolvers directly instead of making database queries
    from graphql_api.resolvers.job_resolvers import resolve_job, resolve_delete_job

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    # Check if the user has permission to delete this job
    if session['role'] != 'admin' and job.poster_id != session['user_id']:
        logger.warning(
            f"Unauthorized job deletion attempt: User {session['user_id']} tried to delete job {job_id} posted by user {job.poster_id}")
        flash('You do not have permission to delete this job.', 'danger')
        return redirect(url_for('employer.my_jobs'))

    try:
        # Delete the job using GraphQL mutation
        result = resolve_delete_job(None, None, id=job_id)

        if result.get('success'):
            logger.info(
                f"Job {job_id} ({job.title} at {job.company}) deleted by user {session['user_id']} via GraphQL")
            flash('Job deleted successfully!', 'success')
        else:
            # Job deletion failed
            errors = result.get('errors', ['Unknown error'])
            logger.error(f"Error deleting job {job_id} via GraphQL: {errors}")
            flash(f'Error deleting job: {", ".join(errors)}', 'danger')
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        flash('An error occurred while deleting the job.', 'danger')

    return redirect(url_for('employer.my_jobs'))

@employer_bp.route('/applications/<int:application_id>/update', methods=['POST'])
@login_required
@role_required('employer', 'admin')
def update_application(application_id):
    """Update an application's status or notes.

    Args:
        application_id (int): ID of application to update

    Returns:
        redirect: Back to applications page with success/error message

    Side Effects:
        - Updates application in database using GraphQL
        - Logs update attempts
        - Flashes success/error messages

    Valid Status Values:
        - pending
        - reviewed  
        - rejected
        - shortlisted
        - hired

    Example:
        POST /applications/42/update
        Form Data: {'status': 'shortlisted', 'notes': 'Strong candidate'}
    """
    # Use GraphQL resolvers directly instead of making database queries
    from graphql_api.resolvers.application_resolvers import resolve_application, resolve_update_application_status
    from graphql_api.resolvers.job_resolvers import resolve_job

    # Get application using the resolver directly
    application = resolve_application(None, None, id=application_id)

    if not application:
        # If application not found, return 404
        from flask import abort
        abort(404)

    # Get job using the resolver directly
    job = resolve_job(None, None, id=application.job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    # Security check: Ensure the employer owns this job or is an admin
    if session['role'] != 'admin' and job.poster_id != session['user_id']:
        logger.warning(f"Unauthorized application status update attempt: User {session['user_id']} tried to update application {application_id} for job {job.id} posted by {job.poster_id}")
        flash('You do not have permission to update this application.', 'danger')
        return redirect(url_for('employer.job_applications', job_id=job.id))

    # Validate the status input
    new_status = request.form.get('status')
    valid_statuses = ['pending', 'reviewed', 'rejected', 'shortlisted', 'hired']

    if not new_status or new_status not in valid_statuses:
        logger.warning(f"Invalid status update attempt: User {session['user_id']} tried to set invalid status '{new_status}' for application {application_id}")
        flash('Invalid status.', 'danger')
        return redirect(url_for('employer.job_applications', job_id=job.id))

    try:
        # Update the application status using GraphQL mutation
        result = resolve_update_application_status(None, None, id=application_id, status=new_status)

        if result.get('application'):
            logger.info(f"Employer {session['user_id']} updated application {application_id} status to {new_status} via GraphQL")
            flash(f'Application status updated to {new_status}.', 'success')
        else:
            # Application update failed
            errors = result.get('errors', ['Unknown error'])
            logger.error(f"Error updating application {application_id} via GraphQL: {errors}")
            flash(f'Error updating application: {", ".join(errors)}', 'danger')
    except Exception as e:
        logger.error(f"Error updating application {application_id}: {str(e)}")
        flash('An error occurred while updating the application.', 'danger')

    return redirect(url_for('employer.job_applications', job_id=job.id))
