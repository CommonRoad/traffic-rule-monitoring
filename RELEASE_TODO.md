# Open Points for the Public Release

Open work before this repository can be published as `github.com/CommonRoad/traffic-rule-monitoring`.
This is the URL the paper links to (`evaluation.tex:8`, `conclusion.tex:21`).
Done so far, committed on branch `release/public`: README rewrite, dependency cleanup, Dockerfile, code fixes.

> Delete this file before the public release.

## Build and reproduction plan

Next steps toward a clean build from public sources that reproduces the paper's results.
The paper itself isn't changed in this plan; it is updated later in a separate step.

1. **Clean the working tree.** Done.
   - Deleted the untracked `selected_scenarios` files.
   - Reverted `predicate_costs_intersection{,_inverted}.yaml` to their committed versions. They work with the current build:
     - rv-monitors ignores unused names;
     - a missing predicate gets cost 0 and probability 1;
     - all values are in range;
     - C3–C6 of 03 on DEU_Salzwedel-107 run without errors.
2. **Freeze the dependency stack.** Postponed: for reproducing the results, the image is built from local copies of the dependencies (`docker/prepare_sources.sh`). Before publishing, merge, then tag, in this order:
   1. environment-model: !218 and `chore/public-release`.
   2. rv-monitors: !71, !73, !74, the §2 verdict fixes and `release/public-prep`.
   3. commonroad-monitor:
      - commit the license change;
      - switch `pyproject.toml` and `cmake/external/External{RVMonitor,EnvironmentModel}.cmake` to HTTPS GitHub URLs at the tags from 1 and 2;
      - pin `commonroad-io` to a release instead of `feature/new-format`.
   4. reactive-planner (`integration_crmonitor`), commonroad-prediction (has uncommitted changes) and commonroad-carla-interface. Check that their own pins point at these tags and not at `develop` or SSH.
   5. Push everything to `github.com/CommonRoad/*`.
3. **Docker build.**
   - Run `docker/prepare_sources.sh`, then `docker build --no-cache`. The sources are copied from the local checkouts, so the build needs no SSH keys or LRZ access.
   - Check `docker/sources/MANIFEST.txt`: commonroad-prediction is copied with uncommitted changes, and commonroad-velocity-planner is a detached checkout at the commit the local venv uses.
   - In the container, check that `crcpp` and the env-model inside `crmonitor` come from the same tag. A mismatch is an ABI risk.
   - Check that `gen_fmla`/`gen_log` run.
   - Status: the image builds from the local sources. The base image is now `python:3.11-trixie` with GCC 14: bullseye is EOL (its security packages are gone from the mirror), and forcing GCC 13 on trixie breaks linking against the system spdlog.
     In the container, 00 and 07 run, `gen_fmla` generates formulas, and the monitor rejects trajectories in 00 (so `crcpp` and `crmonitor` match).
4. **Reproduce the results in the container.**
   - Quick ones: 00, 07, 10, 04, 06. Check 04 and 06 on USA_Peach-4_9_T-1 specifically.
   - Long ones: 01, 02, 03, 05, with the paper's `--threads`.
   - CARLA: 08 and 09 against CARLA 0.10.
   - A 0.0 timing in the 03/05 output means a failure or timeout, not a fast run.
5. **Compare against the paper without editing it.**
   - Compare 03 with Tab. `comp_time_scenario_evaluation` and 05 with Tab. `comp_time_planning`. Also check the figures from 01, 02 and 07/10.
   - The AND-reordering fix in rv-monitors changes the timings; the expected order is C3 > C4 > C5 > C6.
   - If 02 regenerates the predicate costs, commit them before running 03 and 05.
6. **Final checks.**
   - `pre-commit run --all-files` passes on the first run.
   - The `git grep` check also passes in the dependency repos.
   - Push the image to ghcr.io, then follow the README's Docker steps on a clean machine.

## Blockers

- [ ] **Make the dependencies public.** rv-monitors, environment-model, commonroad-monitor, reactive-planner (`integration_crmonitor`), commonroad-prediction, and commonroad-carla-interface are all private on gitlab.lrz.de.
  - Create the GitHub repos under `CommonRoad/`, or check that the README links point to the right repos.
  - Is `traffic-rule-monitoring` meant to be this evaluation repo, or the monitor repo itself? Adjust the README links if needed.
- [ ] **commonroad-monitor fetches its dependencies over SSH from LRZ at `develop`.** Switch these to public HTTPS GitHub URLs at fixed tags:
  - `pyproject.toml` dependencies `commonroad_cpp @ git+ssh://…` and `rv-monitors @ git+ssh://…`;
  - `cmake/external/ExternalRVMonitor.cmake` and `cmake/external/ExternalEnvironmentModel.cmake`.
  - Also check its `commonroad-io @ …@feature/new-format` dependency.
