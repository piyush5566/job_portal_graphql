"""
GraphQL schema definition for the Job Portal application.

This module defines the GraphQL schema types that correspond to the database models:
- User: Represents application users (job seekers, employers, admins)
- Job: Represents job listings posted by employers
- Application: Represents job applications submitted by job seekers

The schema is defined using SDL (Schema Definition Language) and will be used by Ariadne.
"""

# Define the GraphQL schema using SDL (Schema Definition Language)
type_defs = """
    type Query {
        # User queries
        user(id: ID!): User
        users: [User!]!
        
        # Job queries
        job(id: ID!): Job
        jobs(
            location: String
            category: String
            company: String
        ): [Job!]!
        
        # Application queries
        application(id: ID!): Application
        applications: [Application!]!
        myApplications: [Application!]!
        jobApplications(jobId: ID!): [Application!]!
    }
    
    type Mutation {
        # User mutations
        createUser(input: UserInput!): UserPayload!
        updateUser(id: ID!, input: UserInput!): UserPayload!
        deleteUser(id: ID!): DeletePayload!
        
        # Job mutations
        createJob(input: JobInput!): JobPayload!
        updateJob(id: ID!, input: JobInput!): JobPayload!
        deleteJob(id: ID!): DeletePayload!
        
        # Application mutations
        createApplication(input: ApplicationInput!): ApplicationPayload!
        updateApplicationStatus(id: ID!, status: String!): ApplicationPayload!
        deleteApplication(id: ID!): DeletePayload!
    }
    
    # User type and related inputs/payloads
    type User {
        id: ID!
        username: String!
        email: String!
        role: String!
        profilePicture: String
        jobsPosted: [Job!]
        applications: [Application!]
    }
    
    input UserInput {
        username: String!
        email: String!
        password: String!
        role: String!
        profilePicture: String
    }
    
    type UserPayload {
        user: User
        errors: [String!]
    }
    
    # Job type and related inputs/payloads
    type Job {
        id: ID!
        title: String!
        description: String!
        salary: String
        location: String!
        category: String!
        company: String!
        companyLogo: String
        postedDate: String!
        poster: User!
        applications: [Application!]
        applicationCount: Int!
    }
    
    input JobInput {
        title: String!
        description: String!
        salary: String
        location: String!
        category: String!
        company: String!
        companyLogo: String
    }
    
    type JobPayload {
        job: Job
        errors: [String!]
    }
    
    # Application type and related inputs/payloads
    type Application {
        id: ID!
        job: Job!
        applicant: User!
        applicationDate: String!
        status: String!
        resumePath: String
    }
    
    input ApplicationInput {
        jobId: ID!
        resumePath: String
    }
    
    type ApplicationPayload {
        application: Application
        errors: [String!]
    }
    
    # Common payload for delete operations
    type DeletePayload {
        success: Boolean!
        errors: [String!]
    }
"""