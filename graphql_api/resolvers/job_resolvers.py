"""
Job-related GraphQL resolvers.

This module contains resolver functions for Job-related GraphQL operations:
- Queries: job, jobs
- Mutations: createJob, updateJob, deleteJob
- Field resolvers for the Job type
"""

from ariadne import QueryType, MutationType, ObjectType
from flask import session
from models import Job, User, db
from datetime import datetime, timezone

# Initialize types
query = QueryType()
mutation = MutationType()
job_type = ObjectType("Job")

# Query resolvers
@query.field("job")
def resolve_job(_, info, id):
    """Resolver for job query - fetches a job by ID."""
    return db.session.get(Job, id)

@query.field("jobs")
def resolve_jobs(_, info, location=None, category=None, company=None):
    """Resolver for jobs query - fetches jobs with optional filters."""
    query = Job.query
    
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    if category:
        query = query.filter(Job.category.ilike(f'%{category}%'))
    if company:
        query = query.filter(Job.company.ilike(f'%{company}%'))
        
    return query.all()

# Mutation resolvers
@mutation.field("createJob")
def resolve_create_job(_, info, input):
    """Resolver for createJob mutation - creates a new job."""
    try:
        # Check if user is logged in and is an employer
        user_id = session.get('user_id')
        if not user_id:
            return {"job": None, "errors": ["Authentication required"]}
        
        user = db.session.get(User, user_id)
        if not user or user.role not in ['employer', 'admin']:
            return {"job": None, "errors": ["Only employers can post jobs"]}
        
        # Create new job
        job = Job(
            title=input["title"],
            description=input["description"],
            salary=input.get("salary"),
            location=input["location"],
            category=input["category"],
            company=input["company"],
            company_logo=input.get("companyLogo", "img/company_logos/default.png"),
            posted_date=datetime.now(timezone.utc),
            poster_id=user_id
        )
        
        db.session.add(job)
        db.session.commit()
        
        return {"job": job, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"job": None, "errors": [str(e)]}

@mutation.field("updateJob")
def resolve_update_job(_, info, id, input):
    """Resolver for updateJob mutation - updates an existing job."""
    try:
        # Check if user is logged in and is authorized
        user_id = session.get('user_id')
        if not user_id:
            return {"job": None, "errors": ["Authentication required"]}
        
        job = db.session.get(Job, id)
        if not job:
            return {"job": None, "errors": ["Job not found"]}
        
        user = db.session.get(User, user_id)
        if not user or (user.role != 'admin' and job.poster_id != user_id):
            return {"job": None, "errors": ["Not authorized to update this job"]}
        
        # Update fields
        if "title" in input:
            job.title = input["title"]
        if "description" in input:
            job.description = input["description"]
        if "salary" in input:
            job.salary = input["salary"]
        if "location" in input:
            job.location = input["location"]
        if "category" in input:
            job.category = input["category"]
        if "company" in input:
            job.company = input["company"]
        if "companyLogo" in input:
            job.company_logo = input["companyLogo"]
        
        db.session.commit()
        return {"job": job, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"job": None, "errors": [str(e)]}

@mutation.field("deleteJob")
def resolve_delete_job(_, info, id):
    """Resolver for deleteJob mutation - deletes a job."""
    try:
        # Check if user is logged in and is authorized
        user_id = session.get('user_id')
        if not user_id:
            return {"success": False, "errors": ["Authentication required"]}
        
        job = db.session.get(Job, id)
        if not job:
            return {"success": False, "errors": ["Job not found"]}
        
        user = db.session.get(User, user_id)
        if not user or (user.role != 'admin' and job.poster_id != user_id):
            return {"success": False, "errors": ["Not authorized to delete this job"]}
        
        db.session.delete(job)
        db.session.commit()
        return {"success": True, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "errors": [str(e)]}

# Field resolvers
@job_type.field("poster")
def resolve_poster(job, info):
    """Resolver for poster field on Job type."""
    return db.session.get(User, job.poster_id)

@job_type.field("applications")
def resolve_applications(job, info):
    """Resolver for applications field on Job type."""
    return job.applications

@job_type.field("applicationCount")
def resolve_application_count(job, info):
    """Resolver for applicationCount field on Job type."""
    return len(job.applications)

@job_type.field("postedDate")
def resolve_posted_date(job, info):
    """Resolver for postedDate field on Job type."""
    return job.posted_date.isoformat()

# Collect all job-related resolvers
job_resolvers = [query, mutation, job_type]