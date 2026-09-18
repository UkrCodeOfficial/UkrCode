from dataclasses import dataclass
import ast
import re

from .errors import UkrCodeError


@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    line: int
    column: int


class Lexer:
    _token = re.compile(
        r"(?P<space>[ ]+)|(?P<number>\d+(?:\.\d+)?)|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')|"
        r"(?P<name>[\wА-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)|(?P<op>==|!=|>=|<=|\+=|-=|\*=|/=|//|\*\*|[+\-*/%<>=.,:()\[\]{}])|(?P<other>.)"
    )

    def tokenize(self, source: str) -> list[Token]:
        tokens: list[Token] = []
        indents = [0]
        at_line_start = True
        line = 1
        column = 1
        for raw in source.splitlines(keepends=True):
            content = raw.rstrip("\r\n")
            if not content.strip() or content.lstrip().startswith("#"):
                line += 1
                continue
            indent = len(content) - len(content.lstrip(" "))
            if indent > indents[-1]:
                indents.append(indent)
                tokens.append(Token("INDENT", indent, line, 1))
            while indent < indents[-1]:
                indents.pop()
                tokens.append(Token("DEDENT", indent, line, 1))
            if indent != indents[-1]:
                raise UkrCodeError("неправильний відступ", line, 1)
            position = indent
            while position < len(content):
                match = self._token.match(content, position)
                if not match:
                    raise UkrCodeError("неочікуваний символ", line, position + 1)
                kind, value = match.lastgroup, match.group()
                position = match.end()
                if kind == "space":
                    continue
                if kind == "other":
                    raise UkrCodeError(f"невідомий символ {value!r}", line, position)
                if kind == "string":
                    try:
                        value = ast.literal_eval(value)
                    except (SyntaxError, ValueError) as error:
                        raise UkrCodeError("пошкоджений рядок", line, position) from error
                    kind = "STRING"
                elif kind == "number":
                    value = float(value) if "." in value else int(value)
                    kind = "NUMBER"
                elif kind == "name":
                    kind = "NAME"
                else:
                    kind = "OP"
                tokens.append(Token(kind, value, line, position - len(match.group())))
            tokens.append(Token("NEWLINE", "\n", line, len(content) + 1))
            line += 1
            at_line_start = True
        while len(indents) > 1:
            indents.pop()
            tokens.append(Token("DEDENT", 0, line, 1))
        tokens.append(Token("EOF", "", line, 1))
        return tokens