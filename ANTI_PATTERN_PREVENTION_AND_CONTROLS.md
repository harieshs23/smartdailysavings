# Anti-Pattern Prevention and Controls for the Agentic Harness

## 1. Purpose

This document defines the mandatory controls required to prevent the four failure modes observed in prior AI-generated implementation experiments:

1. direct imports across service/module boundaries, bypassing the agreed service boundary and event bus
2. raw Error throws in service methods, bypassing the typed AppError hierarchy
3. tests that assert HTTP status code without proving business-rule compliance
4. missing event bus integration, where state changes are written directly to sibling repositories

These issues are not isolated defects. They are architectural contract violations. The harness must therefore treat them as policy violations that must be prevented by design, enforced at generation time, and validated in CI and review gates.

## 2. Design Principle

The harness must follow a policy-first generation model:

- design intent is generated
- architecture and governance rules are enforced
- code is generated only within approved boundaries
- tests must validate invariants and business outcomes
- evidence is captured before approval is granted

This ensures that code generation remains aligned to architecture, domain boundaries, and business correctness.

## 3. Mandatory Governance Rules

### Rule A1: No direct cross-boundary imports

**Policy statement**
No service, module, or repository in one bounded context may import or directly invoke repository logic from another bounded context without going through the approved integration mechanism.

**Allowed patterns**
- application service contracts
- domain events
- event bus / message broker
- approved integration interfaces
- explicit outbound ports/adapters

**Forbidden patterns**
- direct repository imports from sibling modules
- direct DB writes from one domain service into another domain repository
- direct service-to-service access without a bounded integration model

**Enforcement**
- static import checks (for example, import-linter, Semgrep, or custom AST validation)
- CI policy gate for architectural boundaries
- code generation templates that prohibit direct sibling repository imports
- architecture review requirement before implementation starts

**Rationale**
This prevents hidden coupling and ensures that asynchronous interaction and event-driven behavior remain the primary communication path.

### Rule A2: No raw Error throws in service methods

**Policy statement**
Service methods must raise or propagate only typed AppError-derived exceptions. Raw generic errors are prohibited in application and domain service layers.

**Forbidden patterns**
- throw new Error(...)
- throw Error(...)
- general exception propagation without mapping to AppError
- string-based or undeclared failure handling

**Allowed patterns**
- AppError subclasses
- typed error codes and error metadata
- controlled mapping at API or boundary layer

**Enforcement**
- linter rules or AST checks banning raw throws in service code
- compile-time and review-time enforcement
- test templates requiring typed failure assertions
- mandatory error-code mapping checks in CI

**Rationale**
Typed errors preserve operational semantics, allow consistent handling, and make business errors reviewable and auditable.

### Rule A3: Business-rule tests must validate outcomes, not just HTTP status

**Policy statement**
Tests must verify business-rule compliance and resulting domain state, not just the response status code returned by an HTTP endpoint.

**Required test assertions**
- final state of the domain object or aggregate
- repository changes made through approved flows
- emitted domain events
- business invariants and validation rules
- service behavior under invalid input
- typed AppError outcomes for expected failures

**Forbidden patterns**
- expecting 200/201/400 without proving business correctness
- asserting only status codes and ignoring invariant failures
- tests that pass even when the wrong domain state is stored

**Enforcement**
- test generation templates require Given/When/Then scenarios
- all business flow tests must include invariant assertions
- review gate requires domain-state validation for critical business flows
- CI pipeline must fail when business-rule tests are missing

**Rationale**
A 200 OK response does not prove correctness. The system must validate the rule itself, not merely the API wrapper.

### Rule A4: All state transitions must integrate with the event bus

**Policy statement**
Any meaningful state change that crosses a domain or module boundary must be expressed as a domain event and processed through the approved event bus or outbox pattern.

**Allowed patterns**
- event emitted after domain state mutation
- event published through the event bus
- event-driven integration with downstream handlers
- transactional outbox pattern when required

**Forbidden patterns**
- repository writes directly from one module into another module’s persistence layer
- silent state mutation without a recorded business event
- event contract omissions for cross-context change propagation

**Enforcement**
- event contract registry and schema validation
- API or service generation templates that require event emission
- integration tests validating event publication and downstream processing
- CI checks for missing event handlers on major state changes

**Rationale**
This preserves architectural integrity, supports auditability, and makes side effects visible and maintainable.

## 4. Policy Enforcement Model

