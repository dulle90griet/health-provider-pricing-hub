# Health Provider Pricing Hub

A serverless pricing and tendering data platform for a national private healthcare provider: a central PostgreSQL database, an HTTP API on AWS Lambda, and a Budibase GUI, all managed in Terraform.

> [!NOTE]
> **Status: pre-go-live.** The platform has been deployed and verified, but it is held offline while the clients complete and rationalize their existing data ready for ingestion. The repository contains no client data.

## 🌐 Overview

The client's pricing and tendering ran on spreadsheets shared by email, with no central versioning and with key information passed on verbally and never recorded. The data was inconsistent, incoherent and incomplete.

Through analysis of that data and several rounds of interviews with the client's CEO and accounting staff, I established the relationships, assumptions and usage habits behind their pricing and tendering, worked out the coherent structure beneath the mess, and designed a third normal form (3NF) schema for a central OLTP database that enforces coherence and completeness.

Stack:
- **PostgreSQL on Amazon RDS** as the central database
- **AWS Lambda (Python)** behind **Amazon API Gateway** (HTTP API), using the **Powertools for AWS Lambda** `APIGatewayHttpResolver` for request handling, with **Pydantic** request models
- **Budibase**, running as a single Docker image on **ECS Fargate** with **EFS** storage and **ALB load balancing**, as the GUI
- **Amazon Cognito** for OAuth 2.0 authentication
- **Terraform** for all infrastructure, across four environments
- **GitHub Actions** for CI/CD, with tag-based promotion to production

## 🛣️ Roadmap

Remaining before go-live:
- A one-off script to load the client's cleaned data
- Tender screen: totals for calculated columns, with a new API route

Planned after go-live, to extend the platform beyond its MVP:
- Service Overview screen: manage a Service and all its Direct and Labour Costs in one place, with two new API routes
- Personnel and salary record management, feeding into pricing calculations
- Automated database change audit table
- Data export as plain CSV
- Tender export as a formatted PDF

## 🚧 Documentation in progress

Architecture, data model, CI/CD and setup documentation are coming soon.