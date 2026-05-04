"""Lexer (tokenizer) for the expression engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto


class TokenType(StrEnum):
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    TRUE = auto()
    FALSE = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    DOT = auto()
    COMMA = auto()
    COLON = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()

    EOF = auto()


KEYWORDS = {"true": TokenType.TRUE, "false": TokenType.FALSE}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str


class Lexer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self._pos < len(self._source):
            ch = self._source[self._pos]
            if ch in " \t\r\n":
                self._pos += 1
            elif ch == "'":
                tokens.append(self._read_string())
            elif ch.isdigit() or (ch == "." and self._peek_digit()):
                tokens.append(self._read_number())
            elif ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier())
            elif ch == "=" and self._peek("="):
                tokens.append(Token(TokenType.EQ, "=="))
                self._pos += 2
            elif ch == "!" and self._peek("="):
                tokens.append(Token(TokenType.NEQ, "!="))
                self._pos += 2
            elif ch == "!":
                tokens.append(Token(TokenType.NOT, "!"))
                self._pos += 1
            elif ch == "<" and self._peek("="):
                tokens.append(Token(TokenType.LTE, "<="))
                self._pos += 2
            elif ch == "<":
                tokens.append(Token(TokenType.LT, "<"))
                self._pos += 1
            elif ch == ">" and self._peek("="):
                tokens.append(Token(TokenType.GTE, ">="))
                self._pos += 2
            elif ch == ">":
                tokens.append(Token(TokenType.GT, ">"))
                self._pos += 1
            elif ch == "&" and self._peek("&"):
                tokens.append(Token(TokenType.AND, "&&"))
                self._pos += 2
            elif ch == "|" and self._peek("|"):
                tokens.append(Token(TokenType.OR, "||"))
                self._pos += 2
            elif ch == "+":
                tokens.append(Token(TokenType.PLUS, "+"))
                self._pos += 1
            elif ch == "-":
                tokens.append(Token(TokenType.MINUS, "-"))
                self._pos += 1
            elif ch == "*":
                tokens.append(Token(TokenType.STAR, "*"))
                self._pos += 1
            elif ch == "/":
                tokens.append(Token(TokenType.SLASH, "/"))
                self._pos += 1
            elif ch == ".":
                tokens.append(Token(TokenType.DOT, "."))
                self._pos += 1
            elif ch == ",":
                tokens.append(Token(TokenType.COMMA, ","))
                self._pos += 1
            elif ch == ":":
                tokens.append(Token(TokenType.COLON, ":"))
                self._pos += 1
            elif ch == "(":
                tokens.append(Token(TokenType.LPAREN, "("))
                self._pos += 1
            elif ch == ")":
                tokens.append(Token(TokenType.RPAREN, ")"))
                self._pos += 1
            elif ch == "[":
                tokens.append(Token(TokenType.LBRACKET, "["))
                self._pos += 1
            elif ch == "]":
                tokens.append(Token(TokenType.RBRACKET, "]"))
                self._pos += 1
            elif ch == "{":
                tokens.append(Token(TokenType.LBRACE, "{"))
                self._pos += 1
            elif ch == "}":
                tokens.append(Token(TokenType.RBRACE, "}"))
                self._pos += 1
            else:
                raise ValueError(f"Unexpected character '{ch}' at position {self._pos}")

        tokens.append(Token(TokenType.EOF, ""))
        return tokens

    def _peek(self, expected: str) -> bool:
        nxt = self._pos + 1
        return nxt < len(self._source) and self._source[nxt] == expected

    def _peek_digit(self) -> bool:
        nxt = self._pos + 1
        return nxt < len(self._source) and self._source[nxt].isdigit()

    def _read_string(self) -> Token:
        self._pos += 1  # skip opening quote
        start = self._pos
        while self._pos < len(self._source) and self._source[self._pos] != "'":
            self._pos += 1
        if self._pos >= len(self._source):
            raise ValueError("Unterminated string literal")
        value = self._source[start : self._pos]
        self._pos += 1  # skip closing quote
        return Token(TokenType.STRING, value)

    def _read_number(self) -> Token:
        start = self._pos
        while self._pos < len(self._source) and (
            self._source[self._pos].isdigit() or self._source[self._pos] == "."
        ):
            self._pos += 1
        return Token(TokenType.NUMBER, self._source[start : self._pos])

    def _read_identifier(self) -> Token:
        start = self._pos
        while self._pos < len(self._source) and (
            self._source[self._pos].isalnum() or self._source[self._pos] == "_"
        ):
            self._pos += 1
        word = self._source[start : self._pos]
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word)
