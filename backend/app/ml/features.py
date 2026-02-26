"""
CampusIQ — Feature Engineering Pipeline
Prepares raw student data for ML model training and inference.
"""

import pandas as pd
import numpy as np

# Feature columns the model will be trained on (order matters for SHAP)
FEATURE_COLS = [
    "attendance_pct",
    "assignment_submission_rate",
    "assignment_avg_score",
    "quiz_avg",
    "lab_pct",
    "midterm_score",
    "cgpa",
    "study_hours_per_week",
    "credits",
    "has_scholarship",
    "extracurricular_hours",
    "commute_time_mins",
]

# Human-readable names for SHAP display
FEATURE_NAMES = {
    "attendance_pct": "Attendance Rate",
    "assignment_submission_rate": "Assignment Submission",
    "assignment_avg_score": "Assignment Score",
    "quiz_avg": "Quiz Average",
    "lab_pct": "Lab Participation",
    "midterm_score": "Mid-term Score",
    "cgpa": "Cumulative GPA",
    "study_hours_per_week": "Study Hours/Week",
    "credits": "Course Credits",
    "has_scholarship": "Scholarship Status",
    "extracurricular_hours": "Extracurricular Hours",
    "commute_time_mins": "Commute Time (min)",
}

# Grade → numeric (target for regression)
GRADE_TO_SCORE = {
    "A+": 95, "A": 85, "B+": 75, "B": 65, "C": 55, "D": 45, "F": 25
}

SCORE_TO_GRADE_THRESHOLDS = [
    (90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (50, "C"), (40, "D"), (0, "F")
]


def score_to_grade(score: float) -> str:
    """Convert a numeric score to a letter grade."""
    for threshold, grade in SCORE_TO_GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def score_to_risk(score: float) -> float:
    """Convert a predicted score (0–100) to a risk score (0–1).
    Lower score = higher risk.
    """
    return round(max(0.0, min(1.0, 1.0 - (score / 100.0))), 3)


def risk_level(risk: float) -> str:
    """Categorize risk score."""
    if risk >= 0.6:
        return "high"
    elif risk >= 0.35:
        return "moderate"
    return "low"


def prepare_training_data(df: pd.DataFrame) -> tuple:
    """
    Prepare features (X) and target (y) from raw training data.

    Returns:
        X: pd.DataFrame with feature columns
        y: np.ndarray with numeric target scores
    """
    df = df.copy()

    # Convert boolean to int
    if "has_scholarship" in df.columns:
        df["has_scholarship"] = df["has_scholarship"].astype(int)

    # Encode grade to numeric target
    y = df["grade"].map(GRADE_TO_SCORE).values.astype(float)

    # Select features
    X = df[FEATURE_COLS].copy()

    # Handle missing values
    X = X.fillna(X.median())

    return X, y


def prepare_single_record(record: dict) -> pd.DataFrame:
    """
    Prepare a single student-course record for inference.

    Args:
        record: Dictionary with feature values

    Returns:
        pd.DataFrame with one row, ready for model.predict()
    """
    row = {}
    for col in FEATURE_COLS:
        val = record.get(col, 0)
        if col == "has_scholarship":
            val = int(bool(val))
        row[col] = [val]

    return pd.DataFrame(row)


def compute_features_from_db(
    attendance_pct: float,
    cgpa: float,
    assignment_submission_rate: float = None,
    assignment_avg_score: float = None,
    quiz_avg: float = None,
    lab_pct: float = None,
    midterm_score: float = None,
    study_hours_per_week: int = None,
    credits: int = 4,
    has_scholarship: bool = False,
    extracurricular_hours: int = None,
    commute_time_mins: int = None,
) -> dict:
    """
    Construct a feature dict from individual values.
    Tracks which features have real data vs unavailable (None).
    
    Real data (always available):
    - attendance_pct: From Attendance table
    - cgpa: From Student table
    
    Planned for v2 (tables not yet implemented):
    - assignment_submission_rate, assignment_avg_score
    - quiz_avg, lab_pct, midterm_score
    - study_hours_per_week, extracurricular_hours, commute_time_mins
    """
    features = {
        "attendance_pct": attendance_pct,
        "assignment_submission_rate": assignment_submission_rate,
        "assignment_avg_score": assignment_avg_score,
        "quiz_avg": quiz_avg,
        "lab_pct": lab_pct,
        "midterm_score": midterm_score,
        "cgpa": cgpa,
        "study_hours_per_week": study_hours_per_week,
        "credits": credits,
        "has_scholarship": int(has_scholarship) if has_scholarship is not None else 0,
        "extracurricular_hours": extracurricular_hours,
        "commute_time_mins": commute_time_mins,
    }
    
    # Track missing features
    missing = [k for k, v in features.items() if v is None and k not in ("has_scholarship",)]
    total_features = len(FEATURE_COLS)
    available_features = total_features - len(missing)
    
    return {
        "features": features,
        "missing_features": missing,
        "data_completeness": available_features / total_features,
        "is_estimated": len(missing) > 0,
    }
