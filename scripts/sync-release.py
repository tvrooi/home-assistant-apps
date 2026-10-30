#!/usr/bin/env python3
"""Promote verified completed releases; no app source or credentials in this repo."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

SOURCE = 'tvrooi/Allotment'
IMAGE = 'ghcr.io/tvrooi/flybudget-ha'
FILES = {'config.yaml', 'README.md', 'DOCS.md', 'CHANGELOG.md', 'LICENSE', 'icon.png'}
ROOT = Path(__file__).resolve().parent.parent

def version_key(version):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)-up\.(\d+)', version)
    if not match:
        raise ValueError('Expected an Up release such as 0.2.0-up.4')
    return tuple(map(int, match.groups()))

def read_bundle(archive, version):
    version_key(version)
    expected = {'flybudget_up/' + name for name in FILES | {'release.json'}}
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(expected) or set(names) != expected:
            raise ValueError('Unexpected catalog files or duplicate paths')
        if any(info.file_size > 2_000_000 or (info.external_attr >> 16) & 0o170000 == 0o120000
               for info in bundle.infolist()):
            raise ValueError('Oversized file or symbolic link')
        files = {name: bundle.read('flybudget_up/' + name) for name in FILES | {'release.json'}}
    receipt = json.loads(files['release.json'])
    if receipt.get('version') != version or receipt.get('source_repository') != SOURCE or receipt.get('image') != IMAGE:
        raise ValueError('Unexpected source, image or version')
    if not re.fullmatch(r'[0-9a-f]{40}', receipt.get('source_commit', '')):
        raise ValueError('Invalid source commit')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', receipt.get('image_digest', '')):
        raise ValueError('Invalid image digest')
    if set(receipt.get('files', {})) != FILES:
        raise ValueError('Incomplete file manifest')
    for name in FILES:
        if hashlib.sha256(files[name]).hexdigest() != receipt['files'][name]:
            raise ValueError('Catalog checksum mismatch: ' + name)
    config = files['config.yaml'].decode()
    expected_config = {'version': "'" + version + "'", 'image': IMAGE, 'slug': 'flybudget_up',
                       'watchdog': "'tcp://[HOST]:[PORT:3001]'",
                       'url': 'https://github.com/' + SOURCE + '/tree/' + receipt['source_commit']}
    for key, value in expected_config.items():
        if re.findall(r'(?m)^' + key + r':\s*(.+)$', config) != [value]:
            raise ValueError('Unexpected config field: ' + key)
    # Network/API/host privileges must never sneak into catalog-only promotion.
    if re.search(r'(?m)^(?:privileged|host_network|hassio_api|docker_api|full_access|map):', config):
        raise ValueError('Unexpected app permissions; review manually')
    return files, receipt

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', help='Optional exact completed Up release tag')
    args = parser.parse_args()
    releases = json.loads(run('gh', 'api', 'repos/' + SOURCE + '/releases?per_page=100'))
    candidates = []
    for release in releases:
        tag = release['tag_name']
        try:
            key = version_key(tag.removeprefix('v'))
        except ValueError:
            continue
        if tag.startswith('v') and not release['draft'] and any(a['name'] == 'home-assistant-app.zip' for a in release['assets']):
            if not args.tag or tag == args.tag:
                candidates.append((key, tag))
    if not candidates:
        if args.tag:
            raise ValueError('No completed release with a catalog bundle for this tag')
        print('No completed Up releases yet.')
        return
    _, tag = max(candidates)
    version = tag[1:]
    current_path = ROOT / 'flybudget_up/release.json'
    if current_path.exists():
        current = json.loads(current_path.read_text())
        if version_key(version) <= version_key(current['version']):
            print('Catalog already current; no downgrade or replacement of an existing version.')
            return
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / 'home-assistant-app.zip'
        run('gh', 'release', 'download', tag, '--repo', SOURCE, '--pattern', archive.name, '--dir', directory)
        files, receipt = read_bundle(archive, version)
        run('gh', 'attestation', 'verify', str(archive), '--repo', SOURCE,
            '--source-ref', 'refs/tags/' + tag, '--source-digest', receipt['source_commit'],
            '--signer-workflow', SOURCE + '/.github/workflows/release.yml', '--deny-self-hosted-runners')
        digest = run('docker', 'buildx', 'imagetools', 'inspect', IMAGE + ':' + version,
                     '--format', '{{.Manifest.Digest}}')
        if digest != receipt['image_digest']:
            raise ValueError('The public image tag does not match the signed release digest')
        destination = ROOT / 'flybudget_up'
        destination.mkdir(exist_ok=True)
        for name, data in files.items():
            (destination / name).write_bytes(data)
    print('Promoted ' + tag + ' from ' + receipt['source_commit'])

if __name__ == '__main__':
    main()
