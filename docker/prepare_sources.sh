#!/usr/bin/env bash
# Copy the source code of the CommonRoad dependencies into docker/sources/ so that the Docker image can be built
# without access to their (private) git repositories.
#
# Each repository is copied from its local checkout: all tracked files with their current working-tree content,
# i.e., uncommitted changes are included and untracked files are not.
# docker/sources/MANIFEST.txt records the branch, commit, and uncommitted changes of every copied repository.
#
# Usage: docker/prepare_sources.sh [DEPS_ROOT]
#   DEPS_ROOT: directory containing the checkouts (default: parent directory of this repository)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPS_ROOT="$(cd "${1:-${REPO_ROOT}/..}" && pwd)"
TARGET="${REPO_ROOT}/docker/sources"

REPOS=(
    commonroad-io
    environment-model
    rv-monitors
    commonroad-monitor
    commonroad-velocity-planner
    reactive-planner
    commonroad-prediction
    commonroad-scenario-designer
    commonroad-carla-interface
)

rm -rf "${TARGET}"
mkdir -p "${TARGET}"
MANIFEST="${TARGET}/MANIFEST.txt"
echo "# Dependency sources copied on $(date -u +%Y-%m-%dT%H:%M:%SZ) from ${DEPS_ROOT}" > "${MANIFEST}"

for repo in "${REPOS[@]}"; do
    src="${DEPS_ROOT}/${repo}"
    if ! git -C "${src}" rev-parse --git-dir > /dev/null 2>&1; then
        echo "error: ${src} is not a git checkout" >&2
        exit 1
    fi
    mkdir -p "${TARGET}/${repo}"
    # Tracked files that still exist in the working tree (skips files deleted but not yet committed).
    (cd "${src}" && git ls-files -z | while IFS= read -r -d '' f; do
        [[ -e "${f}" || -L "${f}" ]] && printf '%s\0' "${f}"
    done | tar --null -T - -cf -) | tar -xf - -C "${TARGET}/${repo}"

    branch="$(git -C "${src}" branch --show-current)"
    commit="$(git -C "${src}" rev-parse HEAD)"
    # .git is not copied, so setuptools_scm cannot derive a version in the image; the Dockerfile reads this file.
    git -C "${src}" rev-parse --short=8 HEAD > "${TARGET}/${repo}/.git-commit"
    changes="$(git -C "${src}" status --porcelain --untracked-files=no)"
    {
        echo
        echo "${repo}: ${branch:-detached} ${commit}"
        if [[ -n "${changes}" ]]; then
            echo "  uncommitted changes (included):"
            echo "${changes}" | sed 's/^/    /'
        fi
    } >> "${MANIFEST}"
    echo "copied ${repo} (${branch:-detached} @ ${commit:0:8}${changes:+, with uncommitted changes})"
done

echo
echo "Wrote ${MANIFEST}"
