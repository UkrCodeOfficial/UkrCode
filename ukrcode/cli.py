import argparse
import pathlib
import sys

from . import __version__
from .lexer import Lexer
from .runtime import Interpreter
from .packages import PackageManager


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].endswith(".ucod"):
        argv = ["run", *argv]
    parser = argparse.ArgumentParser(prog="ucod", description="Інтерпретатор UkrCode")
    parser.add_argument("--version", action="version", version=f"UkrCode {__version__}")
    parser.add_argument("command", nargs="?", default="version", choices=["run", "check", "format", "test", "repl", "version", "новий", "встановити", "видалити", "оновити", "список"])
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "version": print(f"UkrCode {__version__}"); return 0
    manager = PackageManager()
    if args.command == "новий":
        print(f"Створено проєкт: {manager.create(args.file)}"); return 0
    if args.command == "встановити":
        print(f"Встановлено: {manager.install(args.file)}"); return 0
    if args.command == "видалити":
        manager.remove(args.file); print(f"Видалено: {args.file}"); return 0
    if args.command == "оновити":
        manager.update(); print("Пакети оновлено"); return 0
    if args.command == "список":
        for package in manager.list(): print(package)
        return 0
    if args.command == "check":
        source = pathlib.Path(args.file).read_text(encoding="utf-8"); Lexer().tokenize(source); print("Синтаксис правильний"); return 0
    if args.command == "format":
        path = pathlib.Path(args.file)
        path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
        print(f"Відформатовано: {path}"); return 0
    if args.command == "test":
        import subprocess
        return subprocess.call([sys.executable, "-m", "pytest", "-q"])
    if args.command == "run":
        Interpreter().run(pathlib.Path(args.file).read_text(encoding="utf-8")); return 0
    print(f"UkrCode {__version__}\nВведіть 'вийти' для завершення.")
    interpreter = Interpreter()
    while True:
        try: source = input(">>> ")
        except EOFError: break
        if source.strip() == "вийти": break
        try: interpreter.run(source + "\n")
        except Exception as error: print(error)
    return 0