"""Tests for the expression engine parser -- written FIRST (TDD RED phase)."""

from src.core.expression.ast_nodes import (
    ArrayLiteral,
    BinaryOp,
    BoolLiteral,
    DictLiteral,
    FunctionCall,
    MemberAccess,
    NumberLiteral,
    StringLiteral,
    UnaryOp,
)
from src.core.expression.parser import Parser


class TestLiterals:
    def test_number_integer(self) -> None:
        node = Parser("42").parse()
        assert isinstance(node, NumberLiteral)
        assert node.value == 42

    def test_number_float(self) -> None:
        node = Parser("0.90").parse()
        assert isinstance(node, NumberLiteral)
        assert node.value == 0.9

    def test_string(self) -> None:
        node = Parser("'hello'").parse()
        assert isinstance(node, StringLiteral)
        assert node.value == "hello"

    def test_true(self) -> None:
        node = Parser("true").parse()
        assert isinstance(node, BoolLiteral)
        assert node.value is True

    def test_false(self) -> None:
        node = Parser("false").parse()
        assert isinstance(node, BoolLiteral)
        assert node.value is False


class TestArraysAndDicts:
    def test_array_literal(self) -> None:
        node = Parser("[5,5,3,5]").parse()
        assert isinstance(node, ArrayLiteral)
        assert len(node.elements) == 4
        assert all(isinstance(e, NumberLiteral) for e in node.elements)

    def test_empty_array(self) -> None:
        node = Parser("[]").parse()
        assert isinstance(node, ArrayLiteral)
        assert len(node.elements) == 0

    def test_dict_literal(self) -> None:
        node = Parser("{'novice':16,'intermediate':20,'advanced':24}").parse()
        assert isinstance(node, DictLiteral)
        assert len(node.pairs) == 3

    def test_empty_dict(self) -> None:
        node = Parser("{}").parse()
        assert isinstance(node, DictLiteral)
        assert len(node.pairs) == 0


class TestMemberAccess:
    def test_simple_member(self) -> None:
        node = Parser("ctx.week").parse()
        assert isinstance(node, MemberAccess)
        assert node.attr == "week"

    def test_nested_member(self) -> None:
        node = Parser("ctx.athlete.level").parse()
        assert isinstance(node, MemberAccess)
        assert node.attr == "level"
        assert isinstance(node.obj, MemberAccess)
        assert node.obj.attr == "athlete"

    def test_deep_nested_member(self) -> None:
        node = Parser("ctx.conditioning.hr_zone_formula").parse()
        assert isinstance(node, MemberAccess)
        assert node.attr == "hr_zone_formula"


class TestFunctionCalls:
    def test_choose_with_array(self) -> None:
        node = Parser("choose(ctx.week,[5,5,3,5])").parse()
        assert isinstance(node, FunctionCall)
        assert node.name == "choose"
        assert len(node.args) == 2
        assert isinstance(node.args[1], ArrayLiteral)

    def test_choose_with_dict(self) -> None:
        node = Parser(
            "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})"
        ).parse()
        assert isinstance(node, FunctionCall)
        assert node.name == "choose"
        assert isinstance(node.args[1], DictLiteral)

    def test_zone_function(self) -> None:
        node = Parser("z(2)").parse()
        assert isinstance(node, FunctionCall)
        assert node.name == "z"
        assert len(node.args) == 1

    def test_thr_function(self) -> None:
        node = Parser("thr()").parse()
        assert isinstance(node, FunctionCall)
        assert node.name == "thr"
        assert len(node.args) == 0

    def test_vo2_function(self) -> None:
        node = Parser("vo2()").parse()
        assert isinstance(node, FunctionCall)
        assert node.name == "vo2"


class TestBinaryOperations:
    def test_addition(self) -> None:
        node = Parser("1 + 2").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "+"

    def test_subtraction(self) -> None:
        node = Parser("10 - 3").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "-"

    def test_multiplication(self) -> None:
        node = Parser("exercise.fatigue_cost * intensity_factor").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "*"

    def test_division(self) -> None:
        node = Parser("100 / 4").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "/"

    def test_equality(self) -> None:
        node = Parser("ctx.rules.allow_optional_ohp == true").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "=="

    def test_not_equal(self) -> None:
        node = Parser("a != b").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "!="

    def test_comparison_lt(self) -> None:
        node = Parser("a < 10").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "<"

    def test_comparison_gte(self) -> None:
        node = Parser("a >= 6").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == ">="

    def test_and_expression(self) -> None:
        node = Parser("a == 1 && b == 2").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "&&"

    def test_or_expression(self) -> None:
        node = Parser("a || b").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "||"


class TestUnaryOperations:
    def test_unary_not(self) -> None:
        node = Parser("!true").parse()
        assert isinstance(node, UnaryOp)
        assert node.op == "!"

    def test_unary_minus(self) -> None:
        node = Parser("-5").parse()
        assert isinstance(node, UnaryOp)
        assert node.op == "-"


class TestPrecedence:
    def test_multiplication_before_addition(self) -> None:
        node = Parser("2 + 3 * 4").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "+"
        assert isinstance(node.right, BinaryOp)
        assert node.right.op == "*"

    def test_comparison_before_logical(self) -> None:
        node = Parser("a == 1 && b == 2").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "&&"
        assert isinstance(node.left, BinaryOp)
        assert node.left.op == "=="

    def test_parenthesized_group(self) -> None:
        node = Parser("(2 + 3) * 4").parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "*"
        assert isinstance(node.left, BinaryOp)
        assert node.left.op == "+"


class TestRealExpressions:
    """Test expressions from actual program definitions."""

    def test_choose_week_reps(self) -> None:
        node = Parser("choose(ctx.week,[5,5,3,5])").parse()
        assert isinstance(node, FunctionCall)

    def test_choose_week_rpe(self) -> None:
        node = Parser("choose(ctx.week,[7,8,8.5,6])").parse()
        assert isinstance(node, FunctionCall)

    def test_backoff_load_factor(self) -> None:
        node = Parser("0.90").parse()
        assert isinstance(node, NumberLiteral)

    def test_conditional_enabled(self) -> None:
        node = Parser("ctx.rules.allow_optional_ohp == true").parse()
        assert isinstance(node, BinaryOp)

    def test_accessory_rir_target(self) -> None:
        node = Parser("ctx.rules.accessory_rir_target").parse()
        assert isinstance(node, MemberAccess)

    def test_fatigue_model_expr(self) -> None:
        node = Parser("exercise.fatigue_cost * intensity_factor").parse()
        assert isinstance(node, BinaryOp)

    def test_max_volume_choose(self) -> None:
        node = Parser(
            "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})"
        ).parse()
        assert isinstance(node, FunctionCall)

    def test_string_literal_notes(self) -> None:
        node = Parser("'Conversational pace / nasal breathing if possible'").parse()
        assert isinstance(node, StringLiteral)

    def test_conditioning_boolean_compound(self) -> None:
        expr = (
            "ctx.conditioning.method=='HR_ZONES'"
            " && ctx.conditioning.hr_zone_formula=='KARVONEN_HRR'"
        )
        node = Parser(expr).parse()
        assert isinstance(node, BinaryOp)
        assert node.op == "&&"
