"""Tests for the expression engine evaluator -- written FIRST (TDD RED phase)."""

import pytest

from src.core.expression.evaluator import ExpressionEvaluator


@pytest.fixture
def evaluator() -> ExpressionEvaluator:
    return ExpressionEvaluator()


@pytest.fixture
def strength_ctx() -> dict:
    return {
        "week": 1,
        "athlete": {
            "level": "intermediate",
            "equipment": ["barbell", "rack", "bench", "dumbbells"],
            "restrictions": [],
            "e1rm": {"squat": 160, "bench": 115, "deadlift": 190, "ohp": 70},
        },
        "rules": {
            "main_method": "HYBRID",
            "hard_set_rule": "RIR_LE_4",
            "accessory_rir_target": 2,
            "rounding_profile": "plate_2p5kg",
            "volume_metric": "hard_sets_weighted",
            "allow_optional_ohp": True,
        },
    }


@pytest.fixture
def conditioning_ctx() -> dict:
    return {
        "week": 1,
        "athlete": {
            "level": "intermediate",
            "time_budget_minutes": 60,
            "modality": "run",
            "equipment": [],
        },
        "conditioning": {
            "method": "HR_ZONES",
            "hr_zone_formula": "KARVONEN_HRR",
            "hr_max": 190,
            "hr_rest": 55,
        },
    }


# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------

