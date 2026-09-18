import json

from ukrcode.runtime import Interpreter


def test_variables_conditions_and_loops(capsys):
    Interpreter().run("""
імʼя: текст = "Ярема"
сума = 0
для число у [1, 2, 3]:
    сума += число
якщо сума == 6:
    написати(імʼя)
""")
    assert capsys.readouterr().out.strip() == "Ярема"


def test_functions_and_collections():
    interpreter = Interpreter()
    interpreter.run("""
функція додати(а, б = 1):
    повернути а + б
результат = додати(4)
дані = {"імʼя": "UkrCode", "значення": результат}
""")
    assert interpreter.global_env["результат"] == 5
    assert interpreter.global_env["дані"]["значення"] == 5


def test_indexing_slices_and_indexed_updates():
    interpreter = Interpreter()
    interpreter.run("""
слова = ["нуль", "один", "два", "три"]
слова[1] = "ОДИН"
слова[2] += "!"
частина = слова[1:3]
словник = {"імʼя": "UkrCode"}
назва = словник["імʼя"]
""")
    assert interpreter.global_env["слова"] == ["нуль", "ОДИН", "два!", "три"]
    assert interpreter.global_env["частина"] == ["ОДИН", "два!"]
    assert interpreter.global_env["назва"] == "UkrCode"


def test_classes_constructors_methods_and_inheritance():
    interpreter = Interpreter()
    interpreter.run("""
клас Користувач:
    функція ініціалізувати(цей, імʼя):
        цей.імʼя = імʼя
    функція привітатися(цей):
        повернути "Привіт, " + цей.імʼя

клас Адмін(Користувач):
    функція права(цей):
        повернути "повний доступ"

адмін = Адмін("Оля")
привітання = адмін.привітатися()
доступ = адмін.права()
""")
    assert interpreter.global_env["привітання"] == "Привіт, Оля"
    assert interpreter.global_env["доступ"] == "повний доступ"


def test_general_builtins():
    interpreter = Interpreter()
    interpreter.run("""
числа = діапазон(1, 4)
кількість = довжина(числа)
опис = тип(числа)
рядок = текст(42)
""")
    assert interpreter.global_env["числа"] == [1, 2, 3]
    assert interpreter.global_env["кількість"] == 3
    assert interpreter.global_env["опис"] == "list"
    assert interpreter.global_env["рядок"] == "42"


def test_standard_library_modules(tmp_path):
    interpreter = Interpreter()
    database_path = tmp_path / "data.sqlite"
    interpreter.run(f"""
імпортувати БазаДаних
імпортувати Текст
імпортувати JSON
бд = БазаДаних.підключити("{database_path}")
бд.створити_таблицю("люди", {{"імʼя": "текст", "вік": "число"}})
бд.додати("люди", {{"імʼя": "Ярема", "вік": 12}})
результат = бд.знайти_одного("люди", де = {{"імʼя": "Ярема"}})
довжина = Текст.довжина(Текст.верхній_регістр("ukrcode"))
дані = JSON.розібрати(JSON.створити({{"довжина": довжина}}))
""")
    assert interpreter.global_env["результат"]["вік"] == 12
    assert interpreter.global_env["дані"]["довжина"] == 7


