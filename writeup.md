# Week 8 — Agent Orchestration: The Recipe Box Sprint
## Part I — Concurrent Agents
### Tasks Selected
- **Agent A — Shopping List:** Implemented `GET /shopping-list?ids=1,2,3`, merging recipe ingredients into a de-duplicated list.
- **Agent B — Tag Filter:** Implemented `GET /recipes?tag=breakfast`, filtering recipes by their tags while preserving the original endpoint behavior.
### Worktree Setup
Two independent Git worktrees were created from the same baseline commit (`2b795ec`):
- `week8-task-a` on branch `week8-task-a`
- `week8-task-b` on branch `week8-task-b`
Both agents worked in separate VS Code windows with independent Copilot Agent sessions. Their tasks were initiated without waiting for the other agent to finish.
### Integration and Collision Risks
Both agents modified `main.py` and `test_main.py`, which introduced a potential merge conflict.
The worktrees prevented the agents from overwriting each other's uncommitted changes. I reviewed their changes and ran tests independently before integrating either implementation.
- Agent A commit: `dd91abb`
- Agent B commit: `a9e6fac`
- Agent A standalone result: 8 tests passed.
- Agent B standalone result: 7 tests passed.
- Integration result: 12 tests passed.
Both branches were merged into `main` using non-fast-forward merges. Git integrated the changes automatically without conflicts.
This demonstrated that even logically independent tasks can affect the same source files, making isolation and integration testing essential.
## Part II — Generator–Critic Loop
### Selected Task
**Ingredient Scaling:** `GET /recipes/{id}/scaled?factor=2`
The generator implemented ingredient quantity scaling. An independent critic agent evaluated the implementation against the following rubric:
1. **Correctness:** Valid scaling, input validation, preservation of recipe data, and edge cases.
2. **Tests:** Meaningful test coverage and regression protection.
3. **Clarity:** Readable implementation, maintainability, and documentation.
### Initial Generator Implementation
Commit: `99e4bf5`
The generator implemented the scaling endpoint and added automated tests.
Result: **15 tests passed.**
### Critic Review 1 — REVISION REQUIRED
The critic identified five issues:
1. Non-finite scaling factors such as `Infinity` were accepted.
2. Compact ingredient quantities such as `200g flour` and `2eggs` were not scaled.
3. Tests did not adequately cover invalid factors and edge cases.
4. Tests used a persistent shared SQLite database.
5. README documentation was incomplete.
The critic verified these findings through targeted probes rather than relying only on the existing test suite.
### Generator Revision 1
Commit: `106684e`
The generator:
- Rejected non-finite and non-positive scaling factors.
- Added support for compact numeric quantities.
- Expanded test coverage for decimal factors, invalid inputs, and unrelated text.
Result: **16 tests passed.**
### Critic Review 2 — REVISION REQUIRED
The critic confirmed the scaling fixes but found remaining issues:
- Tests still used a shared persistent database.
- Explicit coverage for a missing `factor` parameter had been lost.
- README documentation remained outdated.
### Generator Revision 2
Commit: `80be856`
The generator:
- Introduced temporary SQLite database isolation for tests.
- Restored missing-factor validation coverage.
- Updated README documentation and endpoint behavior descriptions.
Result: **17 tests passed.**
### Follow-up Critic Review — REVISION REQUIRED
The critic discovered a numerical precision issue. Python's default Decimal context could round very large quantities, even when the scaling factor was 1.
Example:
- Input: `123456789012345678901234567890 g`
- Expected with factor 1: unchanged
- Previously observed: `123456789012345678901234567900 g`
### Generator Revision 3
Commit: `5c0c9ab`
The generator corrected Decimal precision handling and added regression tests for very large integers, long fractional quantities, and factor 1.
Result: **19 tests passed.**
### Final Critic Review — APPROVED
The independent critic reviewed the final implementation, ran the full test suite, and performed targeted API and precision probes.
The critic confirmed:
- Precision is preserved for large quantities.
- Factor 1 preserves ingredient values.
- Invalid factors return HTTP 422.
- Unknown recipes return HTTP 404 for valid scaling requests.
- Compact quantities and decimal factors work.
- Test databases are isolated.
- Existing endpoints remain functional.
- README documentation is accurate.
**Final verdict: APPROVED.**
## Agent Autonomy and Human Supervision
### Concurrent Agents
Both agents were allowed to:
- Inspect their assigned worktree.
- Modify implementation and test files.
- Execute tests and fix implementation issues.
Both agents were explicitly prohibited from:
- Editing another worktree.
- Creating commits.
- Merging branches.
- Pushing to GitHub.
I supervised the parallel execution, inspected Git status, verified test results, and performed all commits and merges manually.
### Generator Agent
The generator could modify code, tests, and documentation and run tests. Its responsibility was limited to implementation and revisions.
It was not allowed to perform the critic's role, merge branches, or push changes.
### Critic Agent
The critic operated in read-only mode. It could inspect source files, execute tests, and report findings, but could not modify files, commit, merge, or push.
I reviewed the critic's findings and passed actionable feedback to the generator. Each revision was verified and committed separately.
### Human Review Gates
Human supervision was applied at task assignment, worktree selection, code integration, generator revisions, final approval, and repository submission.
## What I Learned
Running multiple coding agents concurrently can reduce implementation time, but it also introduces coordination and integration risks. Git worktrees helped isolate each agent's changes, even though both tasks required modifications to the same source files. The generator–critic loop revealed defects that successful tests alone had not detected, including invalid numeric inputs and precision loss. Keeping separate revision commits made the feedback process transparent and easier to audit. I learned that effective agent orchestration requires both autonomy and deliberate human supervision.
## Final Validation
- Initial starter: 3 tests passed.
- Concurrent agent integration: 12 tests passed.
- Generator initial implementation: 15 tests passed.
- Generator Revision 1: 16 tests passed.
- Generator Revision 2: 17 tests passed.
- Generator Revision 3: 19 tests passed.
- Final merged `main`: **19 tests passed**.
- Final critic verdict: **APPROVED**.
## Evidence
- Git history contains both independent agent branches and merge commits.
- Generator initial implementation and three revisions have separate commits.
- Concurrent agent screenshots are stored in `docs/evidence/`.
- The critic feedback and revision sequence are documented above.
