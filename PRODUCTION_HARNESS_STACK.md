# Production Harness Stack Recommendation

## 1. Objective

This document defines the recommended production stack for the agentic harness described in the architecture and governance documents. The goal is to move from a prototype or repo-local workflow into a scalable, secure, observable, and governable production system.

## 2. Core Design Principles

- explicit agent roles and bounded responsibilities
- policy-first execution model
- observable workflows with governance evidence
- model abstraction and cost awareness
- secure tool execution and approval gates
- reliable deployment and rollback readiness

## 3. Recommended Stack

### 3.1 Application Runtime
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy or SQLModel
- Redis
- PostgreSQL

### 3.2 Frontend
- React
- Vite
- TypeScript
- Tailwind CSS or a design system layer
- React Query / TanStack Query

### 3.3 Workflow / Orchestration
- Celery or RQ for task queues
- Redis as broker and cache
- workflow orchestration layer for task graph execution
- durable job records in PostgreSQL

### 3.4 Model Access Layer
- OpenAI-compatible APIs
- Anthropic API
- Google Gemini API
- provider abstraction layer
- structured model router with cost and latency logic

### 3.5 Governance & Policy Layer
- policy engine or rules registry
- architecture boundary validator
- semantic or AST policy checks
- review and approval workflow
- audit evidence store

### 3.6 Storage and Memory
- PostgreSQL for jobs, workflows, sessions, and audit data
- Redis for queueing and ephemeral state
- vector database for long-term memory (optional but recommended)
- object storage for artifacts and generated outputs

### 3.7 Observability
- OpenTelemetry
- Prometheus
- Grafana
- structured logging
- distributed tracing
- alerting and SLO monitoring

### 3.8 Security and Secrets
- OIDC / SSO
- RBAC / IAM
- secret manager (HashiCorp Vault, AWS Secrets Manager, or equivalent)
- rate limiting and request throttling
- sandboxing for risky tool execution

### 3.9 Deployment
- Docker
- Kubernetes or OpenShift
- GitHub Actions for CI/CD
- Helm or Kustomize for manifests
- automatic rollout with readiness probes and rollback

## 4. Suggested Production Architecture

### 4.1 Frontend
A web-based harness dashboard with:
- workflow submission
- live status of phases
- agent activity log
- approval and escalation queue
- metrics and governance view

### 4.2 API Layer
A secure FastAPI API that provides:
- session and workflow creation
- agent orchestration endpoints
- tool execution orchestration
- audit and evidence retrieval
- rate-limit enforcement

### 4.3 Worker Layer
The worker system executes tasks asynchronously with a queue such as Celery. Responsibilities:
- run sprint jobs
- trigger agent execution
- manage retries and timeouts
- store result artifacts
- record logs and metrics

### 4.4 Governance Layer
This layer is separate from execution and is responsible for:
- policy enforcement
- approval gates
- architecture validation
- audit evidence capture
- escalation logic from evaluator verdicts

### 4.5 Data Persistence
- PostgreSQL holds workflow state, evaluations, sessions, approvals, and run logs
- Redis holds queue state and short-lived caches
- object storage holds files, generated outputs, and evidence artifacts

## 5. Why This Stack

This stack is chosen because it provides:
- easy API development with FastAPI
- robust async job processing with Celery + Redis
- durable structured state with PostgreSQL
- model flexibility and provider abstraction
- good observability and governance support
- stable deployment pattern in Kubernetes/OpenShift

## 6. Production-Ready Recommendations

- separate execution environment from governance environment
- enforce RBAC and per-agent tool permissions
- run risky tools in sandboxed containers
- maintain immutable logs and evidence archives
- version prompts, workflows, and policies
- impose rate limits and quota controls
- require human approval for destructive actions

## 7. Example High-Level Stack Summary

- Backend: FastAPI + Python
- Queue: Celery + Redis
- Database: PostgreSQL
- Memory: Redis + optional vector DB
- Frontend: React + Vite + TypeScript
- Models: OpenAI / Anthropic / Gemini abstraction layer
- Observability: OpenTelemetry + Prometheus + Grafana
- Deployment: Docker + OpenShift/Kubernetes + GitHub Actions

## 8. Final Recommendation

For a production quality harness, the best choice is:

- FastAPI for the control plane API
- Celery + Redis for asynchronous orchestration
- PostgreSQL for durable workflows, approvals, and evidence
- React + Vite + TypeScript for the monitoring dashboard
- OpenShift/Kubernetes for deployment
- OpenTelemetry + Grafana for observability
- provider abstraction for AI models with cost tracking

This provides a strong production base while keeping the system simple, governable, and operable.
