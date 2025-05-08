"""
Application-related GraphQL resolvers.

This module contains resolver functions for Application-related GraphQL operations:
- Queries: application, applications, myApplications, jobApplications
- Mutations: createApplication, updateApplicationStatus, deleteApplication
- Field resolvers for the Application type
"""

from ariadne import QueryType, MutationType, ObjectType
from flask import session
from models import Application, Job, User, db
from datetime import datetime, timezone

# Initialize types
query = QueryType()
mutation = MutationType()
application_type = ObjectType("Application")

# Query resolvers
@query.field("application")
def resolve_application(_, info, id):
    """Resolver for application query - fetches an application by ID."""
    return db.session.get(Application, id)

@query.field("applications")
def resolve_applications(_, info):
    """Resolver for applications query - fetches all applications (admin only)."""
    # Check if user is admin
    user_id = session.get('user_id')
    if not user_id:
        return []
    
    user = db.session.get(User, user_id)
    if not user or user.role != 'admin':
        return []
    
    return Application.query.all()

@query.field("myApplications")
def resolve_my_applications(_, info):
    """Resolver for myApplications query - fetches applications for the current user."""
    user_id = session.get('user_id')
    if not user_id:
        return []
    
    return Application.query.filter_by(applicant_id=user_id).all()

@query.field("jobApplications")
def resolve_job_applications(_, info, jobId):
    """Resolver for jobApplications query - fetches applications for a specific job."""
    user_id = session.get('user_id')
    if not user_id:
        return []
    
    job = db.session.get(Job, jobId)
    if not job:
        return []
    
    user = db.session.get(User, user_id)
    # Only admin or the job poster can see applications
    if not user or (user.role != 'admin' and job.poster_id != user_id):
        return []
    
    return Application.query.filter_by(job_id=jobId).all()

# Mutation resolvers
@mutation.field("createApplication")
def resolve_create_application(_, info, input):
    """Resolver for createApplication mutation - creates a new job application."""
    try:
        # Check if user is logged in and is a job seeker
        user_id = session.get('user_id')
        if not user_id:
            return {"application": None, "errors": ["Authentication required"]}
        
        user = db.session.get(User, user_id)
        if not user or user.role != 'job_seeker':
            return {"application": None, "errors": ["Only job seekers can apply for jobs"]}
        
        job_id = input["jobId"]
        job = db.session.get(Job, job_id)
        if not job:
            return {"application": None, "errors": ["Job not found"]}
        
        # Check if already applied
        existing_application = Application.query.filter_by(
            job_id=job_id, applicant_id=user_id).first()
        if existing_application:
            return {"application": None, "errors": ["You have already applied to this job"]}
        
        # Handle resume if provided
        resume_path = None
        if "resumePath" in input and input["resumePath"]:
            # In a real implementation, you would handle file upload differently
            # This is just a placeholder for the resolver
            resume_path = input["resumePath"]
        
        # Create application
        application = Application(
            job_id=job_id,
            applicant_id=user_id,
            resume_path=resume_path,
            application_date=datetime.now(timezone.utc),
            status='applied'
        )
        
        db.session.add(application)
        db.session.commit()
        
        return {"application": application, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"application": None, "errors": [str(e)]}

@mutation.field("updateApplicationStatus")
def resolve_update_application_status(_, info, id, status):
    """Resolver for updateApplicationStatus mutation - updates an application's status."""
    try:
        # Check if user is logged in and authorized
        user_id = session.get('user_id')
        if not user_id:
            return {"application": None, "errors": ["Authentication required"]}
        
        application = db.session.get(Application, id)
        if not application:
            return {"application": None, "errors": ["Application not found"]}
        
        job = db.session.get(Job, application.job_id)
        user = db.session.get(User, user_id)
        
        # Only admin or the job poster can update application status
        if not user or (user.role != 'admin' and job.poster_id != user_id):
            return {"application": None, "errors": ["Not authorized to update this application"]}
        
        # Validate status
        valid_statuses = ['applied', 'pending', 'reviewed', 'rejected', 'shortlisted', 'hired']
        if status not in valid_statuses:
            return {"application": None, "errors": [f"Invalid status. Must be one of: {', '.join(valid_statuses)}"]}
        
        application.status = status
        db.session.commit()
        
        return {"application": application, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"application": None, "errors": [str(e)]}

@mutation.field("deleteApplication")
def resolve_delete_application(_, info, id):
    """Resolver for deleteApplication mutation - deletes an application."""
    try:
        # Check if user is logged in and authorized
        user_id = session.get('user_id')
        if not user_id:
            return {"success": False, "errors": ["Authentication required"]}
        
        application = db.session.get(Application, id)
        if not application:
            return {"success": False, "errors": ["Application not found"]}
        
        user = db.session.get(User, user_id)
        # Only admin, the job poster, or the applicant can delete an application
        if not user:
            return {"success": False, "errors": ["User not found"]}
        
        if user.role != 'admin' and application.applicant_id != user_id:
            job = db.session.get(Job, application.job_id)
            if job.poster_id != user_id:
                return {"success": False, "errors": ["Not authorized to delete this application"]}
        
        db.session.delete(application)
        db.session.commit()
        
        return {"success": True, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "errors": [str(e)]}

# Field resolvers
@application_type.field("job")
def resolve_job(application, info):
    """Resolver for job field on Application type."""
    return db.session.get(Job, application.job_id)

@application_type.field("applicant")
def resolve_applicant(application, info):
    """Resolver for applicant field on Application type."""
    return db.session.get(User, application.applicant_id)

@application_type.field("applicationDate")
def resolve_application_date(application, info):
    """Resolver for applicationDate field on Application type."""
    return application.application_date.isoformat()

# Collect all application-related resolvers
application_resolvers = [query, mutation, application_type]