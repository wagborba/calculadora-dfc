"""Friction coefficient calculation logic for the DFC Framework."""

from dataclasses import dataclass, field
from datetime import datetime

from .data import DIMENSIONS, Dimension


CLASSIFICATION_BANDS: list[tuple[float, str]] = [
    (0.20, "Fricção irrisória"),
    (0.40, "Fricção baixa"),
    (0.60, "Fricção moderada"),
    (0.80, "Fricção alta"),
    (1.01, "Fricção crítica"),
]


@dataclass
class DimensionResult:
    """Computed result for a single dimension.

    Attributes:
        dimension_id: Identifier of the evaluated dimension.
        dimension_name: Display name of the dimension.
        weight: Weight of the dimension in the final CF.
        scores: Mapping of parameter_id to the assigned score (1–5).
        score_normalized: Normalized score between 0.0 and 1.0.
        skipped: True if the entire dimension was skipped.
    """

    dimension_id: str
    dimension_name: str
    weight: float
    scores: dict[str, int] = field(default_factory=dict)
    score_normalized: float = 0.0
    skipped: bool = False


@dataclass
class EvaluationResult:
    """Full evaluation result including all dimensions and the final CF.

    Attributes:
        product_name: Name of the evaluated product.
        evaluated_at: Timestamp of the evaluation.
        cf: Final Friction Coefficient (0.0–1.0).
        classification: Verbal classification of the CF.
        dimensions: List of per-dimension results.
    """

    product_name: str
    evaluated_at: datetime
    cf: float
    classification: str
    dimensions: list[DimensionResult] = field(default_factory=list)


def classify(cf: float) -> str:
    """Return the verbal classification for a given CF value.

    Args:
        cf: Friction Coefficient between 0.0 and 1.0.

    Returns:
        A string label describing the friction level.
    """
    for threshold, label in CLASSIFICATION_BANDS:
        if cf < threshold:
            return label
    return "Fricção crítica"


def compute_dimension_score(scores: dict[str, int], n_params: int) -> float:
    """Compute the normalised score for one dimension.

    Args:
        scores: Mapping of parameter_id to score (1–5) for answered params.
        n_params: Total number of parameters in the dimension (answered only).

    Returns:
        Normalised score between 0.0 and 1.0. Returns 0.0 if no scores.
    """
    if not scores or n_params == 0:
        return 0.0
    return sum(scores.values()) / (n_params * 5)


def compute_cf(dimension_results: list[DimensionResult]) -> float:
    """Compute the final CF from a list of dimension results.

    Only non-skipped dimensions contribute. The result is normalised by the
    sum of participating weights so that partial evaluations remain valid.

    Args:
        dimension_results: List of DimensionResult objects.

    Returns:
        CF value between 0.0 and 1.0. Returns 0.0 if all dims were skipped.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for dr in dimension_results:
        if dr.skipped or not dr.scores:
            continue
        weighted_sum += dr.score_normalized * dr.weight
        total_weight += dr.weight

    if total_weight == 0.0:
        return 0.0

    return weighted_sum / total_weight


def build_evaluation(
    product_name: str,
    raw_scores: dict[str, dict[str, int]],
    skipped_dimensions: set[str],
    evaluated_at: datetime | None = None,
) -> EvaluationResult:
    """Build a full EvaluationResult from raw collected scores.

    Args:
        product_name: Name of the evaluated product.
        raw_scores: Mapping of dimension_id → {parameter_id: score}.
        skipped_dimensions: Set of dimension_ids that were entirely skipped.
        evaluated_at: Optional timestamp; defaults to now.

    Returns:
        A fully populated EvaluationResult.
    """
    if evaluated_at is None:
        evaluated_at = datetime.now()

    dim_results: list[DimensionResult] = []

    for dim in DIMENSIONS:
        skipped = dim.id in skipped_dimensions
        scores = raw_scores.get(dim.id, {})
        n_answered = len(scores)
        norm_score = compute_dimension_score(scores, n_answered) if not skipped else 0.0

        dim_results.append(
            DimensionResult(
                dimension_id=dim.id,
                dimension_name=dim.name,
                weight=dim.weight,
                scores=scores,
                score_normalized=norm_score,
                skipped=skipped,
            )
        )

    cf = compute_cf(dim_results)
    classification = classify(cf)

    return EvaluationResult(
        product_name=product_name,
        evaluated_at=evaluated_at,
        cf=cf,
        classification=classification,
        dimensions=dim_results,
    )
