# UkrCode

UkrCode is an interpreter-first Ukrainian programming language for readable
automation, CLI tools and bot integrations. Source files use `.ucod`.

## Quick start

Швидке встановлення всього UkrCode на Linux або macOS однією командою:

```bash
curl -fsSL https://raw.githubusercontent.com/UkrCodeOfficial/UkrCode/main/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/.ukrcode"
ucod run examples/hello.ucod
```

Ця команда завантажує весь репозиторій, створює ізольоване Python-середовище,
встановлює CLI `ucod`, копіює `.env.example` у `.env` та автоматично збирає й
встановлює VS Code extension, якщо в системі є `npm` і `code`.

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

Інсталятор завантажує весь репозиторій у `~/.ukrcode`, створює Python
середовище, встановлює `ucod` і, якщо доступний `code`, встановлює VS Code
extension. Файл `~/.ukrcode/.env` створюється з `.env.example`; вставте токен
лише туди.

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

Для звичайної логіки проєкту UkrCode підтримує класи, конструктори, методи,
обʼєкти, наслідування та вбудовані `діапазон`, `довжина`, `тип`, `текст`,
`ціле`, `дробове`, `введення`.

Для Discord automation доступний webhook:

```bash
DISCORD_WEBHOOK_URL="ваш_url" ucod run examples/discord-webhook.ucod
```

Webhook надсилає повідомлення, але ще не є повним Discord Gateway-ботом із
slash commands та voice events.

## Пакети та проєкти

```bash
ucod новий мійбот
cd мійбот
ucod встановити ../спільна-бібліотека
ucod список
ucod оновити
ucod видалити спільна-бібліотека
```

Локальні залежності зберігаються в `.ucod/packages`, а їхній lock-файл — у
`ucod.lock`. Registry-сервер і semantic version resolution залишаються окремим
наступним етапом.

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
cp .env.example .env
# Відкрийте .env і вставте BOT_TOKEN
ucod run examples/telegram-bot.ucod
```

The complete example is in [examples/telegram-bot.ucod](examples/telegram-bot.ucod).
UkrCode автоматично завантажує локальний `.env`; цей файл не потрібно передавати
в терміналі й він ігнорується Git.

Великий приклад магазину Roblox Studio з каталогом, замовленнями, сесіями
користувачів та адмін-панеллю: [examples/roblox-service-shop.ucod](examples/roblox-service-shop.ucod).

Для повної довідки, яку можна передавати ШІ для генерації UkrCode, дивіться
[docs/AI_LANGUAGE_SPEC.md](docs/AI_LANGUAGE_SPEC.md). Ця специфікація оновлюється
разом із мовою.

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
