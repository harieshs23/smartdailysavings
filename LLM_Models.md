# LLM_Models.md

## 1. Purpose

`LLM_Models.md` is the root orchestrator for the agentic harness. It does not implement business logic itself. Instead, it governs the full sprint lifecycle, reads the Evaluator’s verdict, decides the next action, and archives the outcome in a governance trail.

This document defines the orchestration contract for a limited-agent harness:

- Planner: decomposes work into sprint contracts and acceptance criteria
- Generator: implements the sprint contract
- Evaluator: reviews the implementation against the contract and standards
- Monitor: records run state, quality trend, escalation, and token cost after each sprint

The orchestrator is the control plane for the harness and is the primary source of governance decisions.

## 1.1 Launch Model

The Planner is invoked by a single developer prompt such as:

`@planner Add search feature to the screen`

The developer’s only active steps are:

1. invoke the Planner with the feature prompt
2. review `spec.md` and type `Approved` when the scope and criteria are correct

After approval, the harness drives the Generator/Evaluator loop autonomously until all planned sprints pass or escalation occurs.

The Planner writes the sprint contract and handoff context. The Generator reads the contract and produces implementation plus `generator-summary.md`. The Evaluator reads the output and writes `evaluator-feedback.md`. The Root Orchestrator reads the verdict and decides the next action.

All handoff state between agents is written under `.harness/output/` so that each step has a structured, reviewable context boundary.

## 1.2 Agent File Resolution

When the repository is opened by an LLM or Copilot session, the root orchestrator reads this file first and then resolves the active agent definitions from the `.harness/agents/` directory.

Required agent files:
- `.harness/agents/planner.agent.md`
- `.harness/agents/generator.agent.md`
- `.harness/agents/evaluator.agent.md`
- `.harness/agents/monitor.agent.md`

The harness should route work as follows:
- Planner handles requirement decomposition and sprint contracts
- Generator handles implementation work for the active sprint
- Evaluator handles verdict generation and review feedback
- Monitor handles post-sprint logging and governance archive updates

The orchestrator reads and writes handoff files in `.harness/output/` using the following flow:

- `.harness/output/01-spec.md`
- `.harness/output/02-sprint-contract.md`
- `.harness/output/03-generator-summary.md`
- `.harness/output/04-evaluator-feedback.md`
- `.harness/output/05-run-log.md`

These files are the operational handoff boundary between agents.

## 2. Core Principle

The system follows a closed-loop improvement model:

- Plan
- Generate
- Evaluate
- Decide
- Archive
- Refine skills

The orchestrator reads the Evaluator’s structured verdict and decides one of three actions:

1. PASS -> advance to next sprint
2. FAIL -> send structured feedback back to the Generator
3. Escalate -> after three unsuccessful iterations, escalate to a human developer

## 3. Required Files and Responsibilities

### 3.1 `spec.md`
Created by the Planner.

Purpose:
- captures the target requirement
- clarifies scope and constraints
- defines acceptance criteria
- translates the objective into sprint-ready contracts

### 3.2 Sprint Contract Files
Each sprint has a contract that defines:
- objective
- scope
- required files
- GIVEN / WHEN / THEN scenarios
- acceptance criteria
- validation requirements
- known risks

### 3.3 `generator-summary.md`
Created by the Generator.

Contains:
- files changed
- summary of implementation
- AC self-check table
- known gaps
- assumptions
- open risks

### 3.4 `evaluator-feedback.md`
Created by the Evaluator.

Contains:
- verdict: PASS / Conditional Pass / FAIL
- file-level findings
- line-level findings
- rule compliance status
- business-rule verification status
- gaps against contract
- architecture or governance violations

### 3.5 `run-log.md`
Created by the Monitor after each sprint verdict.

Contains:
- sprint id
- iteration count
- verdict
- escalation flag
- estimated token cost
- quality trend notes
- key issues and refinements
- final disposition (advance, retry, escalate)

Stored under:
- `.harness/reviews/`

This directory is the governance audit trail and is the primary evidence base for pattern and skill refinement.

## 4. Root Orchestrator Responsibilities

The root orchestrator (`LLM_Models.md`) owns the control loop and is responsible for the following:

### 4.1 Sprint Intake
- reads the sprint contract and required acceptance criteria
- waits for developer approval on `spec.md`
- confirms the sprint context and constraints
- ensures the task is scoped correctly before generation begins

### 4.2 Generator Handoff
- waits for the developer to type `Approved`
- passes the sprint contract to the Generator
- tracks which files are expected to change
- stores a snapshot of the target state

### 4.3 Verdict Handling
- reads `evaluator-feedback.md`
- classifies outcome as:
  - PASS
  - Conditional Pass
  - FAIL
- decides the next action based on policy

### 4.4 Decision Policy

#### PASS
If verdict is PASS:
- advance to the next sprint
- clear retry count for the sprint
- archive evidence and move to next contract

#### FAIL
If verdict is FAIL:
- send the failure report back to Generator
- include file-level and line-level findings
- request revision within the same sprint scope

#### Conditional Pass
If verdict is Conditional Pass:
- allow a constrained advance only if the conditions are accepted by the orchestrator
- otherwise send targeted feedback to the Generator

