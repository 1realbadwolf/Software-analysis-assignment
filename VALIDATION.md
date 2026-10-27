# Local verification on 27 October 2026

The full local runner completed successfully on Linux with Python 3.12.14. This is local execution evidence, not a hosted GitHub Actions run.

| Check | Result |
|---|---:|
| Unit and TDD/regression cases | 64 passed |
| Real LanceDB integration cases | 7 passed |
| Gherkin BDD scenarios | 3 passed |
| Application test cases total | 74 passed |
| Quality-gate self-tests | 6 passed |
| Statement coverage | 99.09% |
| Branch coverage | 98.39% |
| Killed mutants | 179 |
| Total mutants | 222 |
| Mutation score | 80.63% |
| Coverage demonstration exit | 1 as expected |
| Mutation demonstration exit | 1 as expected |

All 222 mutants have classified killed or survived results. No skipped, untested, timeout, suspicious, interrupted or segfault results were present. Four manual assertion tests were added to the supplied suite to cover numeric compilation and exact canonical SQL. No production-source change was made by this pipeline package.

The earlier 76.06% was a different source/tool/suite version and used 213 mutants. Do not present the new 80.63% result as a directly controlled comparison against that older number. The new result is a fresh baseline for this pipeline.

Both demonstration commands used actual measurements with an explicitly impossible 101% threshold. Evidence is in `reports/demo_coverage_failure.log` and `reports/demo_mutation_failure.log`. Realistic below-threshold fixtures are independently checked by the gate self-tests. The real 75% mutation floor passes normally.

Files in `reports/` retain the unit, integration and BDD JUnit results, coverage JSON/XML, fresh mutation statistics, execution logs, dependency versions, and source hashes. Obtain the hosted run URL and passing/failing screenshots after pushing to your repository; the live-demo rubric marks depend on actually demonstrating it.
