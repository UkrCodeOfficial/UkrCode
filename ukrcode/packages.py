import json
import shutil
from pathlib import Path


class PackageManager:
    def __init__(self, root=None):
        self.root = Path(root or Path.cwd())
        self.directory = self.root / ".ucod" / "packages"
        self.lock_path = self.root / "ucod.lock"

    def _read_lock(self):
        if not self.lock_path.exists():
            return {"версія": 1, "пакети": {}}
        return json.loads(self.lock_path.read_text(encoding="utf-8"))

    def _write_lock(self, lock):
        self.lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def create(self, name):
        root = self.root / name
        root.mkdir(parents=True, exist_ok=False)
        (root / "main.ucod").write_text('написати("Привіт з UkrCode!")\n', encoding="utf-8")
        (root / "ucod.toml").write_text(
            f'назва = "{name}"\nверсія = "0.1.0"\nточка_входу = "main.ucod"\n',
            encoding="utf-8",
        )
        return root

    def create_library(self, name):
        path = self.root / name
        if path.exists():
            raise FileExistsError(path)
        path.mkdir(parents=True, exist_ok=False)
        (path / "main.ucod").write_text(
            f"# Бібліотека {name}\n\nекспорт функція сума(а, б):\n    повернути а + б\n\nекспорт функція привітати(імʼя):\n    повернути \"Привіт, \" + імʼя\n",
            encoding="utf-8",
        )
        (path / "ucod.toml").write_text(
            f'назва = "{name}"\nверсія = "0.1.0"\nточка_входу = "main.ucod"\n',
            encoding="utf-8",
        )
        (path / "README.md").write_text(
            f"# {name}\n\nКористувацька бібліотека UkrCode.\n\nІмпорт:\n\n```ucod\nімпортувати {name}\nрезультат = {name}.сума(2, 3)\n```\n",
            encoding="utf-8",
        )
        return path

    def install(self, source):
        source_path = Path(source).resolve()
        manifest = source_path / "ucod.toml"
        name = source_path.name
        if manifest.exists():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if line.startswith("назва") and "=" in line:
                    name = line.split("=", 1)[1].strip().strip('"')
        destination = self.directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source_path, destination, ignore=shutil.ignore_patterns(".git", ".ucod", "*.pyc"))
        lock = self._read_lock()
        lock["пакети"][name] = {"джерело": str(source_path), "версія": "локальна"}
        self._write_lock(lock)
        return destination

    def remove(self, name):
        destination = self.directory / name
        if destination.exists():
            shutil.rmtree(destination)
        lock = self._read_lock()
        lock["пакети"].pop(name, None)
        self._write_lock(lock)

    def list(self):
        return sorted(self._read_lock()["пакети"])

    def update(self):
        lock = self._read_lock()
        for name, package in list(lock["пакети"].items()):
            if Path(package["джерело"]).exists():
                self.install(package["джерело"])