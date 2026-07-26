---
id: topic.technology.foundation
kind: topic
status: active
---

# Technology Topic Foundation

## Classify the technical task

Identify the subject:

- product or service release;
- library, framework, repository, or model;
- protocol, standard, architecture, or proposal;
- tutorial or migration;
- benchmark or comparison;
- outage, vulnerability, or incident;
- technical review or adoption analysis.

Record whether the article describes an announcement, documented behavior, reproduced observation, operational experience, or inference. These are different evidence classes.

## Technical object record

Before drafting, record when applicable:

- exact name, owner or maintainers, version, date, and release channel;
- availability, region, plan, permissions, and feature flags;
- environment, configuration, dependencies, and compatibility;
- documented behavior and claimed benefit;
- observed or reproduced behavior and test procedure;
- experimental, beta, deprecated, or roadmap status;
- security, privacy, migration, and operational boundaries.

If version, availability, environment, or feature status could change the reader's decision and remains unresolved, block or narrow the claim.

## Evidence

- Prefer official documentation, specifications, source repositories, release notes, issue trackers, and reproducible tests.
- Record product, version, date, environment, configuration, and feature status.
- Separate documented behavior, vendor claims, observed behavior, benchmarks, and inference.
- For performance claims, preserve workload, hardware, dataset, baseline, repetitions, and uncertainty.
- For security claims, distinguish a design property, configured behavior, reported vulnerability, and verified exploitability.

### Evidence roles

Use:

- specifications and official documentation for defined behavior;
- release notes and repositories for version history and implementation state;
- reproducible tests for observed behavior;
- issue trackers for attributed reports, not automatic proof of a universal defect;
- vendor material for vendor claims;
- independent analysis for comparison and operational context;
- advisories and primary incident records for security or outage claims.

Documentation can be outdated or conditional. A successful test proves behavior only in its recorded environment.

### Reproducibility record

For code, procedures, tests, and benchmarks, preserve:

- question and success criterion;
- hardware, software, region, configuration, and dependencies;
- dataset or workload;
- baseline and treatment;
- commands or procedure;
- repetitions, variance, failures, and exclusions;
- raw result or stable artifact;
- limits on generalization.

Label unexecuted code as illustrative. Do not describe one local result as universal performance.

## Writing

- Begin with the user or system problem, not a feature inventory.
- Explain architecture only to the depth required by the reader.
- Include prerequisites, limitations, compatibility, and migration effects where relevant.
- Do not describe a beta, roadmap item, mockup, or experimental flag as generally available.
- Date screenshots and interface instructions when the product changes frequently.

Distinguish:

- announced from released;
- released from generally available;
- available from enabled by default;
- documented from reproduced;
- a demo from a supported production workflow;
- design intent from configured behavior;
- benchmark score from user-visible outcome.

For an architecture article, explain components only to the depth needed for the decision or mechanism. For a tutorial, include verification and failure modes. For a review, state evaluation criteria and the tested environment.

## Visuals

Technical diagrams must reflect verified components and relationships. Generated UI images are illustrative and must not be presented as screenshots of a real product. Code or labels inside generated images require manual verification.

Choose among:

- verified screenshot for exact interface state;
- diagram derived from verified components, boundaries, and data flow;
- chart constructed from preserved benchmark data;
- conceptual cover that does not imply an existing interface or feature;
- no visual when code, a table, or prose is more accurate.

Generated metrics, code, command output, interface text, logos, and product screens must not be treated as evidence. Date screenshots and record version or environment when the interface is mutable.

## Technology completion checks

- [ ] Product, version, release channel, availability, and environment are explicit where material.
- [ ] Vendor claim, documentation, observation, benchmark, and inference remain distinct.
- [ ] Code and procedures are executed or labeled illustrative.
- [ ] Benchmark workload, baseline, configuration, repetitions, and limits are preserved.
- [ ] Beta, experimental, roadmap, and deprecated states are not presented as generally available.
- [ ] Security and reliability language matches the available evidence.
- [ ] Diagrams, screenshots, code, metrics, and labels are verified and dated where needed.