- [ ] **Switch the `Dockerfile` back to public sources.** It currently copies the dependencies from `docker/sources/` (see `docker/prepare_sources.sh`). Once the repos are public and tagged, decide whether to fetch them from GitHub at the tags or keep shipping the copies.
- [ ] **Build and publish the Docker image** as `ghcr.io/commonroad/traffic-rule-monitoring/traffic-rule-monitoring:latest`. Check that `docker build` works without SSH keys or LRZ access.
- [ ] **Fix the crash on USA_Peach-4_9_T-1.**
  - `04_cr_scenario_eval_visualization.py` fails with `RuntimeError: Obstacle::rearSCustom CCS - Curvilinear Projection Error - Obstacle ID: 134 - Time Step: 1`, raised in `monitor.evaluate_scenarios_on_given_egos`.
  - It is a regression in the environment model; the paper tables contain results for this scenario.
  - 03, 05, and 06 probably fail on this scenario too.
  - The same error also hits DEU_Salzwedel-107_1_T-7 in 03:
    - R_G1 throws `Obstacle::getCurvilinearOrientationCustom CCS - Curvilinear Projection Error - Obstacle ID: 20132 - Time Step: 0`.
    - In C1/C2 (no short-circuiting) the monitor skips the whole scenario and returns an empty result. 03 then reports 0.0 for these configs.
    - C3–C6 evaluate fine, presumably because short-circuiting never reaches the failing predicate.
    - This doesn't depend on the predicate cost table. Re-check after !218.
- [ ] **Add a `LICENSE`.** The README already links to it. The dependencies are BSD-3-Clause (rv-monitors, relicensed on `release/public-prep`), CC BY-NC-ND 4.0 (commonroad-monitor), and AGPL-3.0 (environment-model). Pick something compatible, and add a `license` field to `pyproject.toml`.

## Paper and results

- [ ] Merge the open dependency MRs: rv-monitors !71, !73, !74 and the §2 verdict bugs; environment-model !218 (see `code_changes.md` in the paper repo).
- [ ] Re-run all experiments (see `evaluation_runs.md` in the paper repo). Compare the output of 03 and 05 with Tab. `comp_time_scenario_evaluation` and Tab. `comp_time_planning`.
- [x] Decided: the `selected_scenarios` work stays out of the release. Delete `scenarios/selected_scenarios/` and the 4 untracked planning configs. Revert the intersection cost YAMLs (see step 1 of the build plan).
- [ ] Fill in the BibTeX in the README once known (title, journal, volume, number, pages, year, DOI), then uncomment the Citation section.
- [ ] Funding acknowledgment: still TBD in the paper. Copy it into the README once it is decided.

## Repository content

- [ ] **Hydra binaries.** `src/evaluation/monitor/exec/gen_fmla` and `gen_log` are generators from Hydra/Vydra (bitbucket.org/krle/hydra). Check whether the Hydra license allows shipping these binaries. If not, build them in the Docker image and remove them from the repo.
- [ ] Data licensing: check that all scenarios may be redistributed (NGSIM-based `USA_*`, `DEU_Salzwedel-107`, the CommonRoad set-based benchmark scenarios). Add attribution to the README's "Data" section if needed.
- [ ] Optional: add a `CITATION.cff`.
- [ ] `configurations/predicates/monitor.yaml` isn't used by any script. It's a config for the standalone commonroad-monitor CLI. Keep it (and document it in the README) or remove it.

## Verification before publishing

- [ ] Run all scripts in the Docker image: 00–07 and 10, plus 08/09 with a CARLA 0.10 server.
  - Already passed locally, with the current venv: 00, 07, `10 --limit 2`, and 01 with reduced iterations.
  - Not yet run: 02, 03, 05, 06, 08, 09.
- [ ] `pre-commit run --all-files` passes (hooks updated to pre-commit-hooks v6.0.0 and ruff v0.17.0).
- [x] `git grep -nE "/home/|gitlab|lrz\.de|sebastian"` returns only the author entry in `pyproject.toml`.
- [ ] Check the rendered README on GitHub: the image, all links, and every script name resolve.

## Publishing

- [ ] Create the GitHub repo `CommonRoad/traffic-rule-monitoring` with a **single squashed commit** of the release tree, not the 161 private commits. Leave out `RELEASE_TODO.md`, `CLAUDE.md`, `.claude/`, `.idea/`, and `output/`.
- [ ] Check that the redirect `redirect.cps.cit.tum.de/traffic-rule-monitoring` points to the repo.
