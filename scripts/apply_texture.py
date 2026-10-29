"""Execute inside Style3D: runpy.run_path(path, init_globals={'JOB': job_path})."""
import json
import traceback
from pathlib import Path


def execute(job_path, spy):
    job_path = Path(job_path).resolve()
    job = json.loads(job_path.read_text(encoding='utf-8-sig'))
    resolve = lambda p: (job_path.parent / p).resolve()
    image, output = resolve(job['image']), resolve(job['out_dir'])
    if not image.is_file():
        raise FileNotFoundError(image)
    with image.open('rb') as stream:
        head = stream.read(8)
    if not (head == b'\x89PNG\r\n\x1a\n' or head.startswith(b'\xff\xd8\xff')):
        raise ValueError('Supply a PNG or JPEG image')
    sides = job.get('sides', ['front', 'back'])
    if not sides or len(sides) != len(set(sides)) or set(sides) - {'front', 'back'}:
        raise ValueError('sides must contain front and/or back, without duplicates')
    ids = list(spy.GetAllClothPieceIds())
    if not ids:
        raise ValueError('Current project has no cloth pieces')
    used = set(spy.GetClothPieceFabric(i) for i in ids)
    targets = job['fabric_ids']
    if targets == 'all-used':
        targets = sorted(used)
    if not isinstance(targets, list) or not targets:
        raise ValueError('fabric_ids must be a nonempty list or all-used')
    if any(type(i) is not int or i <= 0 or i not in used for i in targets):
        raise ValueError('Target fabric must be a valid fabric used by current pieces')
    if len(set(targets)) != len(targets):
        raise ValueError('Duplicate fabric ids')
    names = sorted(spy.GetEntityName(i) for i in ids)
    # Exclusive directory reserves all outputs. Never retry into a previous run.
    output.mkdir(parents=True, exist_ok=False)
    before, after = output / 'before.sproj', output / 'textured.sproj'
    result = dict(status='failed', phase='backup', piece_count=len(ids),
                  fabric_ids=targets, image=str(image), maps=[])
    try:
        result['backup_ok'] = bool(spy.SaveProject(str(before)))
        if not result['backup_ok'] or not before.is_file() or not before.stat().st_size:
            raise RuntimeError('Backup failed; texture not changed')
        result['phase'] = 'apply'
        for fabric in targets:
            for side in sides:
                value = spy.SideType.Front if side == 'front' else spy.SideType.Back
                ok = bool(spy.ChangeFabricMap(fabric, value, spy.FabricMapType.Texture, str(image)))
                result['maps'].append(dict(fabric=fabric, side=side, ok=ok))
                if not ok:
                    raise RuntimeError('ChangeFabricMap failed; current project may be partially modified')
        result['phase'] = 'save'
        result['save_ok'] = bool(spy.SaveProject(str(after)))
        if not result['save_ok'] or not after.is_file() or not after.stat().st_size:
            raise RuntimeError('Textured project save failed')
        result['phase'] = 'reopen'
        result['reopen_ok'] = bool(spy.OpenProject(str(after)))
        if not result['reopen_ok']:
            raise RuntimeError('Textured project reopen failed')
        actual = list(spy.GetAllClothPieceIds())
        if sorted(spy.GetEntityName(i) for i in actual) != names:
            raise RuntimeError('Piece names/count changed after reopen')
        result.update(status='passed', phase='complete', reopened_piece_count=len(actual))
    except Exception:
        result['error'] = traceback.format_exc()
    result['scope'] = 'color maps; save/reopen and piece names; no physical properties or texture scale set'
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=result['status'], phase=result['phase'], report=str(output / 'result.json'))))
    return result


if __name__ == '__main__' or 'JOB' in globals():
    import spy
    if 'JOB' not in globals():
        raise RuntimeError('Supply JOB using runpy.run_path and init_globals')
    execute(JOB, spy)
