import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('sync-release.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

class CatalogTests(unittest.TestCase):
    def test_release_order_is_numeric(self):
        self.assertGreater(sync.version_key('0.2.0-up.10'), sync.version_key('0.2.0-up.9'))
        with self.assertRaises(ValueError):
            sync.version_key('../evil')

    def test_bundle_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'app.zip'
            with zipfile.ZipFile(archive, 'w') as out:
                out.writestr('../config.yaml', 'bad')
            with self.assertRaisesRegex(ValueError, 'Unexpected catalog files'):
                sync.read_bundle(archive, '0.2.0-up.4')

    def test_real_export_and_tamper_detection(self):
        # CI builds a representative fixture independently from the application repository.
        version = '0.2.0-up.4'
        commit = 'a' * 40
        files = {name: b'fixture' for name in sync.FILES}
        files['config.yaml'] = (f"version: '{version}'\nimage: {sync.IMAGE}\nslug: flybudget_up\n"
            f"watchdog: 'tcp://[HOST]:[PORT:3001]'\nurl: https://github.com/{sync.SOURCE}/tree/{commit}\n").encode()
        receipt = dict(version=version, source_repository=sync.SOURCE, source_commit=commit,
            image=sync.IMAGE, image_digest='sha256:'+'b'*64,
            files={name:hashlib.sha256(data).hexdigest() for name,data in files.items()})
        files['release.json'] = json.dumps(receipt).encode()
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'app.zip'
            def write():
                with zipfile.ZipFile(archive, 'w') as out:
                    for name,data in files.items():
                        out.writestr('flybudget_up/'+name, data)
            write()
            self.assertEqual(sync.read_bundle(archive, version)[1]['version'], version)
            files['config.yaml'] += b'hassio_api: true\n'
            receipt['files']['config.yaml'] = hashlib.sha256(files['config.yaml']).hexdigest()
            files['release.json'] = json.dumps(receipt).encode()
            write()
            with self.assertRaisesRegex(ValueError, 'Unexpected app permissions'):
                sync.read_bundle(archive, version)

if __name__ == '__main__':
    unittest.main()
