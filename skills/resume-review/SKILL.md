---
name: resume-review
description: Check a resume's engineering claims against the author's own git history (commits, git blame, MR and PR descriptions), and mine that history for stronger accomplishments to replace or improve the bullets. Use when the user asks to verify, fact-check or audit their resume or CV against their code, commits, MRs or PRs; to find their best or most impressive work at a company for a resume; to see whether anything they did beats their current bullets; or to draft resume bullets from their contributions.
---

# Resume review

The skill has two modes, and they usually run together:

- **Verify.** Check every claim on the resume against evidence and give each bullet a verdict.
- **Mine.** Rank everything the user shipped, set the top items against the current bullets,
  and propose what to replace, keep, improve or add.

## Ground rules

- **Read only.** Never push, comment, label, post to chat or change a repo. Calls to the user's
  own Git host API are reads.
- **The resume is personal data.** Copy it into its own scratch folder. Never write the contact
  details, or the resume itself, into a report file, commit, memory note or this repo.
- **Never invent a number.** Every number in a proposed bullet must be reproducible from an MR
  or PR description, a commit, `git blame` or a file you parsed. Cite where it came from. If a
  number on the resume can't be reproduced, say so and offer wording that doesn't need it.
- **Credit honestly.** When blame shows someone else generalized or extended the work, say which
  part was the user's and which was theirs. The user will be asked about it in an interview.
- **Shipped means merged.** An open or draft MR is "in review". A closed, unmerged MR was not
  delivered.
- **Cheap first.** MR and PR descriptions hold the benchmarks, site measurements and test lists.
  Read those before touching repos. Don't sweep every repo with `git log -p`, and don't grep all
  session logs; ask first if one seems necessary.

## 1. Read the resume

```bash
ls -t ~/Downloads | grep -i -E 'resume|cv|<surname>' | head   # newest first
mkdir -p "$SCRATCH/resume" && cp ~/Downloads/<file>.pdf "$SCRATCH/resume/resume.pdf"
pdftotext -layout "$SCRATCH/resume/resume.pdf" "$SCRATCH/resume/resume.txt"
```

If an older copy exists, diff the two (`diff <(tr -s ' ' <old.txt) <(tr -s ' ' <new.txt)`).
Newly added claims need the most scrutiny.

Split each bullet into atomic claims: numbers, counts, dates, and scope words such as "adopted
by", "fails a merge", "in production", "across N repos" and "since".

## 2. Identities and inventory

- Author identities: `git config user.email`, then
  `git -c log.showSignature=false log --all --format='%an <%ae>' | sort | uniq -c` in a repo
  the user works in.
- Dump every MR and PR the user authored, once:

  ```bash
  ~/.claude/skills/resume-review/scripts/dump_mrs.sh "$SCRATCH/mrs"   # writes mrs.json
  ```

  It reads GitLab through `glab` (set `GITLAB_HOST` for a self-hosted instance) and GitHub
  through `gh`, whichever is logged in, and normalizes both into one list.
- Optional repo inventory: count the user's commits per repo with a 20-second timeout per repo.
  Skip vendored third-party repos. Use it for dates ("since January") and breadth ("ten repos").

## 3. Verify each claim

Map each claim to its MR or PR:

```bash
python3 -I ~/.claude/skills/resume-review/scripts/grep_mrs.py "$SCRATCH/mrs/mrs.json" \
  'delta=cursor|delta|239' 'tests=playwright|end-to-end|e2e'
```

Then check it according to what kind of claim it is.

| Claim | How to check it |
| --- | --- |
| A measured number (×, %, KB, ms) | Find the table or benchmark in the description and recompute the ratio. Note the conditions: a benchmark or a production measurement, how many samples, what load. |
| "Built" or "shipped" X | Is the MR merged? Is the commit on the default branch (`git branch -r --contains <sha>`)? How much of it survives (`git blame origin/<default> -- <file> \| grep -c <email>`)? |
| "N tests" | Count `def test_`, `it(` and `test(` added in each MR's diff (GitLab `merge_requests/:iid/changes?access_raw_diffs=true`, GitHub `gh pr diff`). Split merged from open, classify by file or fixture, and grep the added lines for sleeps, retries and flaky or rerun markers when the claim mentions them. |
| A coverage percentage of a catalog | Parse the catalog at the commit before and after (Qt `.ts` is XML, gettext `.po` is text). Try each definition (entries, unique sources, translated and different from the source) and report which one reproduces the claim. |
| "Lines of X" | Take `--numstat` additions **and** deletions, then open the biggest files. Re-extracts, lockfiles, generated code and reverted churn inflate it. Prefer a count with meaning: strings, endpoints, tests. |
| "Adopted by others", "used by other teams", "enforced in CI" | Look for other authors' commits or MRs that reference it, dependents on default branches (`package.json`, imports) and CI configs, including shared pipeline includes. If there's no evidence, the verdict is ❌ until the user shows otherwise. |
| A date range | First and last authored commit. |
| Outside git: on-site work, mentoring, a debugging story, a customer's name | Mark it ❔, say what would evidence it, and don't guess. Commit timezone offsets are weak evidence, because dev machines keep their home timezone. |

Verdicts: ✅ holds · ⚠️ true, but a number or scope is off (give the right one) · ❌ no evidence,
or contradicted · ❔ outside git.

## 4. Mine for better material

```bash
python3 -I ~/.claude/skills/resume-review/scripts/rank_mrs.py "$SCRATCH/mrs/mrs.json" --top 40
```

It scores each MR on the signals in its description: merged, measured outcomes, production or
site impact, defect severity, adoption by others and test evidence. It prints the evidence
snippets behind each score. It also lists **series**: the same change made in many repos, which
is a cross-team initiative worth one bullet.

Read the top 25 or so descriptions, then verify each candidate as in step 3 (merged, survives,
numbers reproduce). A score only says where to look; it is not a ranking you can quote.

What makes a strong bullet, strongest first:

1. A measured outcome for users or the business, in production.
2. A production defect with a real consequence (lost inventory, a stalled line, wrong counts),
   traced across layers to its cause.
3. Something other people or teams adopted, shown by their own commits or dependents.
4. Breadth: many repos, teams or sites.
5. Hard technical depth (concurrency, protocols, performance), with a number.
6. Tests, only when they gate something or caught something.

For each current bullet, ask whether a candidate beats it on these criteria with stronger
evidence. Decide **Replace**, **Keep**, **Improve** (same story, better number or wording) or
**Add**.

## 5. Report

1. A table of the current bullets: bullet · verdict · evidence (MR, commit and file refs).
2. A table of stronger candidates: candidate · evidence · its number · the bullet it beats.
3. Drafted bullets, each followed by its evidence refs. Keep the user's voice: strong verb,
   what changed, the number, how.

Give the report in the terminal. Don't publish it; the resume is private. When you save what you
learned to memory, save the verdicts and refs only, never contact details.

## Pitfalls

- `log.showSignature=true` prints GPG lines into the output and inflates counts. Always run
  `git -c log.showSignature=false`.
- `--all` counts every rebased copy of a commit. Dedupe by subject and date, or count MRs instead.
- The local `origin/<default>` may be stale. Take the MR state from the API.
- Blame on the default branch credits a later refactor to whoever refactored it. Read the original
  commit to credit where the idea started.
- A self-hosted GitLab needs `GITLAB_HOST`. A 401 is usually the wrong host, not an expired token.
- GitLab blob search may be off (it needs advanced search). Fall back to `git log -S` in local
  clones.
