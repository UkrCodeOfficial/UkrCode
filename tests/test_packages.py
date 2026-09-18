from ukrcode.packages import PackageManager


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