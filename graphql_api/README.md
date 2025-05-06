# GraphQL API for Job Portal

This directory contains the GraphQL implementation for the Job Portal application using the Ariadne library.

## Overview

The GraphQL API provides a flexible and efficient way to query and mutate data in the Job Portal application. It replaces the REST API with a single endpoint that can handle various operations based on the GraphQL schema.

## Structure

- `schema.py`: Defines the GraphQL schema using SDL (Schema Definition Language)
- `resolvers/`: Contains resolver functions for each type and operation
  - `__init__.py`: Combines all resolvers
  - `user_resolvers.py`: Resolvers for User type and operations
  - `job_resolvers.py`: Resolvers for Job type and operations
  - `application_resolvers.py`: Resolvers for Application type and operations

## GraphQL Schema

The schema defines the following types:

- **User**: Represents application users (job seekers, employers, admins)
- **Job**: Represents job listings posted by employers
- **Application**: Represents job applications submitted by job seekers

And the following operations:

### Queries

- `user(id: ID!)`: Get a user by ID
- `users`: Get all users
- `job(id: ID!)`: Get a job by ID
- `jobs(location: String, category: String, company: String)`: Get jobs with optional filters
- `application(id: ID!)`: Get an application by ID
- `applications`: Get all applications (admin only)
- `myApplications`: Get applications for the current user
- `jobApplications(jobId: ID!)`: Get applications for a specific job

### Mutations

- `createUser(input: UserInput!)`: Create a new user
- `updateUser(id: ID!, input: UserInput!)`: Update an existing user
- `deleteUser(id: ID!)`: Delete a user
- `createJob(input: JobInput!)`: Create a new job
- `updateJob(id: ID!, input: JobInput!)`: Update an existing job
- `deleteJob(id: ID!)`: Delete a job
- `createApplication(input: ApplicationInput!)`: Create a new application
- `updateApplicationStatus(id: ID!, status: String!)`: Update an application's status
- `deleteApplication(id: ID!)`: Delete an application

## Usage

### Accessing the GraphQL API

The GraphQL API is available at `/graphql`. You can use the GraphiQL explorer interface by visiting this URL in your browser.

### Example Queries

#### Get all jobs

```graphql
query {
  jobs {
    id
    title
    company
    location
    category
    salary
    postedDate
    applicationCount
  }
}
```

#### Get a specific job with its applications

```graphql
query {
  job(id: "1") {
    title
    description
    company
    location
    applications {
      id
      applicant {
        username
        email
      }
      status
      applicationDate
    }
  }
}
```

#### Create a new job

```graphql
mutation {
  createJob(input: {
    title: "Software Engineer"
    description: "Develop web applications"
    salary: "$100,000 - $120,000"
    location: "San Francisco, CA"
    category: "Technology"
    company: "Tech Corp"
  }) {
    job {
      id
      title
    }
    errors
  }
}
```

## Testing

You can test the GraphQL implementation using the `test_graphql.py` script:

```bash
python test_graphql.py
```

This script sends a simple query to the GraphQL API and displays the response.

## Implementation Details

The GraphQL API is implemented using the Ariadne library, which is a schema-first GraphQL library for Python. The implementation follows these key principles:

1. **Schema-first approach**: The schema is defined using SDL in `schema.py`
2. **Resolver functions**: Each field in the schema has a corresponding resolver function
3. **Authentication and authorization**: Mutations check user authentication and authorization
4. **Error handling**: All mutations return errors in a consistent format

## Integration with Flask

The GraphQL API is integrated with Flask using a blueprint (`blueprints/graphql`). The blueprint registers the GraphQL endpoint and sets up the GraphiQL explorer interface.