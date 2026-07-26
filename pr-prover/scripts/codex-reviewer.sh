#!/bin/sh
# The repository-owned reviewer adapter.
#
# It is the executable half of the credential-free reviewer lifecycle: pr-prover
# launches it with no GitHub credential in its environment, it runs the
# installed Codex CLI against one exact head in a disposable worktree, and Codex
# writes its finished artifact to --artifact-file. pr-prover validates that file
# and hands it to the configured relay command, which publishes it under the
# reviewer identity. Nothing here posts, and nothing here needs a token.
#
# Codex's own stdout passes straight through, so its last non-empty line is read
# by pr-prover as the lane verdict:
#
#     DONE: STATUS=pass|fail BLOCKING=<count> HEAD=<40-hex sha>
#
# Set PR_PROVER_CODEX to invoke a Codex binary that is not on PATH as "codex".
set -eu

usage() {
	echo "usage: $0 --role R --repo O/N --pr N --head SHA --worktree DIR --artifact-file PATH [--signature TEXT]" >&2
	exit 64
}

role="" repo="" pr="" head="" worktree="" artifact_file=""
signature="Reviewed by: CodexReviewer via Hermes orchestration"

while [ $# -gt 0 ]; do
	case "$1" in
	--role) role="${2:-}"; shift 2 ;;
	--repo) repo="${2:-}"; shift 2 ;;
	--pr) pr="${2:-}"; shift 2 ;;
	--head) head="${2:-}"; shift 2 ;;
	--worktree) worktree="${2:-}"; shift 2 ;;
	--artifact-file) artifact_file="${2:-}"; shift 2 ;;
	--signature) signature="${2:-}"; shift 2 ;;
	*) echo "$0: unknown argument: $1" >&2; usage ;;
	esac
done

for required in "$role" "$repo" "$pr" "$head" "$worktree" "$artifact_file"; do
	[ -n "$required" ] || usage
done

# This lane reviews; it never publishes. A credential reaching it means the
# lifecycle was misconfigured, and running anyway would hide that.
if [ -n "${GH_TOKEN:-}" ] || [ -n "${GITHUB_TOKEN:-}" ]; then
	echo "$0: a GitHub credential reached the reviewer lane; the relay publishes, not this" >&2
	exit 78
fi

[ -d "$worktree" ] || { echo "$0: worktree is not a directory: $worktree" >&2; exit 66; }

codex="${PR_PROVER_CODEX:-codex}"
command -v "$codex" >/dev/null 2>&1 || {
	echo "$0: no Codex CLI found (looked for '$codex'; set PR_PROVER_CODEX)" >&2
	exit 127
}

rm -f "$artifact_file"

prompt=$(cat <<PROMPT
You are ${role} for an existing pull request. This is a read-only audit.

Repo: ${repo}
PR: #${pr}
Exact head under review: ${head}
Worktree (read it; do not modify it): ${worktree}

Review the complete diff and the repository guidance at this exact head. You
have no GitHub credential and must not try to post anything: write your finished
artifact to this file instead, and the trusted parent relay will publish it.

Artifact file to write: ${artifact_file}

The artifact must contain, each on its own line somewhere in the body:

  ROLE=${role}
  ${signature}

and it must quote the exact head ${head}. State your verdict, every blocking
finding with file and line, and the commands you ran with their results.

Then print, as the last non-empty line of your own stdout, exactly:

  DONE: STATUS=pass|fail BLOCKING=<number of blocking findings> HEAD=${head}
PROMPT
)

cd "$worktree"
exec "$codex" exec "$prompt"
