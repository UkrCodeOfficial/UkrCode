import math
import operator
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time
import datetime
import logging
import os
import random
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path
from dataclasses import dataclass

from .errors import UkrCodeError
from .lexer import Lexer
from .parser import Attribute, Binary, Call, DictExpr, Index, ListExpr, Literal, Name, Statement, Unary, UserClass
from .parser import Parser


class ReturnSignal(Exception):
    def __init__(self, value): self.value = value


class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass


@dataclass
class UserFunction:
    name: str
    params: list
    body: list
    closure: dict


class UserObject:
    def __init__(self, class_definition):
        self.class_definition = class_definition
        self.fields = {}


class BoundMethod:
    def __init__(self, function, instance, interpreter):
        self.function = function
        self.instance = instance
        self.interpreter = interpreter

    def __call__(self, *args, **kwargs):
        return self.interpreter.call_user_function(self.function, [self.instance, *args], kwargs, self.interpreter.global_env)


class Module:
    def __init__(self, **values): self.__dict__.update(values)


@dataclass
class EventSpec:
    bot: object
    kind: str
    value: object


class BotSession:
    def __init__(self, data):
        self.data = data

    def отримати(self, key, default=None):
        return self.data.get(key, default)

    def встановити(self, key, value):
        self.data[key] = value
        return value

    def видалити(self, key):
        return self.data.pop(key, None)

    def очистити(self):
        self.data.clear()


