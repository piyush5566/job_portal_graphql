from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Job, Application
from forms import UserEditForm, JobForm, AdminRegistrationForm
from utils import logger, save_company_logo
from blueprints.auth.routes import login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    """
    Render the admin dashboard.

    Returns:
        Rendered admin dashboard template

    Side Effects:
        - Logs dashboard access

    Example:
        /admin/dashboard
    """
    logger.info(f"Admin {session['user_id']} accessed the admin dashboard")
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
@role_required('admin')
def admin_users():
    """
    Display all users for admin management.

    Returns:
        Rendered template with list of all users

    Side Effects:
        - Logs access to user management
        - Retrieves all users from database using GraphQL

    Example:
        /admin/users
    """
    logger.info(f"Admin {session['user_id']} accessed the users management page")

    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.user_resolvers import resolve_users

    # Get users using the resolver directly
    users = resolve_users(None, None)

    logger.info(f"Retrieved {len(users)} users for admin view via GraphQL")
    return render_template('admin/users.html', users=users, form=UserEditForm())

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_new_user():
    """
    Handle creation of new users by admin.

    Returns:
        Rendered template (GET) or redirect (POST)

    Side Effects:
        - Creates new user record in database using GraphQL
        - Logs admin actions
        - Flashes success/error messages

    Example:
        /admin/users/new
    """
    logger.info(f"Admin {session['user_id']} accessed the new user creation page")
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        # Use GraphQL resolver directly instead of making a database query
        from graphql_api.resolvers.user_resolvers import resolve_users, resolve_create_user

        # Check if email already exists using GraphQL
        users = resolve_users(None, None)
        email_exists = any(user.email == form.email.data for user in users)

        if email_exists:
            logger.warning(f"Admin user creation failed: Email {form.email.data} already exists")
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.admin_new_user'))

        # Prepare input for GraphQL mutation
        user_input = {
            "username": form.username.data,
            "email": form.email.data,
            "password": form.password.data,
            "role": form.role.data,
            "profilePicture": "img/profiles/default.jpg"
        }

        # Call the GraphQL resolver directly
        result = resolve_create_user(None, None, input=user_input)

        if result.get("user"):
            user = result["user"]
            logger.info(f"Admin {session['user_id']} created new user: {user.id} ({user.username}, {user.email}) with role {user.role}")
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.admin_users'))
        else:
            # User creation failed
            errors = result.get("errors", ["Unknown error"])
            logger.error(f"Error creating user via GraphQL: {errors}")
            flash(f'Error creating user: {", ".join(errors)}', 'danger')

    if form.errors:
        logger.warning(f"Admin user creation form validation failed: {form.errors}")

    return render_template('admin/new_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_user(user_id):
    """
    Handle editing user details as an admin.

    Args:
        user_id: ID of the user to edit

    Returns:
        Rendered template (GET) or redirect (POST)

    Side Effects:
        - Updates user record in database using GraphQL
        - Logs admin actions
        - Flashes success/error messages

    Example:
        /admin/users/42/edit
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.user_resolvers import resolve_user, resolve_users, resolve_update_user

    # Get user using the resolver directly
    user = resolve_user(None, None, id=user_id)

    if not user:
        # If user not found, return 404
        from flask import abort
        abort(404)

    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        # Check for email conflicts using GraphQL
        users = resolve_users(None, None)
        email_exists = any(u.email == form.email.data and u.id != int(user_id) for u in users)

        if email_exists:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.admin_edit_user', user_id=user_id))

        try:
            # Prepare input for GraphQL mutation
            user_input = {
                "username": form.username.data,
                "email": form.email.data,
                "role": form.role.data,
                # We don't include password here as we're not changing it
                # We don't include profilePicture here as we're not changing it
            }

            # Call the GraphQL resolver directly
            result = resolve_update_user(None, None, id=user_id, input=user_input)

            if result.get("user"):
                updated_user = result["user"]
                logger.info(
                    f"Admin {session['user_id']} updated user {user_id}: {updated_user.username}, {updated_user.email}, role: {updated_user.role}")
                flash('User updated successfully.', 'success')
                return redirect(url_for('admin.admin_users'))
            else:
                # User update failed
                errors = result.get("errors", ["Unknown error"])
                logger.error(f"Error updating user {user_id} via GraphQL: {errors}")
                flash(f'Error updating user: {", ".join(errors)}', 'danger')
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            flash('An error occurred while updating the user.', 'danger')

    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_user(user_id):
    """
    Handle user deletion by admin.

    Args:
        user_id: ID of the user to delete

    Returns:
        Redirect to users list

    Side Effects:
        - Removes user record from database using GraphQL
        - Prevents self-deletion
        - Logs admin actions
        - Flashes success/error messages

    Example:
        POST /admin/users/42/delete
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.user_resolvers import resolve_user, resolve_delete_user

    # Get user using the resolver directly
    user = resolve_user(None, None, id=user_id)

    if not user:
        # If user not found, return 404
        from flask import abort
        abort(404)

    # Prevent admins from deleting themselves
    if int(user_id) == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.admin_users'))

    try:
        # Call the GraphQL resolver directly
        result = resolve_delete_user(None, None, id=user_id)

        if result.get("success"):
            logger.info(
                f"Admin {session['user_id']} deleted user {user_id}: {user.username}, {user.email}")
            flash('User deleted successfully.', 'success')
        else:
            # User deletion failed
            errors = result.get("errors", ["Unknown error"])
            logger.error(f"Error deleting user {user_id} via GraphQL: {errors}")
            flash(f'Error deleting user: {", ".join(errors)}', 'danger')
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash('An error occurred while deleting the user.', 'danger')

    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/jobs')
@login_required
@role_required('admin')
def admin_jobs():
    """
    Display all job listings for admin management.

    Returns:
        Rendered template with list of all jobs

    Side Effects:
        - Logs access to job management
        - Retrieves all jobs from database using GraphQL

    Example:
        /admin/jobs
    """
    logger.info(f"Admin {session['user_id']} accessed the jobs management page")

    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.job_resolvers import resolve_jobs

    # Get jobs using the resolver directly
    jobs = resolve_jobs(None, None)

    logger.info(f"Retrieved {len(jobs)} jobs for admin view via GraphQL")
    return render_template('admin/jobs.html', jobs=jobs, form=JobForm())

@admin_bp.route('/jobs/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_create_job():
    """
    Handle job creation from admin interface.

    Returns:
        GET: Rendered job creation form
        POST: Redirect to jobs list or re-render form with errors

    Side Effects:
        - Creates new job record if validation passes using GraphQL
        - Logs creation attempts (success/failure)
        - Flashes success/error messages
    """
    form = JobForm()

    if form.validate_on_submit():
        try:
            # Handle file upload if present
            logo_filename = None
            if form.company_logo.data:
                logo_filename = save_company_logo(form.company_logo.data)
                logger.info(f"Saved company logo: {logo_filename}")

            # Use GraphQL resolver directly instead of making a database operation
            from graphql_api.resolvers.job_resolvers import resolve_create_job

            # Prepare input for GraphQL mutation
            job_input = {
                "title": form.title.data,
                "description": form.description.data,
                "salary": form.salary.data,
                "location": form.location.data,
                "category": form.category.data,
                "company": form.company.data,
                "companyLogo": logo_filename if logo_filename else "img/company_logos/default.png"
            }

            # Call the GraphQL resolver directly
            result = resolve_create_job(None, None, input=job_input)

            if result.get("job"):
                job = result["job"]
                logger.info(f"Admin {session['user_id']} created new job ID {job.id}")
                flash('Job created successfully!', 'success')
                return redirect(url_for('admin.admin_jobs'))
            else:
                # Job creation failed
                errors = result.get("errors", ["Unknown error"])
                logger.error(f"Error creating job via GraphQL: {errors}")
                flash(f'Error creating job: {", ".join(errors)}', 'danger')

        except Exception as e:
            logger.error(f"Job creation failed: {str(e)}")
            flash('An error occurred while creating the job.', 'danger')

    return render_template('admin/create_job.html', form=form)


@admin_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_job(job_id):
    """
    Handle editing job listings as an admin.

    Args:
        job_id: ID of the job to edit

    Returns:
        Rendered template (GET) or redirect (POST)

    Side Effects:
        - Updates job record in database using GraphQL
        - Logs admin actions
        - Flashes success/error messages

    Example:
        /admin/jobs/15/edit
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.job_resolvers import resolve_job, resolve_update_job

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    form = JobForm(obj=job)

    if form.validate_on_submit():
        try:
            # Prepare input for GraphQL mutation
            job_input = {
                "title": form.title.data,
                "description": form.description.data,
                "salary": form.salary.data,
                "location": form.location.data,
                "category": form.category.data,
                "company": form.company.data,
                # We don't include companyLogo here as we're not changing it
            }

            # Call the GraphQL resolver directly
            result = resolve_update_job(None, None, id=job_id, input=job_input)

            if result.get("job"):
                updated_job = result["job"]
                logger.info(
                    f"Admin {session['user_id']} updated job {job_id}: {updated_job.title} at {updated_job.company}")
                flash('Job updated successfully.', 'success')
                return redirect(url_for('admin.admin_jobs'))
            else:
                # Job update failed
                errors = result.get("errors", ["Unknown error"])
                logger.error(f"Error updating job {job_id} via GraphQL: {errors}")
                flash(f'Error updating job: {", ".join(errors)}', 'danger')
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            flash('An error occurred while updating the job.', 'danger')

    return render_template('admin/edit_job.html', form=form, job=job)

@admin_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_job(job_id):
    """
    Handle job deletion by admin (including associated applications).

    Args:
        job_id: ID of the job to delete

    Returns:
        Redirect to jobs list

    Side Effects:
        - Removes job record and associated applications from database using GraphQL
        - Logs admin actions
        - Flashes success/error messages

    Example:
        POST /admin/jobs/15/delete
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.job_resolvers import resolve_job, resolve_delete_job

    # Get job using the resolver directly
    job = resolve_job(None, None, id=job_id)

    if not job:
        # If job not found, return 404
        from flask import abort
        abort(404)

    try:
        # Call the GraphQL resolver directly to delete the job
        # Note: The GraphQL resolver will handle deleting associated applications
        result = resolve_delete_job(None, None, id=job_id)

        if result.get("success"):
            logger.info(
                f"Admin {session['user_id']} deleted job {job_id}: {job.title} at {job.company}")
            flash('Job deleted successfully.', 'success')
        else:
            # Job deletion failed
            errors = result.get("errors", ["Unknown error"])
            logger.error(f"Error deleting job {job_id} via GraphQL: {errors}")
            flash(f'Error deleting job: {", ".join(errors)}', 'danger')
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        flash('An error occurred while deleting the job.', 'danger')

    return redirect(url_for('admin.admin_jobs'))

@admin_bp.route('/applications')
@login_required
@role_required('admin')
def admin_applications():
    """
    Display all job applications for admin management.

    Returns:
        Rendered template with list of all applications

    Side Effects:
        - Logs access to application management
        - Retrieves all applications from database using GraphQL

    Example:
        /admin/applications
    """
    logger.info(f"Admin {session['user_id']} accessed the applications management page")

    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.application_resolvers import resolve_applications

    # Get applications using the resolver directly
    applications = resolve_applications(None, None)

    logger.info(f"Retrieved {len(applications)} applications for admin view via GraphQL")
    return render_template('admin/applications.html', applications=applications)

@admin_bp.route('/applications/<int:application_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_application(application_id):
    """
    Update application status as admin.

    Args:
        application_id: ID of the application to update

    Returns:
        Redirect to applications list

    Side Effects:
        - Updates application status in database using GraphQL
        - Validates status against allowed values
        - Logs admin actions
        - Flashes success/error messages

    Example:
        POST /admin/applications/42/update
    """
    # Use GraphQL resolver directly instead of making a database query
    from graphql_api.resolvers.application_resolvers import resolve_application, resolve_update_application_status

    # Get application using the resolver directly
    application = resolve_application(None, None, id=application_id)

    if not application:
        # If application not found, return 404
        from flask import abort
        abort(404)

    new_status = request.form.get('status')

    # Validate status with strict input validation
    valid_statuses = ['pending', 'reviewed', 'rejected', 'shortlisted', 'hired']
    if not new_status or new_status not in valid_statuses:
        logger.warning(f"Admin {session['user_id']} attempted invalid application status update: '{new_status}' for application {application_id}")
        flash('Invalid application status.', 'danger')
        return redirect(url_for('admin.admin_applications'))

    previous_status = application.status

    try:
        # Call the GraphQL resolver directly
        result = resolve_update_application_status(None, None, id=application_id, status=new_status)

        if result.get("application"):
            logger.info(f"Admin {session['user_id']} updated application {application_id} status from '{previous_status}' to '{new_status}' via GraphQL")
            flash(f'Application status updated to {new_status}.', 'success')
        else:
            # Application update failed
            errors = result.get("errors", ["Unknown error"])
            logger.error(f"Error updating application {application_id} via GraphQL: {errors}")
            flash(f'Error updating application: {", ".join(errors)}', 'danger')
    except Exception as e:
        logger.error(f"Error updating application {application_id}: {str(e)}")
        flash('An error occurred while updating the application.', 'danger')

    return redirect(url_for('admin.admin_applications'))
