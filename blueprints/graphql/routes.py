"""
Routes for the GraphQL blueprint.

This module defines the GraphQL API endpoint and sets up the Ariadne GraphQL server.
"""

from flask import request, jsonify, current_app
from ariadne import make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from extensions import csrf

from . import graphql_bp
from graphql_api.schema import type_defs
from graphql_api.resolvers import resolvers

# Create executable schema
schema = make_executable_schema(type_defs, *resolvers)

# GraphiQL explorer instance
explorer_html = ExplorerGraphiQL(title="Job Portal GraphQL API").html(None)

@graphql_bp.route("/", methods=["GET"])
@graphql_bp.route("", methods=["GET"])  # Handle both with and without trailing slash
def graphql_explorer():
    """
    Serve the GraphiQL explorer interface.

    This provides an interactive UI for exploring and testing the GraphQL API.
    """
    return explorer_html

@graphql_bp.route("/", methods=["POST"])
@graphql_bp.route("", methods=["POST"])  # Handle both with and without trailing slash
@csrf.exempt
def graphql_server():
    """
    Handle GraphQL API requests.

    This endpoint processes GraphQL queries and mutations and returns the results.
    CSRF protection is disabled for GraphQL queries to allow API clients to work without CSRF tokens.
    For production use, consider implementing proper authentication mechanisms like JWT.
    """
    # Get request data
    data = request.get_json()

    # Execute the query
    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        debug=current_app.debug
    )

    # Return the result
    status_code = 200 if success else 400
    return jsonify(result), status_code