class TelegramBot:
    def __init__(self, token, interpreter):
        if not token:
            raise UkrCodeError("токен Telegram порожній; задайте BOT_TOKEN у середовищі")
        self.token = token
        self.interpreter = interpreter
        self.handlers = []
        self.current_message = None
        self.current_callback_id = None
        self.offset = 0
        self.sessions = {}
        self.orders = []
        self.next_order_id = 1
        self.admin_ids = {item.strip() for item in os.environ.get("ADMIN_IDS", "").split(",") if item.strip()}
        self.api_url = f"https://api.telegram.org/bot{token}/"

    def команда(self, command):
        return EventSpec(self, "command", command)

    def отримав_повідомлення(self, message=None):
        return EventSpec(self, "message", message)

    def отримав_текст(self, text):
        return EventSpec(self, "text", text)

    def натиснули_кнопку(self, data=None):
        return EventSpec(self, "callback", data)

    def сесія(self, user_id):
        key = str(user_id)
        return BotSession(self.sessions.setdefault(key, {}))

    def є_адмін(self, user_id):
        return str(user_id) in self.admin_ids

    def створити_замовлення(self, user_id, послуга, ціна):
        order = {"ід": self.next_order_id, "користувач": user_id, "послуга": послуга, "ціна": ціна, "статус": "нове"}
        self.orders.append(order)
        self.next_order_id += 1
        return order

    def отримати_замовлення(self, user_id=None):
        if user_id is None: return self.orders
        return [order for order in self.orders if order["користувач"] == user_id]

    def register(self, event, body, environment):
        self.handlers.append((event, body, environment))

    def _api(self, method, data=None):
        payload = urllib.parse.urlencode(data or {}).encode("utf-8")
        request = urllib.request.Request(self.api_url + method, data=payload)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code in {401, 404}:
                raise UkrCodeError("Telegram не прийняв токен. Перевірте BOT_TOKEN або створіть новий токен у BotFather") from error
            raise UkrCodeError(f"Telegram HTTP помилка {error.code}") from error
        except urllib.error.URLError as error:
            raise UkrCodeError(f"не вдалося підключитися до Telegram: {error.reason}") from error
        if not result.get("ok"):
            raise UkrCodeError(f"Telegram API: {result.get('description', 'невідома помилка')}")
        return result["result"]

    def відправити(self, text, chat_id=None, кнопки=None, inline_кнопки=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        if chat_id is None:
            raise UkrCodeError("немає активного чату для відповіді")
        data = {"chat_id": chat_id, "text": text}
        if кнопки:
            data["reply_markup"] = json.dumps({
                "keyboard": кнопки,
                "resize_keyboard": True,
                "one_time_keyboard": False,
            }, ensure_ascii=False)
        if inline_кнопки:
            data["reply_markup"] = json.dumps({
                "inline_keyboard": [
                    [{"text": button.get("текст", button.get("text", "")), "callback_data": button.get("дані", button.get("callback_data", ""))} for button in row]
                    for row in inline_кнопки
                ]
            }, ensure_ascii=False)
        return self._api("sendMessage", data)

    def відповісти(self, text, кнопки=None, inline_кнопки=None):
        return self.відправити(text, кнопки=кнопки, inline_кнопки=inline_кнопки)

    def надіслати_фото(self, фото, підпис=None, chat_id=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        if chat_id is None: raise UkrCodeError("немає активного чату для фото")
        data = {"chat_id": chat_id, "photo": фото}
        if підпис: data["caption"] = підпис
        return self._api("sendPhoto", data)

    def надіслати_документ(self, документ, підпис=None, chat_id=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        if chat_id is None: raise UkrCodeError("немає активного чату для документа")
        data = {"chat_id": chat_id, "document": документ}
        if підпис: data["caption"] = підпис
        return self._api("sendDocument", data)

    def редагувати_повідомлення(self, message_id, text, chat_id=None, inline_кнопки=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if inline_кнопки:
            data["reply_markup"] = json.dumps({"inline_keyboard": [[
                {"text": button.get("текст", button.get("text", "")), "callback_data": button.get("дані", button.get("callback_data", ""))}
                for button in row
            ] for row in inline_кнопки]}, ensure_ascii=False)
        return self._api("editMessageText", data)

    def видалити_повідомлення(self, message_id, chat_id=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        return self._api("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def _matches(self, event, message):
        if event.kind == "message": return not message.callback_data and (event.value is None or message.текст == event.value)
        if event.kind == "text": return not message.callback_data and message.текст == event.value
        if event.kind == "callback": return message.callback_data == event.value if event.value else bool(message.callback_data)
        return (message.текст or "").split(" ", 1)[0] == event.value

    def _message(self, update):
        callback = update.get("callback_query", {})
        raw = callback.get("message", {}) if callback else update.get("message", {})
        chat_id = raw.get("chat", {}).get("id")
        return Module(**{
            "текст": raw.get("text", ""),
            "ід": raw.get("message_id"),
            "callback_data": callback.get("data", "") if callback else "",
            "chat_id": chat_id,
            "користувач": Module(**(callback.get("from", {}) if callback else raw.get("from", {}))),
            "відповісти": lambda text, кнопки=None, inline_кнопки=None: self.відправити(text, chat_id, кнопки, inline_кнопки),
            "фото": lambda фото, підпис=None: self.надіслати_фото(фото, підпис, chat_id),
            "документ": lambda документ, підпис=None: self.надіслати_документ(документ, підпис, chat_id),
            "редагувати": lambda text, inline_кнопки=None: self.редагувати_повідомлення(raw.get("message_id"), text, chat_id, inline_кнопки),
            "видалити": lambda: self.видалити_повідомлення(raw.get("message_id"), chat_id),
        })

    def обробити(self, update):
        message = self._message(update)
        self.current_callback_id = update.get("callback_query", {}).get("id")
        self.current_message = message
        for event, body, environment in self.handlers:
            if self._matches(event, message):
                child = Environment(environment)
                child["повідомлення"] = message
                self.interpreter.execute(body, child)
        if self.current_callback_id:
            self._api("answerCallbackQuery", {"callback_query_id": self.current_callback_id})
        self.current_message = None
        self.current_callback_id = None

    def запустити(self):
        print("Telegram-бот запущений (polling)")
        while True:
            updates = self._api("getUpdates", {"timeout": 30, "offset": self.offset})
            for update in updates:
                self.offset = update["update_id"] + 1
                self.обробити(update)
            time.sleep(0.2)


class DiscordBot:
    def __init__(self, webhook_url):
        if not webhook_url:
            raise UkrCodeError("URL Discord webhook порожній; задайте DISCORD_WEBHOOK_URL")
        self.webhook_url = webhook_url

    def надіслати(self, text):
        payload = json.dumps({"content": text}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(self.webhook_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            return response.status

    def відповісти(self, text):
        return self.надіслати(text)


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row

    def виконати(self, query, параметри=None):
        cursor = self.connection.execute(query, параметри or {})
        self.connection.commit()
        return [dict(row) for row in cursor.fetchall()]

    def додати(self, table, values):
        columns = ", ".join(values)
        placeholders = ", ".join(f":{column}" for column in values)
        cursor = self.connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
        self.connection.commit()
        return cursor.lastrowid

    def знайти_одного(self, table, де=None):
        conditions = " AND ".join(f"{key} = :{key}" for key in (де or {})) or "1 = 1"
        row = self.connection.execute(f"SELECT * FROM {table} WHERE {conditions} LIMIT 1", де or {}).fetchone()
        return dict(row) if row else None

    def створити_таблицю(self, table, columns):
        definition = ", ".join(f"{name} {self._sql_type(value)}" for name, value in columns.items())
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {table} ({definition})")
        self.connection.commit()

    @staticmethod
    def _sql_type(value):
        names = {"текст": "TEXT", "число": "INTEGER", "дробове": "REAL", "логічне": "INTEGER"}
        return names.get(value, value if isinstance(value, str) else "TEXT")

    def закрити(self):
        self.connection.close()


class Environment(dict):
    def __init__(self, parent=None):
        super().__init__(); self.parent = parent

    def resolve(self, name):
        if name in self: return self
        if self.parent: return self.parent.resolve(name)
        raise UkrCodeError(f'невідома змінна "{name}"')

    def get_value(self, name): return self.resolve(name)[name]


def load_dotenv(path=None):
    dotenv_path = Path(path or ".env")
    if not dotenv_path.exists():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name:
            os.environ.setdefault(name, value)


def stdlib(interpreter):
    def write(*values): print(*values)
    def env(name): return os.environ.get(name, "")
    text = Module(**{
        "довжина": len,
        "верхній_регістр": lambda value: value.upper(),
        "нижній_регістр": lambda value: value.lower(),
        "обрізати": lambda value: value.strip(),
        "містить": lambda value, part: part in value,
        "замінити": lambda value, old, new: value.replace(old, new),
        "розділити": lambda value, separator: value.split(separator),
        "об'єднати": lambda values, separator: separator.join(values),
    })
    lists = Module(**{
        "довжина": len,
        "додати": lambda values, value: values.append(value) or values,
        "видалити": lambda values, value: values.remove(value) or values,
        "відсортувати": lambda values: sorted(values),
        "містить": lambda values, value: value in values,
    })
    math_module = Module(**{"округлити": round, "абс": abs, "мін": min, "макс": max, "корінь": math.sqrt, "пі": math.pi})
    json_module = Module(**{"розібрати": json.loads, "створити": lambda value: json.dumps(value, ensure_ascii=False)})
    files = Module(**{
        "прочитати": lambda path: open(path, encoding="utf-8").read(),
        "записати": lambda path, text: open(path, "w", encoding="utf-8").write(text),
        "існує": os.path.exists,
        "видалити": os.remove,
        "створити_директорію": lambda path: os.makedirs(path, exist_ok=True),
        "скопіювати": shutil.copy2,
        "перемістити": shutil.move,
        "розмір": os.path.getsize,
    })
    operating_system = Module(**{
        "ім'я": os.name,
        "поточна_директорія": os.getcwd,
        "змінні": lambda: dict(os.environ),
        "встановлено": lambda name: shutil.which(name) is not None,
    })
    date_module = Module(**{
        "зараз": lambda: datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
        "сьогодні": lambda: datetime.date.today().isoformat(),
        "часова_мітка": time.time,
    })
    time_module = Module(**{"затримка": time.sleep, "зараз": time.time})
    random_module = Module(**{"число": random.random, "ціле": random.randint, "вибрати": random.choice, "перемішати": random.shuffle})
    regex = Module(**{"знайти": lambda pattern, value: re.findall(pattern, value), "заміна": lambda pattern, replacement, value: re.sub(pattern, replacement, value), "збігається": lambda pattern, value: re.search(pattern, value) is not None})
    terminal = Module(**{"очистити": lambda: print("\033[2J\033[H", end=""), "прочитати": input, "колір": lambda value, color: f"\033[{color}m{value}\033[0m"})
    processes = Module(**{"запустити": lambda command: subprocess.run(command, shell=True, check=True, capture_output=True, text=True).stdout})
    logs = Module(**{"отримати": lambda name: logging.getLogger(name), "налаштувати": lambda: logging.basicConfig(level=logging.INFO)})
    def http_get(url):
        with urllib.request.urlopen(url) as response:
            return Module(статус=response.status, текст=response.read().decode("utf-8"))
    def http_post(url, дані):
        payload = json.dumps(дані, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            return Module(статус=response.status, текст=response.read().decode("utf-8"))
    http = Module(**{"отримати": http_get, "пост": http_post})
    telegram = Module(Бот=lambda token: TelegramBot(token, interpreter))
    discord = Module(Бот=DiscordBot)
    database = Module(**{"підключити": Database})
    builtins = {
        "написати": write, "введення": input,
        "діапазон": lambda *values: list(range(*values)),
        "довжина": len, "тип": lambda value: type(value).__name__,
        "текст": str, "ціле": int, "дробове": float,
    }
    return {
        **builtins, "середовище": env, "Математика": math_module,
        "Текст": text, "Списки": lists, "JSON": json_module, "Файли": files,
        "ОС": operating_system, "Дата": date_module, "Час": time_module,
        "Випадковість": random_module, "РегулярніВирази": regex,
        "Термінал": terminal, "Процеси": processes, "Логування": logs,
        "HTTP": http, "БазаДаних": database, "Telegram": telegram, "Discord": discord,
    }


class Interpreter:
    def __init__(self):
        load_dotenv()
        self.global_env = Environment()
        self.global_env.update(stdlib(self))

    def run(self, source):
        program = Parser(Lexer().tokenize(source)).parse()
        self.execute(program, self.global_env)
        return self.global_env

    def execute(self, statements, environment):
        for statement in statements: self.execute_statement(statement, environment)

    def execute_statement(self, statement, env):
        kind, data = statement.kind, statement.data
        if kind == "assign": env[data[0]] = self.evaluate(data[1], env)
        elif kind == "setattr":
            target = self.evaluate(data[0].object, env)
            value = self.evaluate(data[1], env)
            if isinstance(target, UserObject): target.fields[data[0].name] = value
            else: setattr(target, data[0].name, value)
        elif kind == "setitem":
            target = self.evaluate(data[0].object, env)
            target[self.evaluate(data[0].start, env)] = self.evaluate(data[1], env)
        elif kind == "update":
            target, operator_name, value = data
            if isinstance(target, Name):
                scope = env.resolve(target.value); current = scope[target.value]
                scope[target.value] = self.apply_binary(current, operator_name[0], self.evaluate(value, env))
            elif isinstance(target, Index):
                collection = self.evaluate(target.object, env)
                index = self.evaluate(target.start, env)
                collection[index] = self.apply_binary(collection[index], operator_name[0], self.evaluate(value, env))
            else: raise UkrCodeError("оновлювати можна лише змінну")
        elif kind == "expr": self.evaluate(data[0], env)
        elif kind == "import":
            name, alias = data; env[alias or name] = self.global_env.get(name, Module())
        elif kind == "function": env[data[0]] = UserFunction(data[0], data[1], data[2], env)
        elif kind == "class":
            parent = env.get_value(data[1]) if data[1] else None
            env[data[0]] = UserClass(data[0], parent, data[2])
        elif kind == "return": raise ReturnSignal(self.evaluate(data[0], env) if data[0] else None)
        elif kind == "підняти": raise UkrCodeError(str(self.evaluate(data[0], env)))
        elif kind == "перервати": raise BreakSignal()
        elif kind == "продовжити": raise ContinueSignal()
        elif kind == "if":
            for condition, body in data[0]:
                if condition is None or self.evaluate(condition, env): self.execute(body, Environment(env)); break
        elif kind == "while":
            while self.evaluate(data[0], env):
                try: self.execute(data[1], Environment(env))
                except BreakSignal: break
                except ContinueSignal: continue
        elif kind == "for":
            for item in self.evaluate(data[1], env):
                child = Environment(env); child[data[0]] = item
                try: self.execute(data[2], child)
                except BreakSignal: break
                except ContinueSignal: continue
        elif kind == "repeat":
            for _ in range(int(self.evaluate(data[0], env))):
                try: self.execute(data[1], Environment(env))
                except BreakSignal: break
                except ContinueSignal: continue
        elif kind == "try":
            try: self.execute(data[0], env)
            except UkrCodeError: self.execute(data[1], env)
            finally: self.execute(data[2], env)
        elif kind == "when":
            event = self.evaluate(data[0], env)
            if isinstance(event, EventSpec): event.bot.register(event, data[1], env)

    def evaluate(self, expression, env):
        if isinstance(expression, Literal): return expression.value
        if isinstance(expression, Name): return env.get_value(expression.value)
        if isinstance(expression, ListExpr): return [self.evaluate(item, env) for item in expression.items]
        if isinstance(expression, DictExpr): return {self.evaluate(k, env): self.evaluate(v, env) for k, v in expression.items}
        if isinstance(expression, Attribute):
            instance = self.evaluate(expression.object, env)
            if isinstance(instance, UserObject):
                if expression.name in instance.fields: return instance.fields[expression.name]
                method = self.find_method(instance.class_definition, expression.name)
                if method: return BoundMethod(method, instance, self)
                raise UkrCodeError(f'обʼєкт не має властивості "{expression.name}"')
            return getattr(instance, expression.name)
        if isinstance(expression, Index):
            collection = self.evaluate(expression.object, env)
            start = self.evaluate(expression.start, env) if expression.start is not None else None
            if expression.stop is None and expression.step is None:
                return collection[start]
            stop = self.evaluate(expression.stop, env) if expression.stop is not None else None
            step = self.evaluate(expression.step, env) if expression.step is not None else None
            return collection[slice(start, stop, step)]
        if isinstance(expression, Unary):
            value = self.evaluate(expression.expression, env); return not value if expression.op == "не" else (-value if expression.op == "-" else value)
        if isinstance(expression, Binary): return self.apply_binary(self.evaluate(expression.left, env), expression.op, self.evaluate(expression.right, env))
        if isinstance(expression, Call):
            function = self.evaluate(expression.function, env); args = [self.evaluate(arg, env) for arg in expression.args]; kwargs = {k: self.evaluate(v, env) for k, v in expression.kwargs.items()}
            if isinstance(function, UserClass):
                instance = UserObject(function)
                initializer = self.find_method(function, "ініціалізувати")
                if initializer: self.call_user_function(initializer, [instance, *args], kwargs, env)
                return instance
            if isinstance(function, UserFunction):
                return self.call_user_function(function, args, kwargs, env)
            return function(*args, **kwargs)
        raise UkrCodeError("невідомий вираз")

    def find_method(self, class_definition, name):
        current = class_definition
        while current:
            for statement in current.body:
                if statement.kind == "function" and statement.data[0] == name:
                    return UserFunction(statement.data[0], statement.data[1], statement.data[2], {"__class__": current})
            current = current.parent if isinstance(current.parent, UserClass) else None
        return None

    def call_user_function(self, function, args, kwargs, env):
        child = Environment(function.closure)
        for index, (name, default) in enumerate(function.params):
            child[name] = kwargs.get(name, args[index] if index < len(args) else self.evaluate(default, env) if default else None)
        try: self.execute(function.body, child)
        except ReturnSignal as signal: return signal.value
        return None

    def apply_binary(self, left, op, right):
        if op == "і": return left and right
        if op == "або": return left or right
        operations = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv, "//": operator.floordiv, "%": operator.mod, "**": operator.pow, "==": operator.eq, "!=": operator.ne, ">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
        try: return operations[op](left, right)
        except KeyError as error: raise UkrCodeError(f"невідомий оператор {op}") from error