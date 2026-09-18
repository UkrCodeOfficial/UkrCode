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