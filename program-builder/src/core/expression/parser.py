"""Recursive-descent parser for the expression engine.

Operator precedence (lowest to highest):
  1. || (logical OR)
  2. && (logical AND)
  3. ==, !=, <, <=, >, >= (comparison)
  4. +, - (additive)
  5. *, / (multiplicative)
  6. !, - (unary prefix)
  7. ., () (postfix: member access, function call)
  8. atoms: number, string, bool, identifier, array, dict, grouped expr
"""

from __future__ import annotations

from src.core.expression.ast_nodes import (
    ArrayLiteral,
    ASTNode,
    BinaryOp,
    BoolLiteral,
    DictLiteral,
    FunctionCall,
    Identifier,
    MemberAccess,
    NumberLiteral,
    StringLiteral,
    UnaryOp,
)
from src.core.expression.lexer import Lexer, Token, TokenType


class Parser:
    def __init__(self, source: str) -> None:
        self._tokens = Lexer(source).tokenize()
        self._pos = 0

    def parse(self) -> ASTNode:
        node = self._parse_or()
        if self._current().type != TokenType.EOF:
            raise ValueError(
                f"Unexpected token {self._current()} after expression"
            )
        return node

    # -- Precedence levels --------------------------------------------------

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._match(TokenType.OR):
            right = self._parse_and()
            left = BinaryOp(op="||", left=left, right=right)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_comparison()
        while self._match(TokenType.AND):
            right = self._parse_comparison()
            left = BinaryOp(op="&&", left=left, right=right)
        return left

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_additive()
        while self._current().type in (
            TokenType.EQ,
            TokenType.NEQ,
            TokenType.LT,
            TokenType.LTE,
            TokenType.GT,
            TokenType.GTE,
        ):
            op = self._advance().value
            right = self._parse_additive()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    def _parse_additive(self) -> ASTNode:
        left = self._parse_multiplicative()
        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    def _parse_multiplicative(self) -> ASTNode:
        left = self._parse_unary()
        while self._current().type in (TokenType.STAR, TokenType.SLASH):
            op = self._advance().value
            right = self._parse_unary()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    def _parse_unary(self) -> ASTNode:
        if self._current().type == TokenType.NOT:
            self._advance()
            operand = self._parse_unary()
            return UnaryOp(op="!", operand=operand)
        if self._current().type == TokenType.MINUS:
            self._advance()
            operand = self._parse_unary()
            return UnaryOp(op="-", operand=operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        node = self._parse_atom()
        while True:
            if self._current().type == TokenType.DOT:
                self._advance()
                attr_token = self._expect(TokenType.IDENTIFIER)
                node = MemberAccess(obj=node, attr=attr_token.value)
            elif self._current().type == TokenType.LPAREN and isinstance(node, Identifier):
                node = self._parse_function_call(node.name)
            else:
                break
        return node

    def _parse_function_call(self, name: str) -> FunctionCall:
        self._expect(TokenType.LPAREN)
        args: list[ASTNode] = []
        if self._current().type != TokenType.RPAREN:
            args.append(self._parse_or())
            while self._match(TokenType.COMMA):
                args.append(self._parse_or())
        self._expect(TokenType.RPAREN)
        return FunctionCall(name=name, args=args)

    def _parse_atom(self) -> ASTNode:
        tok = self._current()

        if tok.type == TokenType.NUMBER:
            self._advance()
            val = float(tok.value)
            return NumberLiteral(value=int(val) if val == int(val) else val)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(value=tok.value)

        if tok.type == TokenType.TRUE:
            self._advance()
            return BoolLiteral(value=True)

        if tok.type == TokenType.FALSE:
            self._advance()
            return BoolLiteral(value=False)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(name=tok.value)

        if tok.type == TokenType.LBRACKET:
            return self._parse_array()

        if tok.type == TokenType.LBRACE:
            return self._parse_dict()

        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_or()
            self._expect(TokenType.RPAREN)
            return node

        raise ValueError(f"Unexpected token {tok} at position {self._pos}")

    def _parse_array(self) -> ArrayLiteral:
        self._expect(TokenType.LBRACKET)
        elements: list[ASTNode] = []
        if self._current().type != TokenType.RBRACKET:
            elements.append(self._parse_or())
            while self._match(TokenType.COMMA):
                elements.append(self._parse_or())
        self._expect(TokenType.RBRACKET)
        return ArrayLiteral(elements=elements)

    def _parse_dict(self) -> DictLiteral:
        self._expect(TokenType.LBRACE)
        pairs: list[tuple[ASTNode, ASTNode]] = []
        if self._current().type != TokenType.RBRACE:
            key = self._parse_or()
            self._expect(TokenType.COLON)
            value = self._parse_or()
            pairs.append((key, value))
            while self._match(TokenType.COMMA):
                key = self._parse_or()
                self._expect(TokenType.COLON)
                value = self._parse_or()
                pairs.append((key, value))
        self._expect(TokenType.RBRACE)
        return DictLiteral(pairs=pairs)

    # -- Helpers ------------------------------------------------------------

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match(self, token_type: TokenType) -> bool:
        if self._current().type == token_type:
            self._advance()
            return True
        return False

    def _expect(self, token_type: TokenType) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise ValueError(f"Expected {token_type}, got {tok} at position {self._pos}")
        self._advance()
        return tok
