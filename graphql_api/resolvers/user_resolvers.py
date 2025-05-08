"""
User-related GraphQL resolvers.

This module contains resolver functions for User-related GraphQL operations:
- Queries: user, users
- Mutations: createUser, updateUser, deleteUser
- Field resolvers for the User type
"""

from ariadne import QueryType, MutationType, ObjectType
from models import User, db

# Initialize types
query = QueryType()
mutation = MutationType()
user_type = ObjectType("User")

# Query resolvers
@query.field("user")
def resolve_user(_, info, id):
    """Resolver for user query - fetches a user by ID."""
    return db.session.get(User, id)

@query.field("users")
def resolve_users(_, info):
    """Resolver for users query - fetches all users."""
    return User.query.all()

# Mutation resolvers
@mutation.field("createUser")
def resolve_create_user(_, info, input):
    """Resolver for createUser mutation - creates a new user."""
    try:
        # Check if email already exists
        existing_user = User.query.filter_by(email=input["email"]).first()
        if existing_user:
            return {"user": None, "errors": ["Email already in use"]}
        
        # Create new user
        user = User(
            username=input["username"],
            email=input["email"],
            role=input["role"],
            profile_picture=input.get("profilePicture", "img/profiles/default.jpg")
        )
        user.set_password(input["password"])
        
        db.session.add(user)
        db.session.commit()
        
        return {"user": user, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"user": None, "errors": [str(e)]}

@mutation.field("updateUser")
def resolve_update_user(_, info, id, input):
    """Resolver for updateUser mutation - updates an existing user."""
    try:
        user = db.session.get(User, id)
        if not user:
            return {"user": None, "errors": ["User not found"]}
        
        # Update fields
        if "username" in input:
            user.username = input["username"]
        if "email" in input:
            # Check if email is already in use by another user
            existing_user = User.query.filter_by(email=input["email"]).first()
            if existing_user and existing_user.id != int(id):
                return {"user": None, "errors": ["Email already in use"]}
            user.email = input["email"]
        if "password" in input:
            user.set_password(input["password"])
        if "role" in input:
            user.role = input["role"]
        if "profilePicture" in input:
            user.profile_picture = input["profilePicture"]
        
        db.session.commit()
        return {"user": user, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"user": None, "errors": [str(e)]}

@mutation.field("deleteUser")
def resolve_delete_user(_, info, id):
    """Resolver for deleteUser mutation - deletes a user."""
    try:
        user = db.session.get(User, id)
        if not user:
            return {"success": False, "errors": ["User not found"]}
        
        db.session.delete(user)
        db.session.commit()
        return {"success": True, "errors": []}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "errors": [str(e)]}

# Field resolvers
@user_type.field("jobsPosted")
def resolve_jobs_posted(user, info):
    """Resolver for jobsPosted field on User type."""
    return user.jobs_posted

@user_type.field("applications")
def resolve_applications(user, info):
    """Resolver for applications field on User type."""
    return user.applications

# Collect all user-related resolvers
user_resolvers = [query, mutation, user_type]