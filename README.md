# UkrCode

UkrCode is an interpreter-first Ukrainian programming language for readable
automation, CLI tools and bot integrations. Source files use `.ucod`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
ucod run examples/hello.ucod
ucod check examples/hello.ucod
ucod --help
```

## Завантаження для друга

```bash
git clone https://github.com/UkrCodeOfficial/UkrCode.git
cd UkrCode
python -m pip install -e .
ucod run examples/hello.ucod
```

Щоб встановити підтримку `.ucod` у VS Code:

```bash
cd vscode-extension
npm install
npm run package
code --install-extension ukrcode-language-support-0.1.0.vsix
```

Після цього відкрийте `.ucod` файл у VS Code. Розширення додає підсвічування,
snippets та команди `UkrCode: Run File`, `UkrCode: Check File` і
`UkrCode: Format File`.

Output:

```text
Привіт, Ярема!
```

## Syntax

```ucod
імʼя: текст = "Ярема"

функція привітати(хто):
	повернути "Привіт, " + хто

для число у [1, 2, 3]:
	написати(число)
```

The MVP includes variables, optional annotations, numbers, text, booleans,
lists, dictionaries, arithmetic and comparison operators, `якщо`, `інакше`,
`для`, `поки`, `повторити`, functions, imports, `спробувати`, `помилка`,
`нарешті`, `повернути`, `перервати`, `продовжити`, JSON, files, environment
variables and a small HTTP client. It has no AI dependency and runs locally.

Available standard modules include `Математика`, `Текст`, `Списки`, `JSON`,
`Файли`, `ОС`, `Дата`, `Час`, `Випадковість`, `РегулярніВирази`, `Термінал`,
`Процеси`, `Логування`, `HTTP`, `БазаДаних` and `Telegram`.

Example SQLite usage:

```ucod
імпортувати БазаДаних

бд = БазаДаних.підключити("дані.sqlite")
бд.створити_таблицю("користувачі", {"імʼя": "текст", "вік": "число"})
бд.додати("користувачі", {"імʼя": "Ярема", "вік": 12})
користувач = бд.знайти_одного("користувачі", де = {"імʼя": "Ярема"})
написати(користувач)
```

## Telegram bot

The first Telegram adapter uses the official Bot API over HTTPS and long
polling. It requires a token in the environment and never stores that token
in source code:

```bash
BOT_TOKEN="ваш_токен" ucod run examples/telegram-bot.ucod
```

The complete example is in [examples/telegram-bot.ucod](examples/telegram-bot.ucod).

## Repository

```text
ukrcode/                 lexer, parser, AST nodes and interpreter runtime
examples/                executable .ucod programs
tests/                   runtime regression tests
vscode-extension/        language support, snippets and run/check commands
docs/                    language notes and roadmap
```

## Status

Completed: lexer, indentation parser, AST, interpreter, CLI, basic standard
library, tests, syntax highlighting, snippets and a working Telegram polling
adapter.

The project is usable for small CLI programs and Telegram bots. It is not yet
a production-complete language platform: bytecode VM, richer diagnostics,
package locking, Discord adapter, language server, debugger and native
compiler remain in the [roadmap](docs/ROADMAP.md).
