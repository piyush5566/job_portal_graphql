"""
GraphQL resolvers package.

This package contains resolver functions for the GraphQL schema.
Resolvers are organized by entity type (User, Job, Application).
"""

from .user_resolvers import user_resolvers
from .job_resolvers import job_resolvers
from .application_resolvers import application_resolvers

# Combine all resolvers
resolvers = [
    *user_resolvers,
    *job_resolvers,
    *application_resolvers
]