#!/usr/bin/env bash
# Links each skill folder in skills/ into ~/.claude/skills/, so a git pull updates them.
# The skills refer to each other at ~/.claude/skills/<name>/, so that is the only target.
set -euo pipefail

repository=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
target="$HOME/.claude/skills"
mkdir -p "$target"

status=0
for skill in "$repository"/skills/*/; do
	skill=${skill%/}
	name=$(basename "$skill")
	link="$target/$name"
	if [ -L "$link" ]; then
		ln -sfn "$skill" "$link"
		echo "linked  $name"
	elif [ -e "$link" ]; then
		echo "skipped $name: $link is a real folder, not a link. Move it away and run again." >&2
		status=1
	else
		ln -s "$skill" "$link"
		echo "linked  $name"
	fi
done
exit "$status"
