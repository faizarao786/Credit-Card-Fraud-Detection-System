# ============================================================
# CREDIT CARD FRAUD DETECTION - MODEL TRAINING
# ============================================================
# This file:
# 1. Loads creditcard.csv
# 2. Separates features and target
# 3. Splits data into training/testing sets
# 4. Trains a Random Forest model
# 5. Handles imbalanced fraud data
# 6. Evaluates the model
# 7. Saves the trained model as fraud_model.pkl
#
# IMPORTANT:
# The saved model is directly compatible with
# fraud_detection_model.py
# ============================================================


import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)


# ============================================================
# 1. FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "creditcard.csv"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "fraud_model.pkl"
)


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("=" * 65)
print("CREDIT CARD FRAUD DETECTION - MODEL TRAINING")
print("=" * 65)

print("\nLoading credit card dataset...")

if not os.path.exists(DATA_FILE):

    raise FileNotFoundError(
        "creditcard.csv was not found.\n"
        "Please place creditcard.csv in the project folder."
    )


df = pd.read_csv(DATA_FILE)


print("Dataset loaded successfully!")
print("Dataset shape:", df.shape)


# ============================================================
# 3. CHECK DATASET
# ============================================================

print("\nDataset columns:")
print(df.columns.tolist())


# ------------------------------------------------------------
# Make sure Class column exists
# ------------------------------------------------------------

if "Class" not in df.columns:

    raise ValueError(
        "The dataset must contain a 'Class' column."
    )


# ------------------------------------------------------------
# Display fraud distribution
# ------------------------------------------------------------

print("\nTransaction distribution:")

print(
    df["Class"].value_counts()
)


print("\nTransaction percentages:")

print(
    df["Class"].value_counts(
        normalize=True
    ).mul(100).round(4)
)


# ============================================================
# 4. REMOVE INVALID VALUES
# ============================================================

print("\nChecking missing values...")

missing_values = df.isnull().sum().sum()

print(
    "Total missing values:",
    missing_values
)


if missing_values > 0:

    print(
        "Removing rows containing missing values..."
    )

    df = df.dropna()


# ============================================================
# 5. SEPARATE FEATURES AND TARGET
# ============================================================

# Class:
# 0 = Normal transaction
# 1 = Fraud transaction

X = df.drop(
    "Class",
    axis=1
)

y = df["Class"]


# ============================================================
# 6. MAKE SURE FEATURES ARE CORRECT
# ============================================================

expected_features = (
    ["Time"]
    + [f"V{i}" for i in range(1, 29)]
    + ["Amount"]
)


missing_features = [
    column
    for column in expected_features
    if column not in X.columns
]


if missing_features:

    raise ValueError(
        "The following required features are missing:\n"
        + ", ".join(missing_features)
    )


# ------------------------------------------------------------
# Keep exact feature order
# ------------------------------------------------------------

X = X[expected_features]


print("\nFeatures used by model:")
print(expected_features)


# ============================================================
# 7. TRAIN / TEST SPLIT
# ============================================================

print("\nSplitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print(
    "Training records:",
    len(X_train)
)

print(
    "Testing records:",
    len(X_test)
)


# ============================================================
# 8. CREATE MACHINE LEARNING MODEL
# ============================================================

print("\nCreating Random Forest model...")

model = RandomForestClassifier(

    # Number of decision trees
    n_estimators=200,

    # Handle imbalanced fraud dataset
    class_weight="balanced_subsample",

    # Reproducible results
    random_state=42,

    # Use all available CPU cores
    n_jobs=-1,

    # Prevent excessively deep trees
    max_depth=None,

    # Minimum samples required at a leaf
    min_samples_leaf=1
)


# ============================================================
# 9. TRAIN MODEL
# ============================================================

print("\nTraining model...")
print("This may take some time...")

model.fit(
    X_train,
    y_train
)

print("\nModel training completed successfully!")


# ============================================================
# 10. MAKE PREDICTIONS
# ============================================================

print("\nTesting model...")

y_pred = model.predict(
    X_test
)


# ============================================================
# 11. FRAUD PROBABILITIES
# ============================================================

y_probability = model.predict_proba(
    X_test
)[:, 1]


# ============================================================
# 12. CALCULATE PERFORMANCE
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)


# ============================================================
# 13. DISPLAY RESULTS
# ============================================================

print("\n")
print("=" * 65)
print("MODEL PERFORMANCE")
print("=" * 65)

print(
    f"\nAccuracy  : {accuracy * 100:.2f}%"
)

print(
    f"Precision : {precision * 100:.2f}%"
)

print(
    f"Recall    : {recall * 100:.2f}%"
)

print(
    f"F1 Score  : {f1 * 100:.2f}%"
)

print(
    f"ROC-AUC   : {roc_auc:.4f}"
)


# ============================================================
# 14. CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "Normal",
            "Fraud"
        ],
        zero_division=0
    )
)


# ============================================================
# 15. CONFUSION MATRIX
# ============================================================

print("Confusion Matrix:")

cm = confusion_matrix(
    y_test,
    y_pred
)

print(cm)


# ============================================================
# 16. SAVE TRAINED MODEL
# ============================================================

print("\nSaving trained model...")

joblib.dump(
    model,
    MODEL_FILE
)


# ============================================================
# 17. FINAL MESSAGE
# ============================================================

print("\n")
print("=" * 65)
print("MODEL SAVED SUCCESSFULLY!")
print("=" * 65)

print(
    "\nModel file:"
)

print(
    MODEL_FILE
)

print(
    "\nThe new fraud_model.pkl is compatible with:"
)

print(
    "fraud_detection_model.py"
)

print(
    "\nYour Flask app can now use the trained model."
)

print("=" * 65)