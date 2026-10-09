import zipfile
from scripts.package_project import build_package


def test_package_excludes_environment_credentials_and_conversations(tmp_path):
    for name in ('cli.py', 'README.md', '.env', 'history.jsonl', 'practice.jsonl', 'secrets.py',
                 '.conda-env/bin/python', '.ai-cli/history.jsonl', 'sessions/private.jsonl',
                 'artifacts/approval/real_acceptance.json'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('placeholder')
    (tmp_path / 'config.py').symlink_to(tmp_path / '.env')
    destination = tmp_path / 'out.zip'
    assert build_package(destination, root=tmp_path) == 2
    with zipfile.ZipFile(destination) as archive:
        assert set(archive.namelist()) == {'local-ai-cli/cli.py', 'local-ai-cli/README.md'}