def test_telegram_handlers_are_registered(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run("""
імпортувати Telegram
бот = Telegram.Бот(середовище("BOT_TOKEN"))
коли бот.команда("/start"):
    написати("старт")
коли бот.отримав_повідомлення():
    написати("повідомлення")
""")
    assert len(interpreter.global_env["бот"].handlers) == 2


def test_telegram_command_handler_matches_text(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run('імпортувати Telegram\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\nколи бот.команда("/start"):\n    написати("старт")\n')
    bot = interpreter.global_env["бот"]
    assert bot._matches(bot.handlers[0][0], bot._message({"message": {"text": "/start", "chat": {"id": 1}}}))


def test_telegram_message_handler_replies(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run("""
імпортувати Telegram
бот = Telegram.Бот(середовище("BOT_TOKEN"))
коли бот.отримав_повідомлення():
    якщо повідомлення.текст == "привіт":
        повідомлення.відповісти("Вітаю!")
""")
    requests = []
    bot = interpreter.global_env["бот"]
    monkeypatch.setattr(bot, "_api", lambda method, data: requests.append((method, data)) or [])
    bot.обробити({"update_id": 1, "message": {"text": "привіт", "chat": {"id": 42}, "from": {"id": 7}}})
    assert requests == [("sendMessage", {"chat_id": 42, "text": "Вітаю!"})]


def test_telegram_reply_keyboard(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run('імпортувати Telegram\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\n')
    bot = interpreter.global_env["бот"]
    requests = []
    monkeypatch.setattr(bot, "_api", lambda method, data: requests.append((method, data)) or [])
    bot.відправити("Меню", 42, [["Допомога", "Профіль"]])
    assert requests[0][0] == "sendMessage"
    assert json.loads(requests[0][1]["reply_markup"])["keyboard"] == [["Допомога", "Профіль"]]


def test_telegram_inline_keyboard_and_callback(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run('імпортувати Telegram\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\nколи бот.натиснули_кнопку("help"):\n    написати("допомога")\n')
    bot = interpreter.global_env["бот"]
    requests = []
    monkeypatch.setattr(bot, "_api", lambda method, data: requests.append((method, data)) or [])
    bot.відправити("Меню", 42, inline_кнопки=[[{"текст": "Допомога", "дані": "help"}]])
    markup = json.loads(requests[0][1]["reply_markup"])
    assert markup["inline_keyboard"][0][0] == {"text": "Допомога", "callback_data": "help"}
    bot.обробити({"update_id": 1, "callback_query": {"id": "cb-1", "data": "help", "message": {"chat": {"id": 42}}}})
    assert requests[-1] == ("answerCallbackQuery", {"callback_query_id": "cb-1"})


def test_telegram_media_and_message_operations(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    interpreter = Interpreter()
    interpreter.run('імпортувати Telegram\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\n')
    bot = interpreter.global_env["бот"]
    requests = []
    monkeypatch.setattr(bot, "_api", lambda method, data: requests.append((method, data)) or [])
    bot.надіслати_фото("image-id", "Фото", 42)
    bot.надіслати_документ("document-id", "Документ", 42)
    bot.редагувати_повідомлення(7, "Оновлено", 42)
    bot.видалити_повідомлення(7, 42)
    assert [method for method, _ in requests] == ["sendPhoto", "sendDocument", "editMessageText", "deleteMessage"]


def test_discord_webhook_sends_json(monkeypatch):
    interpreter = Interpreter()
    interpreter.run('імпортувати Discord\nбот = Discord.Бот("https://discord.test/webhook")\n')
    bot = interpreter.global_env["бот"]
    sent = []
    monkeypatch.setattr(bot, "надіслати", lambda text: sent.append(text) or 204)
    assert bot.відповісти("готово") == 204
    assert sent == ["готово"]


def test_dotenv_is_loaded_from_project(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text('BOT_TOKEN="test-from-file"\n', encoding="utf-8")
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    interpreter = Interpreter()
    assert interpreter.global_env["середовище"]("BOT_TOKEN") == "test-from-file"


def test_bot_sessions_admins_and_orders(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("ADMIN_IDS", "42, 99")
    interpreter = Interpreter()
    interpreter.run('імпортувати Telegram\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\n')
    bot = interpreter.global_env["бот"]
    session = bot.сесія(42)
    session.встановити("кошик", ["lua"])
    order = bot.створити_замовлення(42, "Lua-скрипт", 250)
    assert bot.є_адмін(42)
    assert not bot.є_адмін(7)
    assert session.отримати("кошик") == ["lua"]
    assert bot.отримати_замовлення(42) == [order]