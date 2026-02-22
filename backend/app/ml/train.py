"""
CampusIQ — XGBoost Training Pipeline
Train, evaluate, and save the grade prediction model.

Usage:
    cd backend
    python -m app.ml.train
"""

import os
import time
import json
import numpy as np
import pandas as pd
import joblib

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score
)

from app.ml.features import (
    prepare_training_data, FEATURE_COLS, FEATURE_NAMES,
    score_to_grade, GRADE_TO_SCORE,
)

# ─── Paths ──────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TRAINING_DATA_PATH = os.path.join(DATA_DIR, "training_data.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "grade_predictor.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


def load_data() -> pd.DataFrame:
    """Load training data. Generate if not found."""
    if not os.path.exists(TRAINING_DATA_PATH):
        print("📂 Training data not found. Generating synthetic data...")
        from app.ml.seed_data import main as generate_data
        generate_data()

    df = pd.read_csv(TRAINING_DATA_PATH)
    print(f"📊 Loaded {len(df)} records from {TRAINING_DATA_PATH}")
    return df


def train_model():
    """Full training pipeline: load → split → train → evaluate → save."""
    print("\n🧠 CampusIQ — ML Training Pipeline")
    print("=" * 60)
    start = time.time()

    # 1. Load data
    df = load_data()
    X, y = prepare_training_data(df)
    print(f"✅ Features: {X.shape[1]} | Samples: {X.shape[0]}")

    # 2. Train/test split (80/20, stratified isn't possible with regression)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"✅ Train: {len(X_train)} | Test: {len(X_test)}")

    # 3. XGBoost model
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )

    print("\n🏋️ Training XGBoost Regressor...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 4. Evaluate
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Grade accuracy (convert numeric predictions to letter grades)
    true_grades = [score_to_grade(s) for s in y_test]
    pred_grades = [score_to_grade(s) for s in y_pred]
    grade_accuracy = sum(t == p for t, p in zip(true_grades, pred_grades)) / len(true_grades)

    # Within ±1 grade accuracy
    grade_order = ["F", "D", "C", "B", "B+", "A", "A+"]
    within_one = sum(
        abs(grade_order.index(t) - grade_order.index(p)) <= 1
        for t, p in zip(true_grades, pred_grades)
    ) / len(true_grades)

    print(f"\n📈 Model Performance:")
    print(f"   MAE:             {mae:.2f} points")
    print(f"   RMSE:            {rmse:.2f} points")
    print(f"   R² Score:        {r2:.4f}")
    print(f"   Grade Accuracy:  {grade_accuracy:.1%}")
    print(f"   ±1 Grade Acc:    {within_one:.1%}")

    # 5. Feature importance
    importance = dict(zip(FEATURE_COLS, model.feature_importances_))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    print(f"\n🔑 Feature Importance (top 8):")
    for feat, imp in sorted_imp[:8]:
        bar = "█" * int(imp * 50)
        name = FEATURE_NAMES.get(feat, feat)
        print(f"   {name:25s} {imp:.4f} {bar}")

    # 6. Cross-validation
    print(f"\n🔄 5-Fold Cross Validation...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"   CV R² Scores: {cv_scores.round(4)}")
    print(f"   Mean R²:      {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # 7. Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Model saved → {MODEL_PATH}")

    # 8. Save metadata
    metadata = {
        "model_type": "XGBRegressor",
        "n_estimators": 200,
        "max_depth": 6,
        "n_features": len(FEATURE_COLS),
        "feature_columns": FEATURE_COLS,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "grade_accuracy": round(grade_accuracy, 4),
            "within_one_grade": round(within_one, 4),
            "cv_r2_mean": round(cv_scores.mean(), 4),
            "cv_r2_std": round(cv_scores.std(), 4),
        },
        "feature_importance": {
            FEATURE_NAMES.get(k, k): round(v, 4) for k, v in sorted_imp
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"📋 Metadata saved → {METADATA_PATH}")

    elapsed = time.time() - start
    print(f"\n⏱️  Total time: {elapsed:.1f}s")
    print("=" * 60)
    print("🎉 Training complete! Model ready for inference.")

    return model, metadata


if __name__ == "__main__":
    train_model()
