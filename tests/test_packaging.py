from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET


class PackagingTest(unittest.TestCase):
    def test_packages_the_setup_dashboard_assets(self):
        repository = Path(__file__).resolve().parents[1]
        view = Path("default/data/ui/views/setup_page_dashboard.xml")
        dashboard = ET.parse(repository / view).getroot()
        assets = [
            Path("appserver/static") / dashboard.attrib[attribute]
            for attribute in ("script", "stylesheet")
        ]
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "example-app"
            app.mkdir()
            shutil.copy2(repository / "package.sh", app / "package.sh")
            for folder in ("default", "appserver"):
                shutil.copytree(repository / folder, app / folder)
            subprocess.run(
                ["bash", "package.sh"], cwd=app, check=True, capture_output=True
            )
            with tarfile.open(app / "example-app.tgz", "r:gz") as package:
                for asset in [view, *assets]:
                    with package.extractfile("example-app/" + asset.as_posix()) as file:
                        self.assertEqual(file.read(), (repository / asset).read_bytes())

    def test_excludes_environment_files_and_virtualenvs(self):
        script = Path(__file__).resolve().parents[1] / "package.sh"
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "example-app"
            app.mkdir()
            shutil.copy2(script, app / "package.sh")

            for name in (
                ".env",
                ".venv/bin/python",
                "default/nested/.env",
                "default/nested/.venv/lib.py",
                ".env.example",
                ".venv_backup/keep",
                "default/app.conf",
                "bin/command.py",
                "tests/test_example.py",
                "bin/lib/tests/keep.py",
            ):
                path = app / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")

            subprocess.run(
                ["bash", "package.sh"], cwd=app, check=True, capture_output=True
            )
            with tarfile.open(app / "example-app.tgz", "r:gz") as package:
                paths = {PurePosixPath(member.name) for member in package.getmembers()}

        excluded = sorted(
            str(path) for path in paths if {".env", ".venv"}.intersection(path.parts)
        )
        self.assertEqual(excluded, [])
        self.assertIn(PurePosixPath("example-app/default/app.conf"), paths)
        self.assertIn(PurePosixPath("example-app/bin/command.py"), paths)
        self.assertIn(PurePosixPath("example-app/.env.example"), paths)
        self.assertIn(PurePosixPath("example-app/.venv_backup/keep"), paths)
        self.assertFalse(
            any(path.parts[:2] == ("example-app", "tests") for path in paths)
        )
        self.assertIn(PurePosixPath("example-app/bin/lib/tests/keep.py"), paths)


if __name__ == "__main__":
    unittest.main()
