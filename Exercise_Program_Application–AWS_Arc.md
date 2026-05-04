# Exercise Program Application – AWS Architecture Proposal

## Objective

Design and implement a scalable, cost-effective AWS infrastructure for an Exercise Program Application with automated CI/CD and Infrastructure as Code.

The system is a monorepo containing:

1. **Frontend**

   * React + Vite SPA

2. **Backend API**

   * FastAPI
   * Handles authentication, persistence, orchestration, and business workflows

3. **Program Builder**

   * Python-based program generation engine
   * Invoked internally by Backend only
   * Ultra-fast execution (milliseconds)
   * Low request frequency
   * No need for always-on infrastructure

---

# Architecture Principles

* Low cost
* Low operational overhead
* Production-ready
* Scalable
* Clear separation of concerns
* Infrastructure as Code
* CI/CD automation
* Framework-agnostic business logic

---

# Final Architecture

```text
Frontend (React/Vite)
    → Amazon S3
    → Amazon CloudFront

Backend API (FastAPI)
    → Amazon ECS Fargate
    → Application Load Balancer

Program Builder
    → AWS Lambda
    → Native Lambda Handler
    → Shared Python Core Package

Infrastructure
    → Terraform

CI/CD
    → GitHub Actions
```

---

# System Flow

```text
User
   ↓
CloudFront
   ↓
Frontend (React/Vite)
   ↓
Backend API (FastAPI on ECS)
   ↓
Invoke AWS Lambda
   ↓
Program Builder Core
   ↓
Return Generated Program
```

---

# Component Design

---

## 1. Frontend

### Technology

* React
* Vite

### Deployment

Deploy as static site.

### AWS Services

* S3
* CloudFront
* Route53
* ACM

### Requirements

* SPA routing support
* HTTPS
* CloudFront caching
* CloudFront invalidation after deploy

### Deployment Flow

1. Build Vite app
2. Upload artifacts to S3
3. Invalidate CloudFront cache

---

## 2. Backend API

### Technology

* FastAPI
* Docker

### Deployment

Containerized service running on ECS Fargate.

### AWS Services

* ECS Cluster
* ECS Service
* Fargate
* ECR
* Application Load Balancer
* CloudWatch
* IAM

### Requirements

* Public HTTPS endpoint
* Always available
* Rolling deployments
* Health checks
* Autoscaling

### Initial Sizing

* CPU: 0.25–0.5 vCPU
* Memory: 0.5–1 GB
* Min tasks: 1

### Networking

* ALB public
* ECS tasks behind ALB

---

## 3. Program Builder

## Architecture Pattern

Program Builder must separate:

1. Business logic
2. Runtime adapters

Business logic must not depend on FastAPI or Lambda.

---

## Program Builder Structure

```text
program-builder/
├── core/
│   ├── generator.py
│   ├── progression.py
│   ├── templates.py
│   ├── validators.py
│   └── models.py
│
├── lambda/
│   └── handler.py
│
├── api/
│   ├── main.py
│   └── routes.py
│
└── requirements.txt
```

---

## Core Package

Purpose:

* Contains all program generation logic.

Must be pure Python.

No dependency on:

* FastAPI
* AWS
* Lambda

Responsibilities:

* program generation
* progression logic
* template selection
* validation rules

Example:

```python
def generate_program(request):
    return result
```

---

## Lambda Adapter

Purpose:

* Production execution path

File:

```text
lambda/handler.py
```

Example:

```python
from core.generator import generate_program

def handler(event, context):
    return generate_program(event)
```

Requirements:

* Native Lambda handler
* No Mangum
* No FastAPI runtime in production path

Benefits:

* Lower cold starts
* Smaller package
* Lower complexity

---

## Optional FastAPI Adapter

Purpose:

* Local development
* Testing
* Future standalone service if needed

File:

```text
api/main.py
```

Example:

```python
from fastapi import FastAPI
from core.generator import generate_program

app = FastAPI()

@app.post("/generate")
def generate(request: dict):
    return generate_program(request)
```

This adapter is optional and not part of production runtime.

---

## Lambda Invocation

Backend invokes Lambda directly via AWS SDK.

Do NOT expose Program Builder publicly.

Flow:

```text
Backend → Lambda Invoke → Program Builder
```

Benefits:

* secure
* low latency
* internal only

IAM:
Backend execution role must include:

```json
lambda:InvokeFunction
```

---

# Monorepo Structure

```text
repo/
├── frontend/
│
├── backend/
│   ├── app/
│   ├── Dockerfile
│
├── program-builder/
│   ├── core/
│   ├── lambda/
│   ├── api/
│
├── shared/
│   └── models/
│
├── infra/
│   └── terraform/
│
└── .github/
    └── workflows/
```

---

# Shared Contracts

Create shared request/response schemas.

Folder:

```text
shared/models/
```

Examples:

* program_request.py
* program_response.py

Use:

* Pydantic

Purpose:

* consistent schemas between backend and program builder

---

# CI/CD

## Tool

GitHub Actions

---

## Workflow 1 – Frontend

Trigger:

* frontend/** changes

Steps:

1. Install dependencies
2. Build frontend
3. Upload to S3
4. Invalidate CloudFront

---

## Workflow 2 – Backend

Trigger:

* backend/** changes

Steps:

1. Build Docker image
2. Push to ECR
3. Deploy ECS service

---

## Workflow 3 – Program Builder

Trigger:

* program-builder/** changes

Steps:

1. Install dependencies
2. Package Lambda
3. Deploy Lambda

---

# Infrastructure as Code

## Tool

Terraform

Folder:

```text
infra/terraform/
```

Modules:

```text
modules/
├── frontend
├── backend_ecs
├── lambda_program_builder
├── networking
├── iam
```

---

# AWS Resources

---

## Frontend

* S3 bucket
* CloudFront
* ACM certificate
* Route53

---

## Backend

* ECR
* ECS cluster
* ECS service
* Task definition
* ALB
* Security groups
* IAM roles

---

## Program Builder

* Lambda
* CloudWatch logs
* IAM execution role

---

## Networking

* VPC
* Public subnets
* Private subnets
* Internet Gateway

Avoid NAT Gateway initially unless required.

---

# Observability

Use:

* CloudWatch Logs
* CloudWatch Metrics
* CloudWatch Alarms

Monitor:

* ECS CPU
* ECS memory
* ECS failures
* Lambda errors
* Lambda duration
* ALB 5xx

Optional:

* Sentry

---

# Deployment Order

1. Provision Terraform
2. Deploy frontend
3. Deploy backend ECS
4. Deploy Program Builder Lambda
5. Configure backend Lambda invocation
6. End-to-end validation

---

# Success Criteria

* Frontend accessible via CloudFront
* Backend accessible via HTTPS
* Backend successfully invokes Lambda
* Program Builder returns generated program
* CI/CD fully automated
* Terraform fully reproducible

---

# Key Architectural Decisions

1. Frontend is static and CDN-served.
2. Backend is always-on and containerized.
3. Program Builder is event-driven and serverless.
4. Program Builder business logic is framework-agnostic.
5. FastAPI in Program Builder is optional adapter only.
6. Production Program Builder path is native Lambda.

This architecture optimizes:

* cost
* scalability
* maintainability
* deployment speed
* future flexibility

```
```
