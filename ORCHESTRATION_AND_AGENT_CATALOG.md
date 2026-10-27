# Orchestration Document and Agent Catalog

## 1. Objective

This document defines the operational orchestrator model for the agentic harness and aligns it to the root control file, `LLM_Models.md`.

The harness follows a limited-agent model with a precise control loop:

1. Planner takes the developer prompt and creates the sprint contract and spec
2. Generator implements the approved contract
3. Evaluator reviews output and produces a structured verdict
4. Root orchestrator decides next action
5. Monitor logs the sprint outcome to `.harness/reviews/`

This is the core governance and execution model for the repository.

## 2. Root Orchestration Contract

The root orchestrator is `LLM_Models.md`.

The orchestrator is responsible for:
- reading the active developer prompt
- invoking the Planner as the first stage
- waiting for developer approval on `spec.md`
- running the Generator/Evaluator loop autonomously after `Approved`
- deciding PASS / FAIL / escalate outcomes
- invoking the Monitor after each sprint verdict
- storing evidence under `.harness/reviews/`

The orchestrator is also the governance gatekeeper for all iterations.

## 3. Required Workflow

### Stage 1: Requirements Intake
Developer action:
- invoke Planner with a feature prompt like:
  `@planner Add search feature to the screen`

Planner output:
- `spec.md`
- sprint contract for the scope
- acceptance criteria using GIVEN / WHEN / THEN

### Stage 2: Developer Approval Gate
Developer action:
- review `spec.md`
- type `Approved` if scope and criteria are acceptable

Only after `Approved` does the Generator/Evaluator cycle begin.

### Stage 3: Generator Implementation
Generator responsibilities:
- read the sprint contract
- implement the approved scope
- write implementation and validation artifacts
- produce `generator-summary.md`

### Stage 4: Evaluator Review
Evaluator responsibilities:
- review implementation against contract, standards, and architecture rules
- produce `evaluator-feedback.md`
- output verdict: PASS / Conditional Pass / FAIL

### Stage 5: Orchestrator Decision
Root orchestrator reads `evaluator-feedback.md` and decides:

- PASS -> advance to next sprint
- FAIL -> send targeted feedback back to Generator and retry
- Conditional Pass -> advance only under explicit constraints or rework
- 3 failed iterations -> escalate to developer

### Stage 6: Monitor Archive
Monitor responsibilities:
- write `run-log.md` to `.harness/reviews/`
- record iteration, verdict, escalation state, token estimate, and quality notes
- preserve evidence for future skill refinement

## 4. Handoff File Model

Handoff files live under `.harness/output/` and form the operational boundary between agents.

Required outputs:
- `.harness/output/01-spec.md`
- `.harness/output/02-sprint-contract.md`
- `.harness/output/03-generator-summary.md`
- `.harness/output/04-evaluator-feedback.md`
- `.harness/output/05-run-log.md`

These files are read and written by the agents as part of the cycle. They are the active context exchange between the planner, generator, evaluator, and monitor.

## 5. Agent Catalog

### 5.1 Planner Agent
Purpose:
- transform the feature prompt into a concrete requirement and sprint contract
- create `spec.md` with acceptance criteria

Responsibilities:
- decompose a developer prompt into defined scope
- define business and technical constraints
- produce GIVEN / WHEN / THEN acceptance criteria
- create the sprint contract for implementation
- stop for human approval before implementation begins

### 5.2 Generator Agent
Purpose:
- implement the approved sprint contract
- keep work focused and reviewable

Responsibilities:
- edit code or configuration to satisfy the contract
- produce `generator-summary.md`
- document files changed
- include AC self-check and known gaps
- record assumptions and unresolved risks

### 5.3 Evaluator Agent
Purpose:
- review the implementation against the contract and standards
- provide structured verdict and actionable findings

Responsibilities:
- validate business-rule compliance
- validate architecture rules and guardrails
- check typed error usage and event model integration
- verify required state transitions and invariants
- produce `evaluator-feedback.md` with file-level and line-level findings

### 5.4 Monitor Agent
Purpose:
- archive each sprint result in the governance trail
- identify repeat failure patterns and escalation conditions

Responsibilities:
- read `evaluator-feedback.md`
- compute iteration count and verdict state
- write `run-log.md` to `.harness/reviews/`
- capture token cost estimate and quality trend notes
- flag when the sprint should be retried or escalated

### 5.5 Database Agent
Purpose:
- own schema design and database evolution for future feature work
- keep schema changes explicit, versioned, and reviewable

Responsibilities:
- model new database entities and relationships
- propose indexes, constraints, and lifecycle rules
- prepare migration and rollback plans
- review impact of schema additions or updates on API and business logic
- preserve backward compatibility during iterative product changes

## 6. Limited Agent Architecture

This harness intentionally uses a small set of agents to reduce confusion, drift, and overlapping responsibilities.

Recommended minimal roster:
- Planner
- Generator
- Evaluator
- Monitor

This is the default harness design in this repository and is the operational baseline.

## 7. Decision Policy

The root orchestrator applies the following rules:

### PASS
- advance to the next sprint
- record evidence
- continue until all sprints are complete

### FAIL
- send feedback to the Generator
- keep the sprint in retry loop
- include file and line findings from Evaluator

### Conditional Pass
- only allow advance if the condition is explicitly acceptable
- otherwise send the issue back to Generator

### Escalation
- after 3 unsuccessful iterations on the same sprint, escalate to the human developer
- attach the sprint contract, summary, evaluator feedback, and run logs

## 8. Governance Rule: Developer Is Not in the Loop After Approval

Once the developer reviews `spec.md` and types `Approved`, the harness is expected to operate autonomously.

The developer only performs two actions:
1. invoke the Planner
2. review and approve the spec

From that point onward, all subsequent actions are controlled by the agent loop until:
- all sprints pass, or
- escalation occurs

## 9. Evidence and Audit Trail

The `.harness/reviews/` directory is the primary governance archive.

It stores:
- `run-log.md` for each sprint
- verdict history
- escalation data
- quality trend notes
- repeated failure patterns

This archive is the key input for skill refinement.

## 10. Skill Refinement Inputs

The review archive is used to identify weak areas in skill design, including:
- repeated architecture violations
- repeated AppError misuse
- repeated event-bus bypasses
- status-only testing patterns
- poor requirement decomposition

When the same pattern appears across multiple sprint logs, the harness should update skill prompts, templates, or policy gates.

## 11. Summary

The agentic harness is a small, highly governed loop:

Planner -> Generator -> Evaluator -> Orchestrator -> Monitor

The orchestrator is `LLM_Models.md`, the root control file. The agent catalog and workflow are intentionally limited and explicit so the system remains reviewable, auditable, and operationally safe.
