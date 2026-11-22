"""Testes unitários das regras matemáticas de notas, rubricas, recuperação e frequência do Lote 3 (BE-030)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from pydantic import ValidationError
import pytest

from app.core.class_period_guard import (
    CLASS_PERIOD_CLOSED_ERROR_CODE,
    CLASS_PERIOD_CLOSED_MESSAGE,
    raise_if_class_period_closed,
)
from app.core.exceptions import UnprocessableEntityException
from app.schemas.academic_assessment import (
    StudentGradeItemInputSchema,
    validate_optional_recovery_grade_pt,
    validate_student_grade_value_pt,
)
from app.schemas.enums import (
    AcademicStandingStatus,
    ClassStatus,
    RiskLevel,
    SubmissionStatus,
)
from app.services.academic_assessment_service import (
    classify_academic_standing,
    compute_senai_effective_grade,
)
from app.services.class_lesson_service import (
    compute_attendance_margin_metrics,
    evaluate_attendance_risk_level,
)
from app.services.practical_task_service import PracticalTaskService


class TestSenaiRecoveryAndGradeBoundaries:
    """Valida a regra pedagógica SENAI (maior nota entre original e recuperação) e casos de borda 0.00 e 10.00."""

    @pytest.mark.parametrize(
        ("grade_value", "recovery_grade", "expected_effective", "expected_applied"),
        [
            (Decimal("0.00"), None, Decimal("0.00"), False),
            (Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), False),
            (Decimal("0.00"), Decimal("6.00"), Decimal("6.00"), True),
            (Decimal("10.00"), None, Decimal("10.00"), False),
            (Decimal("10.00"), Decimal("10.00"), Decimal("10.00"), False),
            (Decimal("10.00"), Decimal("7.50"), Decimal("10.00"), False),
            (Decimal("4.25"), Decimal("7.75"), Decimal("7.75"), True),
            (Decimal("8.50"), Decimal("6.25"), Decimal("8.50"), False),
            (Decimal("6.00"), Decimal("6.00"), Decimal("6.00"), False),
        ],
    )
    def test_compute_senai_effective_grade_cases(
        self,
        grade_value: Decimal,
        recovery_grade: Decimal | None,
        expected_effective: Decimal,
        expected_applied: bool,
    ) -> None:
        effective, is_applied = compute_senai_effective_grade(grade_value, recovery_grade)
        assert effective == expected_effective
        assert is_applied is expected_applied

    def test_pydantic_grade_validators_enforce_zero_to_ten_boundaries(self) -> None:
        """Aceita exatamente 0.00 e 10.00 e rejeita qualquer valor fora de [0.00, 10.00]."""
        assert validate_student_grade_value_pt("0") == Decimal("0.00")
        assert validate_student_grade_value_pt("0.00") == Decimal("0.00")
        assert validate_student_grade_value_pt("10") == Decimal("10.00")
        assert validate_student_grade_value_pt("10.00") == Decimal("10.00")
        assert validate_optional_recovery_grade_pt("0.00") == Decimal("0.00")
        assert validate_optional_recovery_grade_pt("10.00") == Decimal("10.00")
        assert validate_optional_recovery_grade_pt(None) is None

        for invalid in ("-0.01", -5, "10.01", 10.5, "abc"):
            with pytest.raises(ValidationError):
                StudentGradeItemInputSchema.model_validate(
                    {"student_id": str(uuid4()), "grade_value": invalid}
                )
            with pytest.raises(ValidationError):
                StudentGradeItemInputSchema.model_validate(
                    {
                        "student_id": str(uuid4()),
                        "grade_value": "5.00",
                        "recovery_grade": invalid,
                    }
                )


class TestAcademicStandingClassification:
    """Valida classificação APPROVED, IN_RECOVERY e AT_RISK combinando média e frequência."""

    @pytest.mark.parametrize(
        ("average", "passing_score", "attendance_rate", "expected_status", "expected_risk", "expected_below"),
        [
            # Casos de borda: nota 0.00 e nota 10.00
            (Decimal("0.00"), Decimal("6.00"), Decimal("100.00"), AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, True),
            (Decimal("10.00"), Decimal("6.00"), Decimal("100.00"), AcademicStandingStatus.APPROVED, RiskLevel.LOW, False),
            # Fronteiras exatas da nota de corte (6.00) e faixa de recuperação [4.00, 5.99]
            (Decimal("6.00"), Decimal("6.00"), Decimal("90.00"), AcademicStandingStatus.APPROVED, RiskLevel.LOW, False),
            (Decimal("5.99"), Decimal("6.00"), Decimal("90.00"), AcademicStandingStatus.IN_RECOVERY, RiskLevel.MODERATE, True),
            (Decimal("4.00"), Decimal("6.00"), Decimal("90.00"), AcademicStandingStatus.IN_RECOVERY, RiskLevel.MODERATE, True),
            (Decimal("3.99"), Decimal("6.00"), Decimal("90.00"), AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, True),
            # Cruzamento com frequência crítica (< 75%) e preventiva (< 78%)
            (Decimal("10.00"), Decimal("6.00"), Decimal("74.99"), AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, False),
            (Decimal("9.00"), Decimal("6.00"), Decimal("75.00"), AcademicStandingStatus.APPROVED, RiskLevel.HIGH, False),
            (Decimal("5.50"), Decimal("6.00"), Decimal("77.50"), AcademicStandingStatus.AT_RISK, RiskLevel.HIGH, True),
            # Sem notas lançadas ainda (None)
            (None, Decimal("6.00"), None, AcademicStandingStatus.IN_RECOVERY, RiskLevel.LOW, False),
            (None, Decimal("6.00"), Decimal("100.00"), AcademicStandingStatus.IN_RECOVERY, RiskLevel.LOW, False),
            (None, Decimal("6.00"), Decimal("70.00"), AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, False),
        ],
    )
    def test_classify_academic_standing_matrix(
        self,
        average: Decimal | None,
        passing_score: Decimal,
        attendance_rate: Decimal | None,
        expected_status: AcademicStandingStatus,
        expected_risk: RiskLevel,
        expected_below: bool,
    ) -> None:
        status_val, risk_val, is_below = classify_academic_standing(
            average,
            passing_score=passing_score,
            attendance_rate=attendance_rate,
        )
        assert status_val == expected_status
        assert risk_val == expected_risk
        assert is_below is expected_below


class TestAttendanceMathAndEdgeCases:
    """Valida regras matemáticas de frequência (75% mínimo legal / 78% alerta preventivo) e casos de borda."""

    def test_zero_lessons_given_avoids_zero_division_and_returns_100_percent(self) -> None:
        """Caso de borda: 0 aulas ministradas -> 100.00% sem erro de divisão por zero."""
        metrics = compute_attendance_margin_metrics(
            total_hours=0,
            attended_hours=0,
            absent_hours=0,
            planned_hours=40,
        )
        assert metrics["attendance_percentage"] == Decimal("100.00")
        assert metrics["is_critical"] is False
        assert metrics["risk_level"] == RiskLevel.LOW
        assert metrics["max_allowed_absent_hours"] == Decimal("0.00")
        assert metrics["remaining_absent_hours_margin"] == Decimal("0.00")
        assert metrics["planned_max_allowed_absent_hours"] == Decimal("10.00")
        assert metrics["planned_remaining_absent_hours_margin"] == Decimal("10.00")
        assert metrics["percentage_margin_to_limit"] == Decimal("25.00")

    def test_hundred_percent_absences_returns_zero_percent_critical_risk(self) -> None:
        """Caso de borda: 100% de faltas -> 0.00%, is_critical=True, RiskLevel.CRITICAL e margem 0.00."""
        metrics = compute_attendance_margin_metrics(
            total_hours=20,
            attended_hours=0,
            absent_hours=20,
            planned_hours=40,
        )
        assert metrics["attendance_percentage"] == Decimal("0.00")
        assert metrics["is_critical"] is True
        assert metrics["risk_level"] == RiskLevel.CRITICAL
        assert metrics["max_allowed_absent_hours"] == Decimal("5.00")
        assert metrics["remaining_absent_hours_margin"] == Decimal("0.00")
        assert metrics["planned_remaining_absent_hours_margin"] == Decimal("0.00")
        assert metrics["percentage_margin_to_limit"] == Decimal("-75.00")

    @pytest.mark.parametrize(
        ("rate", "expected_critical", "expected_risk"),
        [
            (Decimal("0.00"), True, RiskLevel.CRITICAL),
            (Decimal("74.99"), True, RiskLevel.CRITICAL),
            (Decimal("75.00"), True, RiskLevel.HIGH),
            (Decimal("77.99"), True, RiskLevel.HIGH),
            (Decimal("78.00"), False, RiskLevel.LOW),
            (Decimal("100.00"), False, RiskLevel.LOW),
        ],
    )
    def test_attendance_risk_thresholds(
        self,
        rate: Decimal,
        expected_critical: bool,
        expected_risk: RiskLevel,
    ) -> None:
        is_critical, risk = evaluate_attendance_risk_level(rate)
        assert is_critical is expected_critical
        assert risk == expected_risk


class TestDynamicLateStatusAndClosedPeriodGuard:
    """Valida transição dinâmica PENDING -> LATE e bloqueio de período encerrado."""

    def test_resolve_effective_submission_status_marks_expired_pending_as_late(self) -> None:
        now = datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
        past_due = now - timedelta(hours=1)
        future_due = now + timedelta(days=2)

        sub_pending_expired = SimpleNamespace(status=SubmissionStatus.PENDING)
        sub_pending_future = SimpleNamespace(status=SubmissionStatus.PENDING)
        sub_evaluated_past = SimpleNamespace(status=SubmissionStatus.EVALUATED)
        sub_submitted_past = SimpleNamespace(status=SubmissionStatus.SUBMITTED)

        assert (
            PracticalTaskService.resolve_effective_submission_status(
                sub_pending_expired,  # type: ignore[arg-type]
                due_date=past_due,
                reference_now=now,
            )
            == SubmissionStatus.LATE
        )
        assert (
            PracticalTaskService.resolve_effective_submission_status(
                sub_pending_future,  # type: ignore[arg-type]
                due_date=future_due,
                reference_now=now,
            )
            == SubmissionStatus.PENDING
        )
        assert (
            PracticalTaskService.resolve_effective_submission_status(
                sub_evaluated_past,  # type: ignore[arg-type]
                due_date=past_due,
                reference_now=now,
            )
            == SubmissionStatus.EVALUATED
        )
        assert (
            PracticalTaskService.resolve_effective_submission_status(
                sub_submitted_past,  # type: ignore[arg-type]
                due_date=past_due,
                reference_now=now,
            )
            == SubmissionStatus.SUBMITTED
        )

    def test_raise_if_class_period_closed_blocks_completed_and_archived(self) -> None:
        for closed_status in (ClassStatus.COMPLETED, ClassStatus.ARCHIVED):
            fake_class = SimpleNamespace(status=closed_status)
            with pytest.raises(UnprocessableEntityException) as exc_info:
                raise_if_class_period_closed(fake_class)  # type: ignore[arg-type]
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == CLASS_PERIOD_CLOSED_ERROR_CODE
            assert exc_info.value.message == CLASS_PERIOD_CLOSED_MESSAGE

        for open_status in (ClassStatus.ACTIVE, ClassStatus.PLANNING):
            fake_open_class = SimpleNamespace(status=open_status)
            raise_if_class_period_closed(fake_open_class)  # type: ignore[arg-type]
