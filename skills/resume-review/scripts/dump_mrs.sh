#!/usr/bin/env bash
# Dumps every MR (GitLab, through glab) and PR (GitHub, through gh) the current user authored
# into <out>/mrs.json, normalized to one list: ref, host, project, state, merged_at, created_at,
# title, description, url. state is merged, opened or closed on both hosts.
# Usage: dump_mrs.sh <out-dir>     (set GITLAB_HOST for a self-hosted GitLab)
set -euo pipefail

out=${1:?usage: dump_mrs.sh <out-dir>}
mkdir -p "$out"
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# glab auth status fails when any configured host fails, so ask the API itself.
if command -v glab >/dev/null && glab api user >/dev/null 2>&1; then
	page=1
	while :; do
		glab api "merge_requests?scope=created_by_me&state=all&per_page=100&page=$page" >"$out/gitlab-$page.json"
		count=$(python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$out/gitlab-$page.json")
		echo "gitlab page $page: $count" >&2
		[ "$count" -lt 100 ] && break
		page=$((page + 1))
	done
else
	echo "glab not logged in: skipping GitLab" >&2
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
	fields=repository,number,title,state,body,createdAt,closedAt,url,isDraft
	gh search prs --author=@me --limit 1000 --json "$fields" >"$out/github-all.json"
	gh search prs --author=@me --merged --limit 1000 --json number,repository >"$out/github-merged.json"
	echo "github: $(python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$out/github-all.json") PRs" >&2
else
	echo "gh not logged in: skipping GitHub" >&2
fi

python3 -I "$here/normalize_mrs.py" "$out"
