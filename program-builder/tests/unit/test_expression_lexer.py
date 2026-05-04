"""Tests for the expression engine lexer -- written FIRST (TDD RED phase)."""

import pytest

from src.core.expression.lexer import Lexer, Token, TokenType


class TestTokenTypes:
    def test_number_integer(self) -> None:
        tokens = Lexer("42").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, "42")

    def test_number_float(self) -> None:
        tokens = Lexer("0.90").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, "0.90")

    def test_string_single_quotes(self) -> None:
        tokens = Lexer("'hello world'").tokenize()
        assert tokens[0] == Token(TokenType.STRING, "hello world")

    def test_string_empty(self) -> None:
        tokens = Lexer("''").tokenize()
        assert tokens[0] == Token(TokenType.STRING, "")

    def test_identifier(self) -> None:
        tokens = Lexer("ctx").tokenize()
        assert tokens[0] == Token(TokenType.IDENTIFIER, "ctx")

    def test_true_keyword(self) -> None:
        tokens = Lexer("true").tokenize()
        assert tokens[0] == Token(TokenType.TRUE, "true")

    def test_false_keyword(self) -> None:
        tokens = Lexer("false").tokenize()
        assert tokens[0] == Token(TokenType.FALSE, "false")


class TestOperators:
    def test_dot(self) -> None:
        tokens = Lexer("ctx.week").tokenize()
        assert tokens[1] == Token(TokenType.DOT, ".")

    def test_equality(self) -> None:
        tokens = Lexer("a == b").tokenize()
        assert tokens[1] == Token(TokenType.EQ, "==")

    def test_not_equal(self) -> None:
        tokens = Lexer("a != b").tokenize()
        assert tokens[1] == Token(TokenType.NEQ, "!=")

    def test_less_than(self) -> None:
        tokens = Lexer("a < b").tokenize()
        assert tokens[1] == Token(TokenType.LT, "<")

    def test_less_equal(self) -> None:
        tokens = Lexer("a <= b").tokenize()
        assert tokens[1] == Token(TokenType.LTE, "<=")

    def test_greater_than(self) -> None:
        tokens = Lexer("a > b").tokenize()
        assert tokens[1] == Token(TokenType.GT, ">")

    def test_greater_equal(self) -> None:
        tokens = Lexer("a >= b").tokenize()
        assert tokens[1] == Token(TokenType.GTE, ">=")

    def test_and_operator(self) -> None:
        tokens = Lexer("a && b").tokenize()
        assert tokens[1] == Token(TokenType.AND, "&&")

    def test_or_operator(self) -> None:
        tokens = Lexer("a || b").tokenize()
        assert tokens[1] == Token(TokenType.OR, "||")

    def test_plus(self) -> None:
        tokens = Lexer("a + b").tokenize()
        assert tokens[1] == Token(TokenType.PLUS, "+")

    def test_minus(self) -> None:
        tokens = Lexer("a - b").tokenize()
        assert tokens[1] == Token(TokenType.MINUS, "-")

    def test_multiply(self) -> None:
        tokens = Lexer("a * b").tokenize()
        assert tokens[1] == Token(TokenType.STAR, "*")

    def test_divide(self) -> None:
        tokens = Lexer("a / b").tokenize()
        assert tokens[1] == Token(TokenType.SLASH, "/")

    def test_not_operator(self) -> None:
        tokens = Lexer("!a").tokenize()
        assert tokens[0] == Token(TokenType.NOT, "!")


class TestDelimiters:
    def test_parens(self) -> None:
        tokens = Lexer("()").tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_brackets(self) -> None:
        tokens = Lexer("[]").tokenize()
        assert tokens[0].type == TokenType.LBRACKET
        assert tokens[1].type == TokenType.RBRACKET

    def test_braces(self) -> None:
        tokens = Lexer("{}").tokenize()
        assert tokens[0].type == TokenType.LBRACE
        assert tokens[1].type == TokenType.RBRACE

    def test_comma(self) -> None:
        tokens = Lexer(",").tokenize()
        assert tokens[0].type == TokenType.COMMA

    def test_colon(self) -> None:
        tokens = Lexer(":").tokenize()
        assert tokens[0].type == TokenType.COLON


class TestComplexExpressions:
    def test_choose_array(self) -> None:
        expr = "choose(ctx.week,[5,5,3,5])"
        tokens = Lexer(expr).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.IDENTIFIER in types
        assert TokenType.LPAREN in types
        assert TokenType.DOT in types
        assert TokenType.COMMA in types
        assert TokenType.LBRACKET in types
        assert TokenType.NUMBER in types

    def test_choose_dict(self) -> None:
        expr = "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})"
        tokens = Lexer(expr).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.LBRACE in types
        assert TokenType.STRING in types
        assert TokenType.COLON in types

    def test_boolean_expression(self) -> None:
        expr = (
            "ctx.conditioning.method=='HR_ZONES'"
            " && ctx.conditioning.hr_zone_formula=='KARVONEN_HRR'"
        )
        tokens = Lexer(expr).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types.count(TokenType.EQ) == 2
        assert TokenType.AND in types

    def test_zone_function(self) -> None:
        expr = "z(2)"
        tokens = Lexer(expr).tokenize()
        assert tokens[0] == Token(TokenType.IDENTIFIER, "z")
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2] == Token(TokenType.NUMBER, "2")
        assert tokens[3].type == TokenType.RPAREN

    def test_string_literal_expression(self) -> None:
        expr = "'Conversational pace / nasal breathing if possible'"
        tokens = Lexer(expr).tokenize()
        assert tokens[0].type == TokenType.STRING
        assert "Conversational" in tokens[0].value

    def test_eof_always_last(self) -> None:
        tokens = Lexer("42 + x").tokenize()
        assert tokens[-1].type == TokenType.EOF

    def test_whitespace_ignored(self) -> None:
        tokens1 = Lexer("a+b").tokenize()
        tokens2 = Lexer("a + b").tokenize()
        non_eof1 = [t for t in tokens1 if t.type != TokenType.EOF]
        non_eof2 = [t for t in tokens2 if t.type != TokenType.EOF]
        assert non_eof1 == non_eof2

    def test_empty_expression(self) -> None:
        tokens = Lexer("").tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_invalid_character_raises(self) -> None:
        with pytest.raises(ValueError, match="Unexpected character"):
            Lexer("@invalid").tokenize()
