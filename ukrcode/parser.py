from dataclasses import dataclass

from .errors import UkrCodeError
from .lexer import Token


@dataclass
class Literal:
    value: object


@dataclass
class Name:
    value: str


@dataclass
class ListExpr:
    items: list


@dataclass
class DictExpr:
    items: list[tuple]


@dataclass
class Unary:
    op: str
    expression: object


@dataclass
class Binary:
    left: object
    op: str
    right: object


@dataclass
class Call:
    function: object
    args: list
    kwargs: dict


@dataclass
class Attribute:
    object: object
    name: str


@dataclass
class Statement:
    kind: str
    data: tuple


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    @property
    def current(self):
        return self.tokens[self.position]

    def advance(self):
        token = self.current
        self.position += 1
        return token

    def accept(self, value):
        if self.current.value == value or self.current.kind == value:
            return self.advance()
        return None

    def expect(self, value):
        if self.current.value != value and self.current.kind != value:
            raise UkrCodeError(f"очікувалося {value!r}, отримано {self.current.value!r}", self.current.line, self.current.column)
        return self.advance()

    def name(self):
        if self.current.kind != "NAME":
            raise UkrCodeError("очікувалося ім'я", self.current.line, self.current.column)
        return self.advance().value

    def parse(self):
        statements = []
        while self.current.kind != "EOF":
            if self.current.kind == "NEWLINE":
                self.advance()
            else:
                statements.append(self.statement())
        return statements

    def statement(self):
        word = self.current.value
        if word in {"якщо", "поки", "для", "повторити", "функція", "асинхронна", "спробувати", "коли"}:
            return self.compound()
        if word == "імпортувати":
            self.advance(); module = self.name(); alias = None
            if self.accept("як"): alias = self.name()
            self.expect("\n")
            return Statement("import", (module, alias))
        if word in {"повернути", "підняти", "перервати", "продовжити"}:
            self.advance()
            expression = None if word in {"перервати", "продовжити"} else self.expression()
            self.expect("\n")
            return Statement("return" if word == "повернути" else word, (expression,))
        expression = self.expression()
        if isinstance(expression, Name) and self.accept(":"):
            self.name()
            self.expect("=")
            value = self.expression()
            self.expect("\n")
            return Statement("assign", (expression.value, value))
        if isinstance(expression, Name) and self.accept("="):
            value = self.expression()
            self.expect("\n")
            return Statement("assign", (expression.value, value))
        if isinstance(expression, Attribute) and self.accept("="):
            value = self.expression(); self.expect("\n")
            return Statement("setattr", (expression, value))
        if self.current.value in {"=", "+=", "-=", "*=", "/="}:
            operator = self.advance().value; value = self.expression(); self.expect("\n")
            return Statement("update", (expression, operator, value))
        self.expect("\n")
        return Statement("expr", (expression,))

    def block(self):
        self.expect(":"); self.expect("\n"); self.expect("INDENT")
        statements = []
        while self.current.kind not in {"DEDENT", "EOF"}:
            if self.current.kind == "NEWLINE": self.advance()
            else: statements.append(self.statement())
        self.accept("DEDENT")
        return statements

    def compound(self):
        word = self.advance().value
        if word == "асинхронна":
            self.expect("функція"); word = "функція"
        if word == "функція":
            name = self.name(); params = self.parameters(); body = self.block()
            return Statement("function", (name, params, body))
        if word == "якщо":
            branches = [(self.expression(), self.block())]
            while self.current.value == "інакше":
                self.advance()
                if self.accept("якщо"): branches.append((self.expression(), self.block()))
                else: branches.append((None, self.block())); break
            return Statement("if", (branches,))
        if word == "поки": return Statement("while", (self.expression(), self.block()))
        if word == "для":
            variable = self.name(); self.expect("у"); return Statement("for", (variable, self.expression(), self.block()))
        if word == "повторити":
            count = self.expression(); self.expect("разів"); return Statement("repeat", (count, self.block()))
        if word == "спробувати":
            body = self.block(); self.expect("помилка"); handler = self.block(); final = []
            if self.accept("нарешті"): final = self.block()
            return Statement("try", (body, handler, final))
        if word == "коли":
            event = self.expression(); return Statement("when", (event, self.block()))
        raise UkrCodeError("невідома конструкція", self.current.line, self.current.column)

    def parameters(self):
        self.expect("("); params = []
        while self.current.value != ")":
            name = self.name(); default = None
            if self.accept(":"): self.name()
            if self.accept("="): default = self.expression()
            params.append((name, default))
            if not self.accept(","): break
        self.expect(")"); return params

    def expression(self, minimum=0):
        left = self.unary()
        precedence = {"або": 1, "і": 2, "==": 3, "!=": 3, ">": 3, "<": 3, ">=": 3, "<=": 3, "+": 4, "-": 4, "*": 5, "/": 5, "//": 5, "%": 5, "**": 6}
        while self.current.value in precedence and precedence[self.current.value] >= minimum:
            op = self.advance().value; right = self.expression(precedence[op] + (0 if op == "**" else 1)); left = Binary(left, op, right)
        return left

    def unary(self):
        if self.current.value in {"не", "-", "+"}:
            return Unary(self.advance().value, self.unary())
        expression = self.primary()
        while True:
            if self.accept("."): expression = Attribute(expression, self.name())
            elif self.accept("("):
                args, kwargs = [], {}
                while self.current.value != ")":
                    if self.current.kind == "NAME" and self.tokens[self.position + 1].value == "=":
                        key = self.name(); self.expect("="); kwargs[key] = self.expression()
                    else: args.append(self.expression())
                    if not self.accept(","): break
                self.expect(")"); expression = Call(expression, args, kwargs)
            else: break
        return expression

    def primary(self):
        token = self.advance()
        if token.kind == "NUMBER" or token.kind == "STRING": return Literal(token.value)
        if token.value == "так": return Literal(True)
        if token.value == "ні": return Literal(False)
        if token.value == "нічого": return Literal(None)
        if token.kind == "NAME": return Name(token.value)
        if token.value == "(":
            expression = self.expression(); self.expect(")"); return expression
        if token.value == "[":
            items = []
            while self.current.value != "]":
                items.append(self.expression())
                if not self.accept(","): break
            self.expect("]"); return ListExpr(items)
        if token.value == "{":
            items = []
            while self.current.value != "}":
                key = self.expression(); self.expect(":"); items.append((key, self.expression()))
                if not self.accept(","): break
            self.expect("}"); return DictExpr(items)
        raise UkrCodeError(f"неочікуваний токен {token.value!r}", token.line, token.column)