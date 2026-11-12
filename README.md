# resume-review-skill

A [Claude Code](https://claude.com/claude-code) skill that checks a resume against the author's
own git history, then mines that history for stronger material.

| Skill | What it does | Changes outside Claude | Needs |
| --- | --- | --- | --- |
| [resume-review](skills/resume-review/) | Verifies each resume claim against your commits, `git blame` and MR/PR descriptions (✅ / ⚠️ / ❌ / ❔ with refs), then ranks everything you shipped and proposes bullets that replace, keep, improve or add to the current ones. Every number it proposes is reproduced from evidence. | none: read-only | python3, pdftotext, git; glab and/or gh logged in |

## Install

```bash
git clone https://github.com/jackalexandergeo/resume-review-skill.git ~/resume-review-skill
~/resume-review-skill/install.sh
```

`install.sh` links each skill folder into `~/.claude/skills/`, so a `git pull` updates it. Start a
new Claude Code session and ask it to check your resume against your commits, or type
`/resume-review`.

The resume, its contact details and the reports stay on your machine. Nothing in this repo is
specific to one employer.
