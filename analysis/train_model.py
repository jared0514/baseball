"""
MLB Match Outcome Prediction Model
Uses Random Forest to predict game outcomes based on aggregated features.
Includes SHAP explainability analysis and comprehensive metrics reporting.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import shap
from sqlalchemy import create_engine
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, roc_auc_score,
    confusion_matrix, precision_score, recall_score, f1_score,
    roc_curve
)

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "mlb.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")


def load_game_data():
    """Extract game data and basic stats from the database."""
    print("Loading data from database...")
    engine = create_engine(DATABASE_URL)

    query = """
    SELECT 
        g.id, g.game_date, g.home_team_id, g.away_team_id,
        g.home_score, g.away_score,
        ts_home.win_pct as home_win_pct,
        ts_home.run_diff as home_run_diff,
        ts_home.runs_scored as home_rs,
        ts_home.runs_allowed as home_ra,
        ts_away.win_pct as away_win_pct,
        ts_away.run_diff as away_run_diff,
        ts_away.runs_scored as away_rs,
        ts_away.runs_allowed as away_ra
    FROM games g
    JOIN team_standings ts_home ON g.home_team_id = ts_home.team_id
    JOIN team_standings ts_away ON g.away_team_id = ts_away.team_id
    WHERE g.status = 'Final' AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL
    ORDER BY g.game_date ASC
    """

    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} games.")
    return df


def prepare_features(df):
    """Create features and labels for the model."""
    if len(df) == 0:
        return pd.DataFrame(), pd.Series()

    # Feature Engineering
    df['win_pct_diff'] = df['home_win_pct'] - df['away_win_pct']
    df['run_diff_diff'] = df['home_run_diff'] - df['away_run_diff']
    df['home_scoring_rate'] = df['home_rs'] / (df['home_rs'] + df['home_ra']).replace(0, 1)
    df['away_scoring_rate'] = df['away_rs'] / (df['away_rs'] + df['away_ra']).replace(0, 1)
    df['scoring_rate_diff'] = df['home_scoring_rate'] - df['away_scoring_rate']
    df['home_advantage'] = 1  # Home field advantage indicator

    # Label: 1 if Home Team wins, 0 if Away Team wins
    df['home_win'] = (df['home_score'] > df['away_score']).astype(int)

    features = [
        'home_win_pct', 'away_win_pct', 'win_pct_diff',
        'home_run_diff', 'away_run_diff', 'run_diff_diff',
        'home_scoring_rate', 'away_scoring_rate', 'scoring_rate_diff',
        'home_advantage',
    ]

    X = df[features].copy()
    y = df['home_win'].copy()

    return X, y


def train_baseline_model(X, y):
    """Train a simple Logistic Regression baseline."""
    print("\n" + "=" * 60)
    print("Training Baseline Model (Logistic Regression)")
    print("=" * 60)

    tscv = TimeSeriesSplit(n_splits=5)

    accuracies = []
    all_y_true = []
    all_y_pred = []
    all_y_prob = []

    for fold, (train_index, test_index) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        probs = clf.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, preds)
        accuracies.append(acc)
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(preds.tolist())
        all_y_prob.extend(probs.tolist())

        print(f"  Fold {fold + 1}: Accuracy = {acc:.4f}")

    print(f"\n  Mean CV Accuracy: {np.mean(accuracies):.4f} (+/- {np.std(accuracies):.4f})")

    # Full classification report on pooled CV predictions
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_prob = np.array(all_y_prob)

    print("\n  Pooled Classification Report:")
    print(classification_report(all_y_true, all_y_pred,
                                target_names=["Away Win", "Home Win"]))

    auc = roc_auc_score(all_y_true, all_y_prob)
    print(f"  Pooled AUC-ROC: {auc:.4f}")

    # Train final model on full data
    final_model = LogisticRegression(max_iter=1000)
    final_model.fit(X, y)

    baseline_metrics = {
        "model": "LogisticRegression",
        "cv_accuracies": [round(a, 4) for a in accuracies],
        "mean_accuracy": round(np.mean(accuracies), 4),
        "std_accuracy": round(np.std(accuracies), 4),
        "pooled_auc_roc": round(auc, 4),
        "pooled_precision": round(precision_score(all_y_true, all_y_pred), 4),
        "pooled_recall": round(recall_score(all_y_true, all_y_pred), 4),
        "pooled_f1": round(f1_score(all_y_true, all_y_pred), 4),
    }

    return final_model, baseline_metrics


def train_advanced_model(X, y):
    """Train a Random Forest model with GridSearch and full metrics."""
    print("\n" + "=" * 60)
    print("Training Advanced Model (Random Forest)")
    print("=" * 60)

    tscv = TimeSeriesSplit(n_splits=5)

    rf = RandomForestClassifier(random_state=42)

    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 7, 10],
        'min_samples_split': [2, 5, 10]
    }

    grid = GridSearchCV(rf, param_grid, cv=tscv, scoring='accuracy',
                        n_jobs=-1, verbose=0)
    grid.fit(X, y)

    print(f"  Best parameters: {grid.best_params_}")
    print(f"  Best CV Accuracy: {grid.best_score_:.4f}")

    best_model = grid.best_estimator_

    # Detailed cross-validation evaluation with the best model
    accuracies = []
    all_y_true = []
    all_y_pred = []
    all_y_prob = []

    for fold, (train_index, test_index) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        fold_model = RandomForestClassifier(**grid.best_params_, random_state=42)
        fold_model.fit(X_train, y_train)
        preds = fold_model.predict(X_test)
        probs = fold_model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, preds)
        accuracies.append(acc)
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(preds.tolist())
        all_y_prob.extend(probs.tolist())

        print(f"  Fold {fold + 1}: Accuracy = {acc:.4f}")

    print(f"\n  Mean CV Accuracy: {np.mean(accuracies):.4f} (+/- {np.std(accuracies):.4f})")

    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_prob = np.array(all_y_prob)

    print("\n  Pooled Classification Report:")
    report_str = classification_report(all_y_true, all_y_pred,
                                       target_names=["Away Win", "Home Win"])
    print(report_str)

    auc = roc_auc_score(all_y_true, all_y_prob)
    print(f"  Pooled AUC-ROC: {auc:.4f}")

    # Confusion Matrix
    cm = confusion_matrix(all_y_true, all_y_pred)
    print(f"\n  Confusion Matrix:")
    print(f"    TN={cm[0][0]}  FP={cm[0][1]}")
    print(f"    FN={cm[1][0]}  TP={cm[1][1]}")

    # --- Save Model ---
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "rf_predictor.pkl")
    joblib.dump(best_model, model_path)
    print(f"\n  Model saved to: {model_path}")

    # Save feature names alongside model
    feature_names_path = os.path.join(MODELS_DIR, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(list(X.columns), f)

    # --- Save ROC Curve Plot ---
    os.makedirs(PLOTS_DIR, exist_ok=True)

    fpr, tpr, _ = roc_curve(all_y_true, all_y_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='#007AFF', lw=2, label=f'Random Forest (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--', label='Random Baseline')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('ROC Curve — MLB Game Outcome Prediction', fontsize=14)
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "roc_curve.png"), dpi=150)
    plt.close()
    print(f"  ROC curve saved to: {PLOTS_DIR}/roc_curve.png")

    # --- Save Confusion Matrix Plot ---
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set(xticks=[0, 1], yticks=[0, 1],
           xticklabels=["Away Win", "Home Win"],
           yticklabels=["Away Win", "Home Win"],
           xlabel="Predicted Label", ylabel="True Label",
           title="Confusion Matrix — Random Forest")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "confusion_matrix.png"), dpi=150)
    plt.close()
    print(f"  Confusion matrix saved to: {PLOTS_DIR}/confusion_matrix.png")

    # Build metrics dict
    rf_metrics = {
        "model": "RandomForest",
        "best_params": grid.best_params_,
        "cv_accuracies": [round(a, 4) for a in accuracies],
        "mean_accuracy": round(np.mean(accuracies), 4),
        "std_accuracy": round(np.std(accuracies), 4),
        "pooled_auc_roc": round(auc, 4),
        "pooled_precision": round(precision_score(all_y_true, all_y_pred), 4),
        "pooled_recall": round(recall_score(all_y_true, all_y_pred), 4),
        "pooled_f1": round(f1_score(all_y_true, all_y_pred), 4),
        "confusion_matrix": cm.tolist(),
    }

    return best_model, rf_metrics


def run_shap_analysis(model, X, feature_names):
    """Run SHAP explainability analysis on the trained Random Forest model."""
    print("\n" + "=" * 60)
    print("Running SHAP Explainability Analysis")
    print("=" * 60)

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Use a sample for SHAP if dataset is large
    sample_size = min(500, len(X))
    X_sample = X.sample(n=sample_size, random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # For binary classification, shap_values is a list of 2 arrays
    # We want class 1 (Home Win) SHAP values
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]
    else:
        shap_vals = shap_values

    # --- SHAP Summary Plot (Beeswarm) ---
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_vals, X_sample, feature_names=feature_names,
                      show=False, plot_size=(10, 6))
    plt.title("SHAP Feature Importance — Home Win Prediction", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "shap_summary.png"), dpi=150,
                bbox_inches='tight')
    plt.close()
    print(f"  SHAP summary plot saved to: {PLOTS_DIR}/shap_summary.png")

    # --- SHAP Bar Plot (Mean |SHAP|) ---
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_vals, X_sample, feature_names=feature_names,
                      plot_type="bar", show=False, plot_size=(10, 6))
    plt.title("Mean |SHAP| Feature Importance", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "shap_bar.png"), dpi=150,
                bbox_inches='tight')
    plt.close()
    print(f"  SHAP bar plot saved to: {PLOTS_DIR}/shap_bar.png")

    # --- Compute mean absolute SHAP values for API ---
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    # Flatten in case of multi-dimensional output
    if mean_abs_shap.ndim > 1:
        mean_abs_shap = mean_abs_shap.mean(axis=-1)
    mean_abs_shap = mean_abs_shap.flatten()
    # Build list of (name, value) pairs and sort by value descending
    importance_pairs = [(name, float(mean_abs_shap[i])) for i, name in enumerate(feature_names)]
    importance_pairs.sort(key=lambda x: -x[1])
    feature_importance = {name: round(val, 6) for name, val in importance_pairs}

    # Chinese labels for feature descriptions
    feature_labels_cn = {
        'home_win_pct': '主隊勝率',
        'away_win_pct': '客隊勝率',
        'win_pct_diff': '勝率差',
        'home_run_diff': '主隊得失分差',
        'away_run_diff': '客隊得失分差',
        'run_diff_diff': '得失分差之差',
        'home_scoring_rate': '主隊得分比率',
        'away_scoring_rate': '客隊得分比率',
        'scoring_rate_diff': '得分比率差',
        'home_advantage': '主場優勢',
    }

    shap_results = {
        "feature_importance": feature_importance,
        "feature_labels_cn": feature_labels_cn,
        "sample_size": sample_size,
        "total_features": len(feature_names),
    }

    # Save SHAP results JSON
    shap_path = os.path.join(MODELS_DIR, "shap_results.json")
    with open(shap_path, "w", encoding="utf-8") as f:
        json.dump(shap_results, f, ensure_ascii=False, indent=2)
    print(f"  SHAP results saved to: {shap_path}")

    return shap_results


def main():
    print("=" * 60)
    print("MLB Model Training Pipeline")
    print("=" * 60)

    df = load_game_data()

    if len(df) < 100:
        print("Not enough data to train model. Please fetch more games first.")
        return

    X, y = prepare_features(df)
    feature_names = list(X.columns)

    print(f"\nDataset: {len(X)} samples, {len(feature_names)} features")
    print(f"Home Win Rate: {y.mean():.3f} ({y.sum()}/{len(y)})")
    print(f"Features: {feature_names}")

    # Train models
    baseline_model, baseline_metrics = train_baseline_model(X, y)
    rf_model, rf_metrics = train_advanced_model(X, y)

    # SHAP analysis on the best model
    shap_results = run_shap_analysis(rf_model, X, feature_names)

    # Save all metrics to a single JSON for the API
    all_metrics = {
        "baseline": baseline_metrics,
        "random_forest": rf_metrics,
        "shap": shap_results,
        "dataset_info": {
            "total_games": len(X),
            "home_win_rate": round(float(y.mean()), 4),
            "features": feature_names,
        }
    }

    metrics_path = os.path.join(MODELS_DIR, "training_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    print(f"\n  All metrics saved to: {metrics_path}")

    print("\n" + "=" * 60)
    print("Training Pipeline Complete!")
    print("=" * 60)
    print(f"\n  Baseline (LR) Accuracy: {baseline_metrics['mean_accuracy']:.4f}")
    print(f"  Random Forest Accuracy: {rf_metrics['mean_accuracy']:.4f}")
    print(f"  Random Forest AUC-ROC:  {rf_metrics['pooled_auc_roc']:.4f}")
    print(f"\n  Top SHAP Features:")
    for feat, val in list(shap_results['feature_importance'].items())[:5]:
        label = shap_results['feature_labels_cn'].get(feat, feat)
        print(f"    {label} ({feat}): {val:.6f}")


if __name__ == "__main__":
    main()
