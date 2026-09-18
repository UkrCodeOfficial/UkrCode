import math
import operator
import os
import json
import urllib.request
import urllib.parse
import time
from dataclasses import dataclass

from .errors import UkrCodeError
from .lexer import Lexer
from .parser import Attribute, Binary, Call, DictExpr, ListExpr, Literal, Name, Statement, Unary
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


class Module:
    def __init__(self, **values): self.__dict__.update(values)


@dataclass
class EventSpec:
    bot: object
    kind: str
    value: object


class TelegramBot:
    def __init__(self, token, interpreter):
        if not token:
            raise UkrCodeError("токен Telegram порожній; задайте BOT_TOKEN у середовищі")
        self.token = token
        self.interpreter = interpreter
        self.handlers = []
        self.current_message = None
        self.offset = 0
        self.api_url = f"https://api.telegram.org/bot{token}/"

    def команда(self, command):
        return EventSpec(self, "command", command)

    def отримав_повідомлення(self, message=None):
        return EventSpec(self, "message", message)

    def register(self, event, body, environment):
        self.handlers.append((event, body, environment))

    def _api(self, method, data=None):
        payload = urllib.parse.urlencode(data or {}).encode("utf-8")
        request = urllib.request.Request(self.api_url + method, data=payload)
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            raise UkrCodeError(f"Telegram API: {result.get('description', 'невідома помилка')}")
        return result["result"]

    def відправити(self, text, chat_id=None):
        chat_id = chat_id or (self.current_message.chat_id if self.current_message else None)
        if chat_id is None:
            raise UkrCodeError("немає активного чату для відповіді")
        return self._api("sendMessage", {"chat_id": chat_id, "text": text})

    def відповісти(self, text):
        return self.відправити(text)

    def _matches(self, event, message):
        if event.kind == "message": return True
        return (message.text or "").split(" ", 1)[0] == event.value

    def _message(self, update):
        raw = update.get("message", {})
        chat_id = raw.get("chat", {}).get("id")
        return Module(**{
            "текст": raw.get("text", ""),
            "chat_id": chat_id,
            "користувач": Module(**raw.get("from", {})),
            "відповісти": lambda text: self.відправити(text, chat_id),
        })

    def обробити(self, update):
        message = self._message(update)
        self.current_message = message
        for event, body, environment in self.handlers:
            if self._matches(event, message):
                child = Environment(environment)
                child["повідомлення"] = message
                self.interpreter.execute(body, child)
        self.current_message = None

    def запустити(self):
        print("Telegram-бот запущений (polling)")
        while True:
            updates = self._api("getUpdates", {"timeout": 30, "offset": self.offset})
            for update in updates:
                self.offset = update["update_id"] + 1
                self.обробити(update)
            time.sleep(0.2)


class Environment(dict):
    def __init__(self, parent=None):
        super().__init__(); self.parent = parent

    def resolve(self, name):
        if name in self: return self
        if self.parent: return self.parent.resolve(name)
        raise UkrCodeError(f'невідома змінна "{name}"')

    def get_value(self, name): return self.resolve(name)[name]


def stdlib(interpreter):
    def write(*values): print(*values)
    def env(name): return os.environ.get(name, "")
    math_module = Module(**{"округлити": round, "абс": abs, "мін": min, "макс": max, "корінь": math.sqrt, "пі": math.pi})
    json_module = Module(**{"розібрати": json.loads, "створити": lambda value: json.dumps(value, ensure_ascii=False)})
    files = Module(**{"прочитати": lambda path: open(path, encoding="utf-8").read(), "записати": lambda path, text: open(path, "w", encoding="utf-8").write(text), "існує": os.path.exists, "видалити": os.remove})
    def http_get(url):
        with urllib.request.urlopen(url) as response:
            return Module(статус=response.status, текст=response.read().decode("utf-8"))
    http = Module(**{"отримати": http_get})
    telegram = Module(Бот=lambda token: TelegramBot(token, interpreter))
    return {"написати": write, "середовище": env, "Математика": math_module, "JSON": json_module, "Файли": files, "HTTP": http, "Telegram": telegram}


class Interpreter:
    def __init__(self):
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
        elif kind == "setattr": setattr(self.evaluate(data[0].object, env), data[0].name, self.evaluate(data[1], env))
        elif kind == "update":
            target, operator_name, value = data
            if isinstance(target, Name):
                scope = env.resolve(target.value); current = scope[target.value]
                scope[target.value] = self.apply_binary(current, operator_name[0], self.evaluate(value, env))
            else: raise UkrCodeError("оновлювати можна лише змінну")
        elif kind == "expr": self.evaluate(data[0], env)
        elif kind == "import":
            name, alias = data; env[alias or name] = self.global_env.get(name, Module())
        elif kind == "function": env[data[0]] = UserFunction(data[0], data[1], data[2], env)
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
        if isinstance(expression, Attribute): return getattr(self.evaluate(expression.object, env), expression.name)
        if isinstance(expression, Unary):
            value = self.evaluate(expression.expression, env); return not value if expression.op == "не" else (-value if expression.op == "-" else value)
        if isinstance(expression, Binary): return self.apply_binary(self.evaluate(expression.left, env), expression.op, self.evaluate(expression.right, env))
        if isinstance(expression, Call):
            function = self.evaluate(expression.function, env); args = [self.evaluate(arg, env) for arg in expression.args]; kwargs = {k: self.evaluate(v, env) for k, v in expression.kwargs.items()}
            if isinstance(function, UserFunction):
                child = Environment(function.closure)
                for index, (name, default) in enumerate(function.params): child[name] = args[index] if index < len(args) else self.evaluate(default, env) if default else None
                try: self.execute(function.body, child)
                except ReturnSignal as signal: return signal.value
                return None
            return function(*args, **kwargs)
        raise UkrCodeError("невідомий вираз")

    def apply_binary(self, left, op, right):
        if op == "і": return left and right
        if op == "або": return left or right
        operations = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv, "//": operator.floordiv, "%": operator.mod, "**": operator.pow, "==": operator.eq, "!=": operator.ne, ">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
        try: return operations[op](left, right)
        except KeyError as error: raise UkrCodeError(f"невідомий оператор {op}") from error