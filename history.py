"""Read Python functions on a bounded first-parent history; never import repo code."""
import ast
import copy
import hashlib
import json
from pathlib import Path
from fixture import git

def symbols(source, path, revision):
    tree = ast.parse(source)
    found = {}
    lines = source.splitlines()
    def visit(nodes, prefix=''):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + node.name
                normal = copy.deepcopy(node)
                normal.name = '_symbol_'
                fingerprint = hashlib.sha256(ast.dump(normal, include_attributes=False).encode()).hexdigest()
                found[(path, name)] = {'name':name, 'path':path, 'revision':revision,
                    'start':node.lineno, 'end':node.end_lineno,
                    'source':'\n'.join(lines[node.lineno-1:node.end_lineno]), 'fingerprint':fingerprint}
                visit(node.body, name + '.')
            elif isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + '.')
    visit(tree.body)
    return found

def mine(repo, limit=100, progress=None):
    if not 2 <= limit <= 200:
        raise ValueError('History limit must be between 2 and 200 commits')
    revisions = git(repo, 'rev-list', '--first-parent', f'--max-count={limit}', 'HEAD').splitlines()[::-1]
    ghosts, previous, births, skipped = [], {}, {}, []
    for index, rev in enumerate(revisions):
        current = {}
        paths = git(repo, 'ls-tree', '-r', '--name-only', rev).splitlines()
        for path in paths[:200]:
            if not path.endswith('.py'):
                continue
            source = git(repo, 'show', f'{rev}:{path}')
            if len(source) > 100_000:
                skipped.append({'revision':rev, 'path':path, 'reason':'file_size_limit'})
                continue
            try:
                current.update(symbols(source, path, rev))
            except SyntaxError:
                skipped.append({'revision':rev, 'path':path, 'reason':'Python_parse_error'})
        for key, value in current.items():
            if key not in previous:
                births[key] = rev
        for key, old in previous.items():
            if key in current:
                continue
            matches = [v for k,v in current.items() if k not in previous and v['fingerprint']==old['fingerprint']]
            ghost = {**old, 'id':hashlib.sha256((rev+old['path']+old['name']).encode()).hexdigest()[:16],
                'birth_observed':births[key], 'disappearance':rev,
                'message':git(repo, 'show', '-s', '--format=%s', rev),
                'status':'renamed_or_moved' if len(matches)==1 else 'removed_on_observed_mainline',
                'descendant':matches[0] if len(matches)==1 else None,
                'diff':git(repo, 'show', '--format=', '--no-ext-diff', '--no-renames', rev, '--', old['path'])}
            ghosts.append(ghost)
        previous = current
        if progress:
            progress(index+1, len(revisions))
    return {'commits':len(revisions), 'scope':'bounded first-parent Python AST scan',
            'ghosts':ghosts, 'living':list(previous.values()), 'skipped':skipped,
            'truncated':len(revisions)==limit}

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('repo'); p.add_argument('--limit',type=int,default=100)
    args=p.parse_args()
    print(json.dumps(mine(Path(args.repo).resolve(), args.limit), indent=2))
