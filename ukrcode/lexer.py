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
        source = self._normalize_python_blocks(source)
        tokens: list[Token] = []
        indents = [0]
        group_depth = 0
        pending_block_after_colon = False
        line = 1
        for raw in source.splitlines(keepends=True):
            content = raw.rstrip("\r\n")
            if not content.strip() or content.lstrip().startswith("#"):
                line += 1
                continue
            indent = len(content) - len(content.lstrip(" "))
            if pending_block_after_colon and indent > indents[-1]:
                indents.append(indent)
                tokens.append(Token("INDENT", indent, line, 1))
            while (pending_block_after_colon or group_depth == 0) and indent < indents[-1]:
                indents.pop()
                tokens.append(Token("DEDENT", indent, line, 1))
            if group_depth == 0 and indent != indents[-1]:
                raise UkrCodeError("неправильний відступ", line, 1)
            position = indent
            line_ended_with_colon = False
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
                    if value == ":":
                        line_ended_with_colon = True
                    if value in "([{": group_depth += 1
                    elif value in ")]}": group_depth = max(0, group_depth - 1)
                tokens.append(Token(kind, value, line, position - len(match.group())))
            pending_block_after_colon = line_ended_with_colon
            tokens.append(Token("NEWLINE", "\n", line, len(content) + 1))
            line += 1
        while len(indents) > 1:
            indents.pop()
            tokens.append(Token("DEDENT", 0, line, 1))
        tokens.append(Token("EOF", "", line, 1))
        return tokens

    @staticmethod
    def _normalize_python_blocks(source: str) -> str:
        pattern = re.compile(r"пайтон\(\s*(?P<quote>'''|\"\"\")(?P<code>.*?)(?P=quote)\s*\)", re.DOTALL)

        def replace(match):
            return "пайтон(" + repr(match.group("code")) + ")"

        return pattern.sub(replace, source)