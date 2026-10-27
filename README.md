# COMP 441 Track E CI and quality gates

This package implements the rubric's 8-mark CI/CD component for the supplied localGPT metadata-filter module. Copy the CONTENTS of this folder to the root of the group's fork. The workflow belongs at `.github/workflows/track-e-quality.yml`, not inside another nested folder. Keep and review your repository's existing files before replacing same-named files; the supplied production source is Member 1's modified version.

## What runs

Every push and pull request runs:

1. Python 3.12 and pinned test-tool installation.
2. A clean staged copy of the repository's actual `rag_system/retrieval/filters.py`, with hashes and commit information.
3. Self-tests proving the gate rejects low scores, incomplete data and missing evidence.
4. Unit/TDD regression suite (64 cases).
5. Real LanceDB integration suite (7 cases).
6. Gherkin/pytest-bdd suite (3 scenarios).
7. Statement coverage >=95% and branch coverage >=90%, with all expected cases passing and none skipped.
8. A fresh Mutmut run on the current staged production source, using the deterministic unit suite. This run does not reuse the earlier 76.06% historical score.
9. Mutation score >=75%, with no interrupted, timed-out, untested or unclassified mutants.
10. Execution evidence upload on success or failure. The verified source/test package is published as a downloadable GitHub artifact only when all prior stages pass.

The workflow uses isolated package init files so localGPT app startup and paid/GPU model dependencies are not needed for these deterministic tests. The production filter file is copied byte for byte. Seven integration tests execute emitted SQL against a real local LanceDB table. BDD tests exercise the public filter compiler at component level; they are not full-application acceptance tests. The DeepEval/LLM harness is not bundled because its executable artifacts were not supplied.

This is continuous integration and gated artifact delivery. It does not deploy the full localGPT application to a production server; no hosting target was provided, and deployment is not required by Section 7.10.

## Match to the supplied marking sheet

| Rubric criterion | Marks | Implementation and evidence |
|---|---:|---|
| Pipeline coverage and correctness | 3 | Automatic push/PR workflow; separate unit, real integration and BDD steps; JUnit XML for each |
| Quality gate configured | 2 | `ci/gate.py` enforces coverage and current mutation score; nonzero exit fails the job |
| Threshold justification | 1 | Editable `ci/quality_policy.json`; justification below and measured results in `VALIDATION.md` |
| Live demonstration | 2 | Normal passing run plus manually dispatched failing gate run; presenter must execute on GitHub |

The implementation cannot establish a live GitHub run or guarantee marks before it is committed and executed in the group's repository.

## Threshold justification

The coverage floors of 95% statements and 90% branches were selected below the supplied measured baseline of 97.27% statements and 95.16% branches. They allow limited headroom while rejecting substantial regressions. Four additional assertion tests now exercise integer IN, integer equality, Boolean-list rejection and exact canonical SQL. Current measurements are recorded separately in `VALIDATION.md`.

The proposed mutation floor is 75%, initially chosen near the earlier 76.06% result. Mutmut 3.7.0 generates a different mutant population on the modified source, so the new count must be reported independently. All generated mutants remain in the denominator; unknown results and infrastructure problems fail the gate rather than appearing as success. The group should review and adopt the thresholds; they are not prescribed by the lecturer. Do not lower them merely to obtain a green run.

## Install in the group repository

1. Extract the ZIP on your computer or in Codespaces.
2. Copy `.github`, `ci`, `tests` and `rag_system` into the repository root. On systems hiding dotfolders, ensure `.github` is copied. Preserve the group's other files.
3. Inspect the changes with `git status` and `git diff`. The supplied source must match the intended group version.
4. Commit and push from the repository root:

```bash
git add .github/workflows/track-e-quality.yml ci tests rag_system/retrieval/filters.py
git commit -m "Add Track E automated tests and enforced quality gates"
git push
```

5. Open the repository's Actions tab and select **Track E CI and quality gates**.
6. Open the run. Show separate unit, integration, BDD, coverage-gate and mutation-gate steps.
7. Download the run's `track-e-evidence-...` artifact. Keep the run URL and screenshots for the final report.

Repository rules or branch protection must also require the **Hybrid tests and enforced quality gates** status check if you want failed checks to block merging. A failing job blocks artifact delivery already; configuring branch protection needs repository-owner access and is not performed by this package.

## Demonstrate the gate failing

After committing the workflow to the default branch, go to Actions > Track E CI and quality gates > Run workflow.

- `demo: none`: normal thresholds.
- `demo: coverage-gate`: statement threshold becomes 101% for this execution. Passing tests still cannot satisfy the coverage gate.
- `demo: mutation-gate`: tests and coverage pass first; mutation threshold becomes 101% for this execution, so the mutation gate fails on actual fresh results.

These options intentionally misconfigure one threshold for a controlled demonstration; they do not fabricate measurements or change production code. Both runs should show a red failed job. Reports are still uploaded, while the verified-suite delivery step is skipped. Explain the changed threshold during the presentation. Keep one genuine normal green run and one red demo run as evidence. The gate self-tests additionally exercise realistic below-threshold results.

## Local verification

From the repository root:

```bash
python -m pip install -r ci/requirements.txt
python ci/run_local.py
```

Results are under `reports/`; the staged disposable test workspace is under `build/track_e/`. The script exits at the first failure. Linux is required for the pinned Mutmut version; use GitHub Actions, Codespaces, Colab or WSL if your laptop runs Windows.

To demonstrate a failing gate locally after a normal run:

```bash
python ci/gate.py coverage --demo coverage-gate
python ci/gate.py mutation --demo mutation-gate
```

Each command should return exit status 1. Normal gate commands use no demo flag.

## Presentation script

“The pipeline runs automatically on every push and pull request. It checks 64 unit and regression cases, seven integration tests against a real LanceDB table, and three BDD scenarios. It requires at least 95 percent statement coverage, 90 percent branch coverage and a 75 percent mutation score. A below-threshold or incomplete result fails the job and prevents delivery of the verified suite. Reports are retained for review. I will first show the normal run, then a controlled failing gate run.”

Use the actual measured score from the run you demonstrate, not a historical score from another version.

## Sources and contribution

- COMP 441 Group Project Brief, Section 7.10, and the supplied mark-sheet image, rows 12.1–12.4.
- GitHub Python workflows: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- GitHub manual execution: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- Mutmut configuration: https://mutmut.readthedocs.io/en/latest/

The OpenAI assistant prepared the new workflow, gate scripts, integration tests and four assertion tests, and ran local verification. Include this contribution in the group AI-use declaration. New execution is dated 27 October 2026. The original uploaded hybrid and TDD files retain their earlier history.
