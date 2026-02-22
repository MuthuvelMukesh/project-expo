"""
CampusIQ — Inference Engine
Load trained model, predict grades, and generate SHAP explanations.

Usage (standalone test):
    cd backend
    python -m app.ml.predict
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from app.ml.features import (
    FEATURE_COLS, FEATURE_NAMES, prepare_single_record,
    score_to_grade, score_to_risk, risk_level, compute_features_from_db,
)

# ─── Paths ──────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "grade_predictor.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")

# ─── Singleton Model Cache ──────────────────────────────────

_model = None
_explainer = None


def load_model():
    """Load the grade prediction model (cached singleton)."""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run `python -m app.ml.train` first."
        )

    _model = joblib.load(MODEL_PATH)
    return _model


def get_explainer():
    """Get or create a SHAP TreeExplainer (cached singleton)."""
    global _explainer
    if _explainer is not None:
        return _explainer

    try:
        import shap
        model = load_model()
        _explainer = shap.TreeExplainer(model)
        return _explainer
    except ImportError:
        print("⚠️  SHAP not installed. Explainability disabled.")
        return None
    except Exception as e:
        print(f"⚠️  SHAP initialization failed: {e}")
        return None


def predict_grade(features: dict) -> dict:
    """
    Predict grade and risk for a single student-course record.

    Args:
        features: Dict with keys matching FEATURE_COLS

    Returns:
        {
            "predicted_score": float,
            "predicted_grade": str,
            "risk_score": float,
            "risk_level": str,
            "confidence": float,
            "factors": [...],
        }
    """
    model = load_model()

    # Prepare features
    X = prepare_single_record(features)

    # Predict
    predicted_score = float(model.predict(X)[0])
    predicted_score = max(0.0, min(100.0, predicted_score))

    grade = score_to_grade(predicted_score)
    risk = score_to_risk(predicted_score)

    # Confidence from prediction variance (simple heuristic)
    # Use tree variance if available, else static
    try:
        # Get predictions from all trees
        leaf_preds = []
        for booster_idx in range(model.n_estimators):
            tree_pred = model.predict(X, iteration_range=(0, booster_idx + 1))
            leaf_preds.append(tree_pred[0])
        variance = np.var(leaf_preds[-50:]) if len(leaf_preds) >= 50 else np.var(leaf_preds)
        confidence = max(0.5, min(0.99, 1.0 - (variance / 500.0)))
    except Exception:
        confidence = 0.85

    # SHAP explanations
    factors = generate_shap_factors(X, features)

    return {
        "predicted_score": round(predicted_score, 1),
        "predicted_grade": grade,
        "risk_score": risk,
        "risk_level": risk_level(risk),
        "confidence": round(confidence, 3),
        "factors": factors,
    }


def generate_shap_factors(X: pd.DataFrame, raw_features: dict) -> list:
    """
    Generate SHAP-based explanation factors.

    Returns a list sorted by absolute impact (descending):
    [
        {"factor": "Attendance Rate", "impact": 0.23, "value": "82.5%"},
        ...
    ]
    """
    explainer = get_explainer()

    if explainer is not None:
        try:
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            shap_array = shap_values.flatten() if hasattr(shap_values, 'flatten') else np.array(shap_values).flatten()

            factors = []
            for i, col in enumerate(FEATURE_COLS):
                impact = float(shap_array[i])
                value = raw_features.get(col, 0)

                # Format value for display
                display_value = _format_feature_value(col, value)

                factors.append({
                    "factor": FEATURE_NAMES.get(col, col),
                    "impact": round(impact, 3),
                    "value": display_value,
                })

            # Sort by absolute impact (highest first)
            factors.sort(key=lambda f: abs(f["impact"]), reverse=True)
            return factors[:6]  # Top 6 factors

        except Exception as e:
            print(f"⚠️  SHAP computation failed: {e}")

    # Fallback: use feature importance from model
    return _fallback_factors(X, raw_features)


def _fallback_factors(X: pd.DataFrame, raw_features: dict) -> list:
    """Fallback explanation using model feature importances."""
    try:
        model = load_model()
        importances = model.feature_importances_

        factors = []
        for i, col in enumerate(FEATURE_COLS):
            value = raw_features.get(col, 0)
            # Approximate impact direction from value relative to a "average"
            avg_benchmarks = {
                "attendance_pct": 75, "assignment_submission_rate": 70,
                "assignment_avg_score": 65, "quiz_avg": 60,
                "lab_pct": 70, "midterm_score": 55,
                "cgpa": 7.0, "study_hours_per_week": 12,
                "credits": 4, "has_scholarship": 0.3,
                "extracurricular_hours": 5, "commute_time_mins": 30,
            }
            benchmark = avg_benchmarks.get(col, 50)
            direction = 1 if value >= benchmark else -1
            impact = float(importances[i]) * direction

            factors.append({
                "factor": FEATURE_NAMES.get(col, col),
                "impact": round(impact, 3),
                "value": _format_feature_value(col, value),
            })

        factors.sort(key=lambda f: abs(f["impact"]), reverse=True)
        return factors[:6]
    except Exception:
        return []


def _format_feature_value(col: str, value) -> str:
    """Format feature value for human-readable display."""
    pct_cols = {"attendance_pct", "assignment_submission_rate", "lab_pct"}
    if col in pct_cols:
        return f"{value}%"
    elif col == "cgpa":
        return f"{value}/10"
    elif col == "has_scholarship":
        return "Yes" if value else "No"
    elif col in {"study_hours_per_week", "extracurricular_hours", "commute_time_mins"}:
        return str(int(value))
    return str(round(value, 1))


def predict_batch(records: list[dict]) -> list[dict]:
    """Predict grades for multiple student-course records."""
    return [predict_grade(r) for r in records]


def get_model_metadata() -> dict:
    """Load model performance metadata."""
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH) as f:
            return json.load(f)
    return {"error": "Model metadata not found. Train the model first."}


# ─── Standalone Test ────────────────────────────────────────

def _test():
    """Run a quick test with sample data."""
    print("\n🔮 CampusIQ — Inference Test")
    print("=" * 60)

    # Test with a few profiles
    profiles = [
        ("High performer", compute_features_from_db(
            attendance_pct=92, assignment_submission_rate=95,
            assignment_avg_score=88, quiz_avg=85, lab_pct=90,
            midterm_score=82, cgpa=9.2, study_hours_per_week=20,
            credits=4, has_scholarship=True,
        )),
        ("Average student", compute_features_from_db(
            attendance_pct=72, assignment_submission_rate=68,
            assignment_avg_score=60, quiz_avg=55, lab_pct=65,
            midterm_score=50, cgpa=6.5, study_hours_per_week=8,
            credits=4,
        )),
        ("At-risk student", compute_features_from_db(
            attendance_pct=45, assignment_submission_rate=40,
            assignment_avg_score=35, quiz_avg=30, lab_pct=40,
            midterm_score=28, cgpa=4.5, study_hours_per_week=3,
            credits=4,
        )),
    ]

    for name, features in profiles:
        result = predict_grade(features)
        print(f"\n👤 {name}:")
        print(f"   Grade: {result['predicted_grade']} (score: {result['predicted_score']})")
        print(f"   Risk:  {result['risk_level']} ({result['risk_score']})")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Top factors:")
        for f in result["factors"][:4]:
            arrow = "↑" if f["impact"] > 0 else "↓"
            print(f"     {arrow} {f['factor']:25s} impact={f['impact']:+.3f}  value={f['value']}")

    # Print model metadata
    meta = get_model_metadata()
    if "metrics" in meta:
        print(f"\n📋 Model: {meta['model_type']} | R²={meta['metrics']['r2']:.4f} | "
              f"Grade Acc={meta['metrics']['grade_accuracy']:.1%}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    _test()
