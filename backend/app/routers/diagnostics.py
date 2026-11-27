"""Router dedicado para endpoints de Diagnósticos Explicáveis e Discrepâncias de Aprendizagem (EPIC-07 / BE-037 / BE-038)."""

from app.routers.self_assessments import (
    evaluate_class_explainable_diagnostics,
    get_diagnostic_discrepancies,
    router,
)

__all__ = [
    "evaluate_class_explainable_diagnostics",
    "get_diagnostic_discrepancies",
    "router",
]