The harness must enforce these rules using multiple layers so that no single loophole bypasses protection.

### 4.1 Generation-Time Enforcement
The agent should not be allowed to generate code that violates policy.

Examples:
- templates prohibit direct sibling repository imports
- code generation prompts require AppError-based failures
- generated tests must include business invariant assertions
- generated state transitions must include event publication scaffolding

### 4.2 Static Analysis Enforcement
The CI pipeline should run policy checks before merge.

Examples:
- architecture boundary checks
- forbidden raw throw detection
- event bus usage verification
- test coverage quality checks

### 4.3 Review Gate Enforcement
The governance review process must validate that generated code matches the architecture contract.

Examples:
- design review for module boundaries
- security and governance review for event flows
- business-rule validation review before deployment

### 4.4 Runtime Verification
The running system should validate expected behavior under operational conditions.

Examples:
- event publication logs
- invariant assertions in integration tests
- domain-level monitoring and failure detection

## 5. Required Review Checkpoints

The harness should force a review workflow for any change that affects architecture or business behavior.

### Checkpoint 1: Architecture Boundary Check
Confirm:
- no direct sibling imports
- no bypass of event bus
- domain boundaries preserved

### Checkpoint 2: Error Contract Check
Confirm:
- domain/service code uses AppError hierarchy
- no raw Error throws
- failure mapping is explicit

### Checkpoint 3: Business Rule Validation Check
Confirm:
- tests validate business rules and domain state
- HTTP status is not the only assertion
- invariant-based tests exist for key flows

### Checkpoint 4: Event Contract Check
Confirm:
- relevant state transitions emit events
- downstream processing is defined
- outbox or bus integration is active

## 6. Agent Responsibilities for Anti-Pattern Prevention

### Architecture Agent
- defines bounded context boundaries
- validates import flows
- approves integration patterns
- ensures event-first design

### Governance Design Agent
- codifies control rules and review gate requirements
- maps policies to engineering standards
- maintains policy library for the harness

### Engineering Agent
- generate code only within approved patterns
- use AppError hierarchy
- ensure event-driven behavior is part of generated workflows

### QA Agent
- validate invariants, not only status codes
- prove business-rule compliance through assertions
- verify event emission and state correctness

### Audit & Evidence Agent
- capture policy checks and review evidence
- maintain traceability between requirement, code, test, and approval

## 7. Sample Policy Library

The harness should maintain a shared policy registry. Example entries:

- ARCH-001: Bounded context boundaries must be preserved
- ARCH-002: No direct imports across sibling repositories
- ERR-001: Raw throws are forbidden in service methods
- ERR-002: Typed AppError must be used for expected failures
- TEST-001: Business-rule tests required for all critical flows
- TEST-002: HTTP status alone is insufficient validation
- EVT-001: State changes require event publication
- EVT-002: Event contracts must be registered and validated

Each policy entry should include:
- policy id
- description
- owner
- enforcement mechanism
- review requirement
- exception handling procedure

## 8. Example Failure Prevention Pattern

### Example: account activation workflow

A workflow that activates an account must not:
- write account state directly in a sibling repository
- raise raw Error from a service method
- pass a test that only checks a 200 HTTP response
- skip event publication for activation state

It must instead:
- process via approved boundary service
- raise AccountActivationError or a subclass of AppError
- assert that account state changed correctly and the correct activation event was emitted
- verify a downstream consumer processed the activation event

## 9. Operational Control Model

The production environment should treat these anti-patterns as controlled exceptions with approval requirements.

Any exception to the rules requires:
- documented rationale
- explicit business owner approval
- mitigation plan
- review of residual risk
- evidence of alternate controls

This ensures the system remains governed rather than permissive.

## 10. Evidence Standard

For every major implementation or architectural change, the harness should retain evidence showing:

- policy checks passed
- architecture review completed
- event contract validated
- business-rule tests executed
- AppError handling validated
- approval or exceptions recorded

This becomes the evidence chain for governance and audits.

## 11. Conclusion

The prior failure modes are a clear signal that AI-generated implementation without strong policy enforcement produces architecturally invalid results. The harness must therefore embed these rules as mandatory controls, not guidance.

The solution is not simply “more prompting.” The solution is a governance-aware architecture that defines: 

- strict boundaries
- typed failure contracts
- invariant-based tests
- event-driven state propagation
- review and evidence requirements

Without these controls, the harness risks reproducing the same structural failures at scale.
