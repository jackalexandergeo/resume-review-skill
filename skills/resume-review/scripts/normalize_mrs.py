"""Merges the raw GitLab and GitHub dumps in a folder into <folder>/mrs.json, one shared shape."""
import glob
import json
import os
import sys


def FromGitLab(mergeRequest):
    reference = mergeRequest['references']['full']
    return {
        'ref': reference,
        'host': 'gitlab',
        'project': reference.split('!')[0],
        'state': mergeRequest['state'],
        'merged_at': mergeRequest.get('merged_at'),
        'created_at': mergeRequest.get('created_at'),
        'title': mergeRequest.get('title') or '',
        'description': mergeRequest.get('description') or '',
        'url': mergeRequest.get('web_url'),
        'draft': bool(mergeRequest.get('draft')),
    }


def FromGitHub(pullRequest, mergedKeys):
    project = pullRequest['repository']['nameWithOwner']
    key = (project, pullRequest['number'])
    state = 'merged' if key in mergedKeys else ('opened' if pullRequest['state'] == 'open' else 'closed')
    return {
        'ref': '%s#%d' % key,
        'host': 'github',
        'project': project,
        'state': state,
        'merged_at': pullRequest.get('closedAt') if state == 'merged' else None,
        'created_at': pullRequest.get('createdAt'),
        'title': pullRequest.get('title') or '',
        'description': pullRequest.get('body') or '',
        'url': pullRequest.get('url'),
        'draft': bool(pullRequest.get('isDraft')),
    }


def Main(folder):
    mergeRequests = []
    for path in sorted(glob.glob(os.path.join(folder, 'gitlab-*.json'))):
        mergeRequests += [FromGitLab(item) for item in json.load(open(path))]
    githubPath = os.path.join(folder, 'github-all.json')
    if os.path.exists(githubPath):
        merged = json.load(open(os.path.join(folder, 'github-merged.json')))
        mergedKeys = {(item['repository']['nameWithOwner'], item['number']) for item in merged}
        mergeRequests += [FromGitHub(item, mergedKeys) for item in json.load(open(githubPath))]
    json.dump(mergeRequests, open(os.path.join(folder, 'mrs.json'), 'w'))
    states = {}
    for mergeRequest in mergeRequests:
        states[mergeRequest['state']] = states.get(mergeRequest['state'], 0) + 1
    print('%d MRs/PRs %s -> %s' % (len(mergeRequests), states, os.path.join(folder, 'mrs.json')), file=sys.stderr)


if __name__ == '__main__':
    Main(sys.argv[1])
