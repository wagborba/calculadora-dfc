"""Flask web application for the DFC Calculator."""

import io
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, render_template, request, send_file

from dfc.calculator import (
    DimensionResult,
    EvaluationResult,
    build_evaluation,
)
from dfc.data import DIMENSIONS
from dfc.exporter import export_json, export_txt

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dimensions_to_json() -> str:
    """Serialise DIMENSIONS list to a JSON string for the frontend."""
    dims = []
    for dim in DIMENSIONS:
        dims.append(
            {
                "id": dim.id,
                "name": dim.name,
                "weight": dim.weight,
                "parameters": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                    }
                    for p in dim.parameters
                ],
            }
        )
    return json.dumps(dims, ensure_ascii=False)


def _result_to_dict(result: EvaluationResult) -> dict:
    """Serialise an EvaluationResult to a plain dict."""
    return {
        "product_name": result.product_name,
        "evaluated_at": result.evaluated_at.isoformat(),
        "cf": round(result.cf, 4),
        "classification": result.classification,
        "dimensions": [
            {
                "dimension_id": dr.dimension_id,
                "dimension_name": dr.dimension_name,
                "weight": dr.weight,
                "scores": dr.scores,
                "score_normalized": round(dr.score_normalized, 4),
                "skipped": dr.skipped,
            }
            for dr in result.dimensions
        ],
    }


def _dict_to_result(data: dict) -> EvaluationResult:
    """Deserialise a plain dict back to an EvaluationResult."""
    dims = [
        DimensionResult(
            dimension_id=dr["dimension_id"],
            dimension_name=dr["dimension_name"],
            weight=dr["weight"],
            scores={k: int(v) for k, v in dr.get("scores", {}).items()},
            score_normalized=dr.get("score_normalized", 0.0),
            skipped=dr.get("skipped", False),
        )
        for dr in data.get("dimensions", [])
    ]
    return EvaluationResult(
        product_name=data["product_name"],
        evaluated_at=datetime.fromisoformat(data["evaluated_at"]),
        cf=data["cf"],
        classification=data["classification"],
        dimensions=dims,
    )


def _build_comparison(a: dict, b: dict) -> dict:
    """Build a comparison dict with deltas and directional arrows."""
    _THRESHOLD = 0.005

    def arrow(delta: float) -> str:
        if delta > _THRESHOLD:
            return "↑"
        if delta < -_THRESHOLD:
            return "↓"
        return "→"

    cf_a = a["cf"]
    cf_b = b["cf"]
    delta_cf = cf_b - cf_a

    dims_b = {d["id"]: d for d in b["dimensions"]}

    dimension_rows = []
    for dim_a in a["dimensions"]:
        dim_b = dims_b.get(dim_a["id"])
        row = {
            "id": dim_a["id"],
            "name": dim_a["name"],
            "score_a": None if dim_a["skipped"] else dim_a["score_normalized"],
            "score_b": None,
            "delta": None,
            "arrow": "→",
            "skipped_a": dim_a["skipped"],
            "skipped_b": True,
        }
        if dim_b is not None:
            row["skipped_b"] = dim_b["skipped"]
            row["score_b"] = None if dim_b["skipped"] else dim_b["score_normalized"]
            if not dim_a["skipped"] and not dim_b["skipped"]:
                delta = dim_b["score_normalized"] - dim_a["score_normalized"]
                row["delta"] = round(delta, 4)
                row["arrow"] = arrow(delta)
        dimension_rows.append(row)

    return {
        "a": {
            "product_name": a["product_name"],
            "evaluated_at": a["evaluated_at"],
            "cf": cf_a,
            "classification": a["classification"],
        },
        "b": {
            "product_name": b["product_name"],
            "evaluated_at": b["evaluated_at"],
            "cf": cf_b,
            "classification": b["classification"],
        },
        "cf_delta": round(delta_cf, 4),
        "cf_arrow": arrow(delta_cf),
        "dimensions": dimension_rows,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", dimensions_json=_dimensions_to_json())


@app.route("/compare")
def compare_page():
    return render_template("compare.html")


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "JSON payload required"}), 400

    product_name = payload.get("product_name", "").strip()
    if not product_name:
        return jsonify({"error": "product_name is required"}), 400

    raw_scores: dict[str, dict[str, int]] = {}
    for dim_id, params in payload.get("scores", {}).items():
        raw_scores[dim_id] = {
            p_id: int(score)
            for p_id, score in params.items()
            if score is not None
        }

    skipped_dimensions = set(payload.get("skipped_dimensions", []))

    result = build_evaluation(
        product_name=product_name,
        raw_scores=raw_scores,
        skipped_dimensions=skipped_dimensions,
    )
    return jsonify(_result_to_dict(result))


@app.route("/api/export/json", methods=["POST"])
def api_export_json():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400

    result = _dict_to_result(data)

    with tempfile.TemporaryDirectory() as tmp:
        path = export_json(result, output_dir=Path(tmp))
        content = path.read_bytes()

    filename = path.name
    return send_file(
        io.BytesIO(content),
        mimetype="application/json",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/export/txt", methods=["POST"])
def api_export_txt():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON payload required"}), 400

    result = _dict_to_result(data)

    with tempfile.TemporaryDirectory() as tmp:
        path = export_txt(result, output_dir=Path(tmp))
        content = path.read_bytes()

    filename = path.name
    return send_file(
        io.BytesIO(content),
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/compare", methods=["POST"])
def api_compare():
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")

    if not file_a or not file_b:
        return jsonify({"error": "file_a and file_b are required"}), 400

    try:
        data_a = json.loads(file_a.read().decode("utf-8"))
        data_b = json.loads(file_b.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return jsonify({"error": f"Invalid JSON file: {exc}"}), 400

    comparison = _build_comparison(data_a, data_b)
    return jsonify(comparison)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
