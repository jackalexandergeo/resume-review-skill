"""Scores MRs/PRs on the resume signals in their descriptions, so you know which ones to read first.

The score only says where to look. Verify every candidate before it becomes a bullet.

Usage: rank_mrs.py <mrs.json> [--top N] [--merged-only] [--host gitlab|github]
"""
import argparse
import collections
import json
import re

MEASURED = re.compile(
    r'\b\d[\d,.]*\s?(?:×|x\b)'                                   # 239×, 33x
    r'|\b\d[\d,.]*\s?%'                                          # 16 %, 92%
    r'|\b\d[\d,.]*\s?(?:[kKMG]i?B|bytes)\b'                      # 222 KB, 190 bytes
    r'|\b\d[\d,.]*\s?(?:ms|s|sec|seconds|min|minutes|hours)\b'    # 1.4 s, 500 ms
    r'|\bfrom\s+\d[\d,.]*\S*\s+to\s+\d',                         # from 20 to 2
)
PRODUCTION = re.compile(r'\b(?:on[- ]site|production|customer|site|operators?|controller\d+|outage|incident|field|plant|warehouse)\b', re.I)
SEVERITY = re.compile(r'\b(?:lost|wrong|stuck|freez\w*|crash\w*|discard\w*|silent\w*|never|hang\w*|stall\w*|blank|broke\w*|data loss|re-?pick\w*)\b', re.I)
ADOPTION = re.compile(r'\b(?:adopt\w*|shared|reus\w*|other teams?|every (?:app|repo|list|page)|across \d+|all \d+ (?:apps|repos))\b', re.I)
TESTS = re.compile(r'\b\d+\s+(?:suites?|tests?|cases)\b|\b(?:playwright|pytest|jest|vitest|e2e|end-to-end)\b', re.I)
CONVENTIONAL_PREFIX = re.compile(r'^(?:Draft:\s*)?\w+(?:\([^)]*\))?!?:\s*', re.I)


def Count(expression, text, cap):
    return min(len(expression.findall(text)), cap)


def Score(mergeRequest):
    text = mergeRequest['title'] + '\n' + mergeRequest['description']
    signals = {
        'merged': 4 if mergeRequest['state'] == 'merged' else 0,
        'measured': 2 * Count(MEASURED, text, 5),
        'production': 1.5 * Count(PRODUCTION, text, 4),
        'severity': Count(SEVERITY, text, 3),
        'adoption': 1.5 * Count(ADOPTION, text, 3),
        'tests': 0.5 * Count(TESTS, text, 3),
        'depth': min(len(mergeRequest['description']) / 2000, 2),
    }
    return sum(signals.values()), signals


def Evidence(mergeRequest, limit=3):
    snippets = []
    for match in MEASURED.finditer(mergeRequest['description']):
        start = mergeRequest['description'].rfind('\n', 0, match.start()) + 1
        end = mergeRequest['description'].find('\n', match.end())
        line = mergeRequest['description'][start:end if end != -1 else None].strip()
        if line and line not in snippets:
            snippets.append(line[:160])
        if len(snippets) == limit:
            break
    return snippets


def Series(mergeRequests, minimum=3):
    groups = collections.defaultdict(list)
    for mergeRequest in mergeRequests:
        subject = CONVENTIONAL_PREFIX.sub('', mergeRequest['title']).lower()
        subject = re.sub(r'\bfor \S+$', 'for <repo>', subject)
        groups[subject].append(mergeRequest)
    return sorted(((subject, items) for subject, items in groups.items() if len({item['project'] for item in items}) >= minimum), key=lambda pair: -len(pair[1]))


def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--top', type=int, default=40)
    parser.add_argument('--merged-only', action='store_true', help='drop open MRs too (closed ones are always dropped)')
    parser.add_argument('--host', choices=('gitlab', 'github'), help='rank one host only, e.g. gitlab for the employer, github for personal work')
    arguments = parser.parse_args()
    kept = ('merged',) if arguments.merged_only else ('merged', 'opened')
    everything = [item for item in json.load(open(arguments.path)) if not arguments.host or item['host'] == arguments.host]
    mergeRequests = [item for item in everything if item['state'] in kept]
    ranked = sorted(((Score(item), item) for item in mergeRequests), key=lambda pair: -pair[0][0])
    for (score, signals), mergeRequest in ranked[:arguments.top]:
        mergedOn = mergeRequest['merged_at'][:10] if mergeRequest.get('merged_at') else mergeRequest['state']
        strongest = ', '.join('%s %g' % (name, value) for name, value in sorted(signals.items(), key=lambda pair: -pair[1]) if value)
        print('%5.1f  %-58s %-10s %s' % (score, mergeRequest['ref'][-58:], mergedOn, mergeRequest['title'][:80]))
        print('       [%s]' % strongest)
        for snippet in Evidence(mergeRequest):
            print('       · %s' % snippet)
    print('\n##### series (same change in 3+ repos)')
    for subject, items in Series(everything):
        states = collections.Counter(item['state'] for item in items)
        print('%3d MRs %s  %s' % (len(items), dict(states), subject[:90]))


if __name__ == '__main__':
    Main()
