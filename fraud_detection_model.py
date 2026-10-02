# ============================================================
# CREDIT CARD FRAUD DETECTION MODEL
# Refined Prediction Module
# Compatible with Flask app.py
# ============================================================

import os
import pandas as pd
import joblib


# ============================================================
# 1. MODEL FILE LOCATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILE = os.path.join(
    BASE_DIR,
    "fraud_model.pkl"
)


# ============================================================
# 2. LOAD TRAINED MODEL
# ============================================================

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        "fraud_model.pkl was not found. "
        "Please train the model first."
    )

try:
    model = joblib.load(MODEL_FILE)

except Exception as e:
    raise RuntimeError(
        f"Unable to load fraud_model.pkl: {e}"
    )


# ============================================================
# 3. REQUIRED FEATURES
# ============================================================

FEATURE_COLUMNS = (
    ["Time"]
    + [f"V{i}" for i in range(1, 29)]
    + ["Amount"]
)


# ============================================================
# 4. PREPARE TRANSACTION DATA
# ============================================================

def prepare_transaction(transaction_data):

    # --------------------------------------------------------
    # Dictionary -> DataFrame
    # --------------------------------------------------------

    if isinstance(transaction_data, dict):

        transaction_data = pd.DataFrame(
            [transaction_data]
        )

    # --------------------------------------------------------
    # Already a DataFrame
    # --------------------------------------------------------

    elif isinstance(transaction_data, pd.DataFrame):

        transaction_data = transaction_data.copy()

    # --------------------------------------------------------
    # Other data -> DataFrame
    # --------------------------------------------------------

    else:

        transaction_data = pd.DataFrame(
            transaction_data
        )

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in FEATURE_COLUMNS
        if column not in transaction_data.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # Keep only model features
    # --------------------------------------------------------

    transaction_data = transaction_data[
        FEATURE_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Convert all features to numeric
    # --------------------------------------------------------

    for column in FEATURE_COLUMNS:

        transaction_data[column] = pd.to_numeric(
            transaction_data[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Check invalid values
    # --------------------------------------------------------

    if transaction_data.isnull().any().any():

        invalid_columns = transaction_data.columns[
            transaction_data.isnull().any()
        ].tolist()

        raise ValueError(
            "Invalid or missing numeric values in: "
            + ", ".join(invalid_columns)
        )

    return transaction_data


# ============================================================
# 5. GET FRAUD PROBABILITY
# ============================================================

def get_fraud_probability(transaction_data):

    # --------------------------------------------------------
    # Models with predict_proba
    # --------------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(
            transaction_data
        )[0]

        # ----------------------------------------------------
        # Find class-1 probability correctly
        # ----------------------------------------------------

        if hasattr(model, "classes_"):

            classes = list(model.classes_)

            if 1 in classes:

                fraud_index = classes.index(1)

                return float(
                    probabilities[fraud_index] * 100
                )

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        if len(probabilities) > 1:

            return float(
                probabilities[1] * 100
            )

        return float(
            probabilities[0] * 100
        )

    # --------------------------------------------------------
    # If model doesn't support probability
    # --------------------------------------------------------

    return None


# ============================================================
# 6. PREDICT TRANSACTION
# ============================================================

def predict_transaction(transaction_data):

    """
    Predict whether a credit-card transaction
    is Normal or Fraudulent.

    Compatible with app.py.
    """

    # --------------------------------------------------------
    # Prepare input
    # --------------------------------------------------------

    transaction_data = prepare_transaction(
        transaction_data
    )

    # --------------------------------------------------------
    # Model prediction
    # --------------------------------------------------------

    prediction = model.predict(
        transaction_data
    )[0]

    # --------------------------------------------------------
    # Fraud probability
    # --------------------------------------------------------

    fraud_probability = get_fraud_probability(
        transaction_data
    )

    # --------------------------------------------------------
    # Convert prediction to integer
    # --------------------------------------------------------

    try:

        prediction = int(prediction)

    except (ValueError, TypeError):

        prediction = 1 if str(prediction).lower() in [
            "fraud",
            "fraudulent",
            "1",
            "true"
        ] else 0

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    if prediction == 1:

        result = "Fraudulent Transaction"

    else:

        result = "Normal Transaction"

    # --------------------------------------------------------
    # Probability formatting
    # --------------------------------------------------------

    if fraud_probability is None:

        fraud_probability = 0.0

    fraud_probability = max(
        0.0,
        min(100.0, fraud_probability)
    )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "result": result,
        "fraud_probability": round(
            fraud_probability,
            2
        )
    }


# ============================================================
# 7. TEST MODEL
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("CREDIT CARD FRAUD DETECTION MODEL")
    print("=" * 65)

    print("Model file:")
    print(MODEL_FILE)

    print()

    print("Model loaded successfully.")

    print()

    print("Required features:")
    print(FEATURE_COLUMNS)

    print()

    print("Prediction function is ready.")

    print("=" * 65)