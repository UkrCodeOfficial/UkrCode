from ukrcode.packages import PackageManager
from ukrcode.runtime import Interpreter


def test_local_package_lifecycle(tmp_path):
    manager = PackageManager(tmp_path)
    project = manager.create("приклад")
    assert (project / "main.ucod").exists()

    dependency = tmp_path / "бібліотека"
    dependency.mkdir()
    (dependency / "ucod.toml").write_text('назва = "текстові-інструменти"\nверсія = "1.0.0"\n', encoding="utf-8")
    (dependency / "main.ucod").write_text('написати("готово")\n', encoding="utf-8")

    installed = manager.install(dependency)
    assert installed.exists()
    assert manager.list() == ["текстові-інструменти"]
    assert 'текстові-інструменти' in (tmp_path / "ucod.lock").read_text(encoding="utf-8")

    manager.remove("текстові-інструменти")
    assert manager.list() == []


def test_user_library_scaffold_and_import(tmp_path):
    manager = PackageManager(tmp_path)
    library = manager.create_library("складник")

    assert library.is_dir()
    assert (library / "ucod.toml").exists()
    assert "експорт" in (library / "main.ucod").read_text(encoding="utf-8")

    installed = manager.install(library)
    interpreter = Interpreter(tmp_path)
    interpreter.run('імпортувати складник\nрезультат = складник.сума(2, 3)\n')

    assert installed.exists()
    assert interpreter.global_env["результат"] == 5