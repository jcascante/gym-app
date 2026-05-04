"""Sandboxed evaluator for the expression engine.

Only whitelisted functions are available. No access to Python builtins,
eval, exec, __import__, or any other dangerous construct.
"""

from __future__ import annotations

from typing import Any

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
from src.core.expression.parser import Parser


def _builtin_choose(key: Any, lookup: Any) -> Any:
    """choose(key, array_or_dict) -- 1-indexed for arrays, key-lookup for dicts."""
    if isinstance(lookup, list):
        idx = int(key) - 1
        if idx < 0 or idx >= len(lookup):
            raise ValueError(
                f"choose() index {key} out of range for array of length {len(lookup)}"
            )
        return lookup[idx]
    if isinstance(lookup, dict):
        str_key = str(key)
        if str_key not in lookup:
            raise ValueError(
                f"choose() key '{str_key}' not found in dict {list(lookup.keys())}"
            )
        return lookup[str_key]
    raise ValueError(f"choose() second argument must be array or dict, got {type(lookup)}")


ALLOWED_FUNCTIONS: dict[str, Any] = {
    "choose": _builtin_choose,
    "z": lambda n: f"z({n})",
    "thr": lambda: "thr()",
    "vo2": lambda: "vo2()",
}


class ExpressionEvaluator:
    def __init__(self, extra_functions: dict[str, Any] | None = None) -> None:
        self._functions = {**ALLOWED_FUNCTIONS}
        if extra_functions:
            self._functions.update(extra_functions)

    def evaluate(self, expression: str, ctx: dict[str, Any] | None = None) -> Any:
        ast = Parser(expression).parse()
        env: dict[str, Any] = {}
        if ctx is not None:
            env["ctx"] = ctx
            for k, v in ctx.items():
                if k != "ctx":
                    env[k] = v
        return self._eval(ast, env)

    def _eval(self, node: ASTNode, env: dict[str, Any]) -> Any:
        if isinstance(node, NumberLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value

        if isinstance(node, ArrayLiteral):
            return [self._eval(el, env) for el in node.elements]

        if isinstance(node, DictLiteral):
            return {
                self._eval(k, env): self._eval(v, env) for k, v in node.pairs
            }

        if isinstance(node, Identifier):
            if node.name in env:
                return env[node.name]
            raise ValueError(f"Undefined variable '{node.name}'")

        if isinstance(node, MemberAccess):
            obj = self._eval(node.obj, env)
            if isinstance(obj, dict):
                if node.attr not in obj:
                    raise ValueError(
                        f"Key '{node.attr}' not found in dict"
                    )
                return obj[node.attr]
            raise ValueError(
                f"Cannot access attribute '{node.attr}' on {type(obj).__name__}"
            )

        if isinstance(node, FunctionCall):
            return self._eval_function(node, env)

        if isinstance(node, BinaryOp):
            return self._eval_binary(node, env)

        if isinstance(node, UnaryOp):
            return self._eval_unary(node, env)

        raise ValueError(f"Unknown AST node type: {type(node)}")

    def _eval_function(self, node: FunctionCall, env: dict[str, Any]) -> Any:
        if node.name not in self._functions:
            raise ValueError(f"Unknown function '{node.name}'")
        fn = self._functions[node.name]
        args = [self._eval(arg, env) for arg in node.args]
        return fn(*args)

    def _eval_binary(self, node: BinaryOp, env: dict[str, Any]) -> Any:
        left = self._eval(node.left, env)
        right = self._eval(node.right, env)

        match node.op:
            case "+":
                return left + right
            case "-":
                return left - right
            case "*":
                return left * right
            case "/":
                if right == 0:
                    raise ValueError("Division by zero")
                return left / right
            case "==":
                return left == right
            case "!=":
                return left != right
            case "<":
                return left < right
            case "<=":
                return left <= right
            case ">":
                return left > right
            case ">=":
                return left >= right
            case "&&":
                return bool(left) and bool(right)
            case "||":
                return bool(left) or bool(right)
            case _:
                raise ValueError(f"Unknown operator '{node.op}'")

    def _eval_unary(self, node: UnaryOp, env: dict[str, Any]) -> Any:
        operand = self._eval(node.operand, env)
        if node.op == "!":
            return not operand
        if node.op == "-":
            return -operand
        raise ValueError(f"Unknown unary operator '{node.op}'")