class TestLiterals:
    def test_integer(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("42") == 42

    def test_float(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("0.90") == 0.9

    def test_string(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("'hello'") == "hello"

    def test_true(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("true") is True

    def test_false(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("false") is False

    def test_empty_array(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("[]") == []


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

class TestArithmetic:
    def test_addition(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("2 + 3") == 5

    def test_subtraction(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("10 - 3") == 7

    def test_multiplication(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("4 * 5") == 20

    def test_division(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("100 / 4") == 25.0

    def test_unary_minus(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("-5") == -5

    def test_precedence(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("2 + 3 * 4") == 14

    def test_parentheses(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("(2 + 3) * 4") == 20

    def test_division_by_zero(self, evaluator: ExpressionEvaluator) -> None:
        with pytest.raises(ValueError, match=r"[Dd]ivision by zero"):
            evaluator.evaluate("1 / 0")


# ---------------------------------------------------------------------------
# Comparison / Boolean
# ---------------------------------------------------------------------------

class TestComparison:
    def test_equality_true(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("5 == 5") is True

    def test_equality_false(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("5 == 6") is False

    def test_not_equal(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("5 != 6") is True

    def test_less_than(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("3 < 5") is True

    def test_less_equal(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("5 <= 5") is True

    def test_greater_than(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("6 > 5") is True

    def test_greater_equal(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("5 >= 6") is False

    def test_string_equality(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("'HR_ZONES' == 'HR_ZONES'") is True

    def test_string_inequality(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("'HR_ZONES' != 'PACE'") is True


class TestLogical:
    def test_and_true(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("true && true") is True

    def test_and_false(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("true && false") is False

    def test_or_true(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("false || true") is True

    def test_or_false(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("false || false") is False

    def test_not_true(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("!true") is False

    def test_not_false(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("!false") is True

    def test_compound_and_or(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("true && false || true") is True


# ---------------------------------------------------------------------------
# Context Access
# ---------------------------------------------------------------------------

class TestContextAccess:
    def test_simple_context_field(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.week", ctx=strength_ctx)
        assert result == 1

    def test_nested_context_field(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.athlete.level", ctx=strength_ctx)
        assert result == "intermediate"

    def test_deep_nested_field(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.athlete.e1rm.squat", ctx=strength_ctx)
        assert result == 160

    def test_rules_field(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.rules.accessory_rir_target", ctx=strength_ctx)
        assert result == 2

    def test_boolean_context_field(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.rules.allow_optional_ohp", ctx=strength_ctx)
        assert result is True

    def test_conditioning_context(
        self, evaluator: ExpressionEvaluator, conditioning_ctx: dict
    ) -> None:
        result = evaluator.evaluate("ctx.conditioning.method", ctx=conditioning_ctx)
        assert result == "HR_ZONES"

    def test_missing_context_raises(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        with pytest.raises((KeyError, AttributeError, ValueError)):
            evaluator.evaluate("ctx.nonexistent.field", ctx=strength_ctx)


# ---------------------------------------------------------------------------
# choose() Function
# ---------------------------------------------------------------------------

class TestChoose:
    def test_choose_with_array_week1(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        strength_ctx["week"] = 1
        result = evaluator.evaluate("choose(ctx.week,[5,5,3,5])", ctx=strength_ctx)
        assert result == 5

    def test_choose_with_array_week3(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        strength_ctx["week"] = 3
        result = evaluator.evaluate("choose(ctx.week,[5,5,3,5])", ctx=strength_ctx)
        assert result == 3

    def test_choose_with_array_week4(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        strength_ctx["week"] = 4
        result = evaluator.evaluate("choose(ctx.week,[5,5,3,5])", ctx=strength_ctx)
        assert result == 5

    def test_choose_with_dict_novice(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"athlete": {"level": "novice"}}
        result = evaluator.evaluate(
            "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})",
            ctx=ctx,
        )
        assert result == 16

    def test_choose_with_dict_intermediate(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"athlete": {"level": "intermediate"}}
        result = evaluator.evaluate(
            "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})",
            ctx=ctx,
        )
        assert result == 20

    def test_choose_with_dict_advanced(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"athlete": {"level": "advanced"}}
        result = evaluator.evaluate(
            "choose(ctx.athlete.level, {'novice':16,'intermediate':20,'advanced':24})",
            ctx=ctx,
        )
        assert result == 24

    def test_choose_with_float_array(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        strength_ctx["week"] = 2
        result = evaluator.evaluate("choose(ctx.week,[7,8,8.5,6])", ctx=strength_ctx)
        assert result == 8

    def test_choose_array_out_of_bounds(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"week": 10}
        with pytest.raises((IndexError, ValueError)):
            evaluator.evaluate("choose(ctx.week,[1,2,3])", ctx=ctx)

    def test_choose_dict_missing_key(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"athlete": {"level": "elite"}}
        with pytest.raises((KeyError, ValueError)):
            evaluator.evaluate(
                "choose(ctx.athlete.level, {'novice':16,'intermediate':20})",
                ctx=ctx,
            )


# ---------------------------------------------------------------------------
# Context Comparison Expressions (from program definitions)
# ---------------------------------------------------------------------------

class TestRealExpressions:
    def test_optional_ohp_enabled(
        self, evaluator: ExpressionEvaluator, strength_ctx: dict
    ) -> None:
        result = evaluator.evaluate(
            "ctx.rules.allow_optional_ohp == true", ctx=strength_ctx
        )
        assert result is True

    def test_conditioning_method_check(
        self, evaluator: ExpressionEvaluator, conditioning_ctx: dict
    ) -> None:
        result = evaluator.evaluate(
            "ctx.conditioning.method=='HR_ZONES'", ctx=conditioning_ctx
        )
        assert result is True

    def test_compound_boolean(
        self, evaluator: ExpressionEvaluator, conditioning_ctx: dict
    ) -> None:
        expr = (
            "ctx.conditioning.method=='HR_ZONES'"
            " && ctx.conditioning.hr_zone_formula=='KARVONEN_HRR'"
        )
        result = evaluator.evaluate(expr, ctx=conditioning_ctx)
        assert result is True

    def test_compound_boolean_false(
        self, evaluator: ExpressionEvaluator, conditioning_ctx: dict
    ) -> None:
        conditioning_ctx["conditioning"]["hr_zone_formula"] = "PERCENT_HRMAX"
        expr = (
            "ctx.conditioning.method=='HR_ZONES'"
            " && ctx.conditioning.hr_zone_formula=='KARVONEN_HRR'"
        )
        result = evaluator.evaluate(expr, ctx=conditioning_ctx)
        assert result is False

    def test_choose_week_progression(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        """Verify full 4-week progression for squat reps."""
        expected_reps = [5, 5, 3, 5]
        for week in range(1, 5):
            ctx = {"week": week}
            result = evaluator.evaluate("choose(ctx.week,[5,5,3,5])", ctx=ctx)
            expected = expected_reps[week - 1]
            assert result == expected, f"Week {week}: expected {expected}, got {result}"

    def test_choose_week_rpe_progression(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        """Verify full 4-week RPE progression."""
        expected_rpe = [7, 8, 8.5, 6]
        for week in range(1, 5):
            ctx = {"week": week}
            result = evaluator.evaluate("choose(ctx.week,[7,8,8.5,6])", ctx=ctx)
            assert result == expected_rpe[week - 1]

    def test_string_literal_notes(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        result = evaluator.evaluate("'Conversational pace / nasal breathing if possible'")
        assert result == "Conversational pace / nasal breathing if possible"

    def test_simple_number_expression(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        """Prescriptions like sets_expr: '3' should evaluate to number."""
        assert evaluator.evaluate("3") == 3

    def test_backoff_factor(self, evaluator: ExpressionEvaluator) -> None:
        assert evaluator.evaluate("0.90") == 0.9

    def test_multiplication_with_context(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        ctx = {"exercise": {"fatigue_cost": 0.9}}
        result = evaluator.evaluate(
            "exercise.fatigue_cost * 0.8", ctx=ctx
        )
        assert abs(result - 0.72) < 0.001


# ---------------------------------------------------------------------------
# Sandbox Safety
# ---------------------------------------------------------------------------

class TestSandboxSafety:
    def test_no_builtin_access(self, evaluator: ExpressionEvaluator) -> None:
        """Must not allow access to Python builtins."""
        with pytest.raises(ValueError):
            evaluator.evaluate("__import__('os')")

    def test_no_eval(self, evaluator: ExpressionEvaluator) -> None:
        with pytest.raises(ValueError):
            evaluator.evaluate("eval('1+1')")

    def test_no_exec(self, evaluator: ExpressionEvaluator) -> None:
        with pytest.raises(ValueError):
            evaluator.evaluate("exec('x=1')")

    def test_unknown_function_raises(self, evaluator: ExpressionEvaluator) -> None:
        with pytest.raises(ValueError):
            evaluator.evaluate("unknown_func(1,2)")

    def test_variable_without_context_raises(
        self, evaluator: ExpressionEvaluator
    ) -> None:
        with pytest.raises(ValueError):
            evaluator.evaluate("ctx.week")
