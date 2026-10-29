import importlib.util
import json
import tempfile
import unittest
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('apply_texture', Path(__file__).parents[1] / 'scripts/apply_texture.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Fake:
    SideType = SimpleNamespace(Front='front', Back='back')
    FabricMapType = SimpleNamespace(Texture='texture')

    def __init__(self, fail=None):
        self.fail, self.maps, self.saves = fail, [], []

    def GetAllClothPieceIds(self):
        return [1, 2]

    def GetClothPieceFabric(self, i):
        return 10

    def GetEntityName(self, i):
        return 'piece' + str(i)

    def SaveProject(self, path):
        self.saves.append(path)
        if self.fail == 'backup':
            return False
        Path(path).write_bytes(b'saved project')
        return True

    def ChangeFabricMap(self, *args):
        self.maps.append(args)
        return self.fail != 'map'

    def OpenProject(self, path):
        return self.fail != 'reopen'


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()) / ('fabric-skill-' + uuid.uuid4().hex)
        self.root.mkdir()
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / 'fabric.png').write_bytes(b'\x89PNG\r\n\x1a\n')
        self.job = self.root / 'job.json'
        self.write_job()

    def write_job(self, **extra):
        self.job.write_text(json.dumps(dict(image='fabric.png', out_dir='run', fabric_ids='all-used', **extra)))

    def test_success_deduplicates_used_fabric(self):
        spy = Fake()
        r = module.execute(self.job, spy)
        self.assertEqual(r['status'], 'passed')
        self.assertEqual([x[1] for x in spy.maps], ['front', 'back'])
        self.assertEqual(len(spy.saves), 2)
        self.assertTrue((self.root / 'run/before.sproj').is_file())

    def test_existing_directory_refused_before_save(self):
        (self.root / 'run').mkdir()
        spy = Fake()
        with self.assertRaises(FileExistsError):
            module.execute(self.job, spy)
        self.assertEqual(spy.saves, [])

    def test_backup_failure_does_not_apply(self):
        spy = Fake('backup')
        r = module.execute(self.job, spy)
        self.assertEqual(r['phase'], 'backup')
        self.assertEqual(spy.maps, [])
        self.assertEqual(r['status'], 'failed')

    def test_partial_map_failure_preserves_backup_no_final_save(self):
        spy = Fake('map')
        r = module.execute(self.job, spy)
        self.assertEqual(r['status'], 'failed')
        self.assertEqual(r['phase'], 'apply')
        self.assertEqual(len(spy.saves), 1)
        self.assertTrue((self.root / 'run/before.sproj').exists())

    def test_reopen_failure_reported(self):
        r = module.execute(self.job, Fake('reopen'))
        self.assertEqual(r['status'], 'failed')
        self.assertEqual(r['phase'], 'reopen')

    def test_single_side_selection(self):
        self.write_job(sides=['front'])
        spy = Fake()
        module.execute(self.job, spy)
        self.assertEqual(len(spy.maps), 1)

    def test_invalid_target_or_image_no_save(self):
        for change in [{'fabric_ids': [999]}, {'image': 'missing.png'}]:
            job = json.loads(self.job.read_text())
            job.update(change)
            self.job.write_text(json.dumps(job))
            spy = Fake()
            with self.assertRaises((ValueError, FileNotFoundError)):
                module.execute(self.job, spy)
            self.assertEqual(spy.saves, [])
            self.write_job()


if __name__ == '__main__':
    unittest.main()
