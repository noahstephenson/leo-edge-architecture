"""Regenerate selected evidence and figures independently, then compare content."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path, text=False):
    content = path.read_bytes()
    if text:
        content = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/reproduced/verification')
    args = parser.parse_args()
    scratch = args.output.resolve()
    if scratch.exists() and any(scratch.iterdir()):
        parser.error('Use a fresh scratch directory')
    subprocess.run([sys.executable, 'experiments/e13_mbse_evidence.py', '--output', str(scratch)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'figures/scripts/fig_mt2_deadline.py', '--evidence', str(scratch),
                    '--output', str(scratch / 'figures')], cwd=ROOT, check=True)
    failures = []
    manifest = json.loads((ROOT / 'results/current/manifest.json').read_text())
    for name in [*manifest['result_sha256'], 'manifest.json']:
        if digest(ROOT / 'results/current' / name, True) != digest(scratch / name, True):
            failures.append(name)
    figures = json.loads((ROOT / 'figures/current/manifest.json').read_text())
    for name in [*figures['output_sha256'], 'manifest.json']:
        if digest(ROOT / 'figures/current' / name, name.endswith('.json')) != digest(scratch / 'figures' / name, name.endswith('.json')):
            failures.append('figures/' + name)
    if failures:
        raise RuntimeError('Regeneration differs: ' + ', '.join(failures))
    print('Independent evidence and figure regeneration matches current artifacts')


if __name__ == '__main__':
    main()
