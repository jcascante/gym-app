"""AST node types for the expression engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ASTNode:
    pass


@dataclass(frozen=True)
class NumberLiteral(ASTNode):
    value: int | float


@dataclass(frozen=True)
class StringLiteral(ASTNode):
    value: str


@dataclass(frozen=True)
class BoolLiteral(ASTNode):
    value: bool


@dataclass(frozen=True)
class ArrayLiteral(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)


@dataclass(frozen=True)
class DictLiteral(ASTNode):
    pairs: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)


@dataclass(frozen=True)
class Identifier(ASTNode):
    name: str


@dataclass(frozen=True)
class MemberAccess(ASTNode):
    obj: ASTNode
    attr: str


@dataclass(frozen=True)
class FunctionCall(ASTNode):
    name: str
    args: list[ASTNode] = field(default_factory=list)


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    op: str
    left: ASTNode = field(default_factory=ASTNode)
    right: ASTNode = field(default_factory=ASTNode)


@dataclass(frozen=True)
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode = field(default_factory=ASTNode)