#### Escalation
If the same sprint fails after maximum of three iterations:
- escalate to the human developer
- attach all evidence, including:
  - spec contract
  - generator summary
  - evaluator verdict
  - prior run logs
  - quality trend analysis

### 4.5 Monitoring Trigger
After each sprint, the Monitor runs automatically and writes a structured `.harness/reviews/run-log.md` entry.

The root orchestrator should treat this archive as the governance evidence record and as the core input for future skill refinement.

### 4.6 Developer Approval Gate
The developer is intentionally excluded from routine execution once the feature prompt is accepted.

Required developer interaction:
1. invoke the Planner with a feature prompt
2. review the generated `spec.md`
3. type `Approved` to authorize the autonomous Generator/Evaluator loop

After `Approved`, all subsequent workflow decisions are made by the harness until the sprint set is complete or escalation is triggered.

## 5. Decision Loop

```text
Start
  -> Planner creates spec.md and sprint contract
  -> Generator implements contract
  -> Generator writes generator-summary.md
  -> Evaluator reviews output and writes evaluator-feedback.md
  -> Orchestrator reads verdict
      if PASS -> advance to next sprint
      if FAIL -> send feedback to Generator
      if Conditional Pass -> decide with constraints or rework
      if max iterations reached -> escalate to developer
  -> Monitor archives run-log.md under .harness/reviews
  -> Skill refinement loop reads historical run logs and evaluator feedback
End
```

## 6. Iteration and Escalation Policy

### Maximum retry threshold
The harness should allow a maximum of three iterations per sprint contract.

Iteration rules:
- Iteration 1: initial implementation
- Iteration 2: rework based on evaluator feedback
- Iteration 3: final rework attempt
- After 3 unsuccessful iterations: escalate to human developer

### Escalation trigger
Escalate when one or more of the following is true:
- same contract fails repeatedly
- architecture violations persist after rework
- business-rule compliance remains unproven
- evaluator marks core requirements as not satisfied
- the issue is systemic rather than local

## 7. Monitor Responsibilities

The Monitor is a governance function, not an implementation worker.

It is responsible for:
- reading `evaluator-feedback.md`
- collecting sprint metadata
- creating `run-log.md`
- storing the record under `.harness/reviews/`
- identifying repeated failure patterns
- flagging skills that require refinement

### 7.1 `run-log.md` structure
Each run log should contain:

- sprint id
- iteration count
- requirement summary
- verdict
- status: pass / retry / escalate
- evaluator findings summary
- escalation flag
- estimated token cost
- quality trend notes
- recommendations for skill refinement

### 7.2 Governance archive path
```text
.harness/
  reviews/
    sprint-001-run-log.md
    sprint-002-run-log.md
    ...
```

This archive acts as the official governance audit trail and is the main input for identifying weak skill files, repeated failure patterns, and policy gaps.

## 8. Skill Refinement Use of Historical Review Data

The monitor and orchestrator should use the archive to detect which skills need improvement.

Refinement triggers include:
- repeated FAIL across multiple sprints for the same issue class
- repeated architecture boundary violations
- repeated AppError misuse
- repeated failure in business-rule validation
- repeated event-bus integration gaps
- repeated poor test quality tied to HTTP-only assertions

Examples of skill refinement signals:
- Generator skill weak in event-driven contract implementation
- Evaluator skill weak in validating business invariants
- Planner skill weak in defining GIVEN/WHEN/THEN contracts
- Governance skill weak in detecting architecture boundary policy violations

The system should convert these patterns into action items such as:
- update prompt templates
- tighten evaluation criteria
- add new policy checks
- improve examples in skill documentation
- add guardrails to the Generator contract

## 9. Agent Allocation for the Minimal Harness

### Planner
- owns requirements decomposition
- produces spec.md and sprint contracts

### Generator
- implements sprint scope
- produces generator-summary.md

### Evaluator
- reviews output against architecture, standards, and acceptance criteria
- produces evaluator-feedback.md

### Monitor / Orchestrator control function
- reads verdicts and decides progression or escalation
- writes run-log.md to `.harness/reviews`
- tracks token cost and quality trend

This is the recommended limited-runtime model: four controlled roles with explicit execution boundaries.

## 10. Standard Decision Table

| Evaluator verdict | Orchestrator action | Monitor action | Outcome |
| --- | --- | --- | --- |
| PASS | advance to next sprint | write run-log.md | continue workflow |
| Conditional Pass | allow only with explicit constraints or rework | write run-log.md | proceed with caution |
| FAIL | send targeted feedback to Generator and retry | write run-log.md | iterative correction |
| 3rd FAIL | escalate to human developer | archive full evidence | stop and escalate |

## 11. Governance and Audit Trail Rule

The `.harness/reviews` archive is not optional. It is the primary governance artifact.

It should be treated as:
- audit evidence
- skill refinement data source
- quality trend ledger
- developer escalation pack
- contract validation archive

## 12. Summary

`LLM_Models.md` is the root orchestrator and governance control plane for the harness. It is the point where the system reads evaluator judgment, decides sprint progression, triggers escalation, and records that decision in the architecture audit trail. The Monitor ensures every sprint outcome is archived under `.harness/reviews`, giving the system the evidence it needs to refine skill files and improve quality over time.
