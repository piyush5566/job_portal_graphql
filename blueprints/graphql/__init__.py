"""
GraphQL blueprint for the Job Portal application.

This blueprint provides the GraphQL API endpoint for the application.
"""

from flask import Blueprint

graphql_bp = Blueprint('graphql_api', __name__)

from . import routes