"""Finds the MRs/PRs whose title or description matches each pattern, with the text around each hit.

Usage: grep_mrs.py <mrs.json> 'label=regex' ['label=regex' ...]
"""
import json
import re
import sys


def Snippet(text, match, width=110):
    return text[max(0, match.start() - width):match.end() + width].replace('\n', ' ')


def Main(path, queries):
    mergeRequests = json.load(open(path))
    for query in queries:
        label, pattern = query.split('=', 1)
        expression = re.compile(pattern, re.I)
        print('##### %s  /%s/' % (label, pattern))
        for mergeRequest in mergeRequests:
            text = mergeRequest['title'] + '\n' + mergeRequest['description']
            matches = list(expression.finditer(text))
            if not matches:
                continue
            mergedOn = ' ' + mergeRequest['merged_at'][:10] if mergeRequest.get('merged_at') else ''
            print('- %s [%s%s] %s' % (mergeRequest['ref'], mergeRequest['state'], mergedOn, mergeRequest['title'][:90]))
            for match in matches[:2]:
                print('    …%s…' % Snippet(text, match))


if __name__ == '__main__':
    Main(sys.argv[1], sys.argv[2:])
