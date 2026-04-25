import os
import joblib
import pandas as pd
from datetime import datetime, date

# Load once (cached)
_MODEL = None
_GENDER_ENCODER = None
_PLAN_ENCODER = None
_FEATURE_COLUMNS = None

def _calculate_age(dob_str: str) -> int:
    if not dob_str:
        return 0

    dob_str = str(dob_str).strip()

    # Try multiple formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dob = datetime.strptime(dob_str, fmt).date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return max(age, 0)
        except ValueError:
            pass

    # If all formats fail
    return 0

def label_to_plan_id(plan_label: str) -> int:
    # Examples: "Beginner 3", "Intermediate 4", "Advanced 1"
    parts = plan_label.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid plan label format: {plan_label}")

    level = parts[0].lower()   # beginner/intermediate/advanced
    number = int(parts[1])     # 1..5

    if level == "beginner":
        return number  # 1..5
    if level == "intermediate":
        return 5 + number  # 6..10
    if level == "advanced":
        return 10 + number  # 11..15

    raise ValueError(f"Unknown level in plan label: {plan_label}")

def _load_assets():
    global _MODEL, _GENDER_ENCODER, _PLAN_ENCODER, _FEATURE_COLUMNS

    if _MODEL is not None:
        return

    # Adjust path if you place pkls elsewhere
    base_dir = os.path.dirname(__file__)  # backend/ml
    model_dir = os.path.join(base_dir, "model_assets")

    _MODEL = joblib.load(os.path.join(model_dir, "workout_plan.pkl"))
    _GENDER_ENCODER = joblib.load(os.path.join(model_dir, "gender_encoder.pkl"))
    _PLAN_ENCODER = joblib.load(os.path.join(model_dir, "workout_plan_encoder.pkl"))
    _FEATURE_COLUMNS = joblib.load(os.path.join(model_dir, "feature_columns.pkl"))

def predict_plan(fitness_data: dict) -> tuple[int, str]:
    """
    Returns: (plan_id 1..15, plan_label like 'Beginner 2')
    fitness_data must include: dob, gender, height, weight, workout_duration, weekly_frequency
    """

    _load_assets()

    dob = fitness_data.get("dob", "2000-01-01")
    gender = fitness_data.get("gender", "Male")
    height = float(fitness_data.get("height", 0))
    weight = float(fitness_data.get("weight", 0))
    duration = float(fitness_data.get("workout_duration", 0))
    freq = float(fitness_data.get("weekly_frequency", 0))

    age = _calculate_age(dob)
    gender_enc = int(_GENDER_ENCODER.transform([gender])[0])

    # Avoid divide-by-zero
    height_m = max(height / 100.0, 0.01)
    bmi = weight / (height_m ** 2)
    weight_height_ratio = weight / max(height, 1.0)
    duration_per_week = duration * freq
    bmi_age_ratio = bmi / max(age, 1)

    row = {
        "Age": age,
        "Gender_enc": gender_enc,
        "Weight_kg": weight,
        "Height_cm": height,
        "Session_Duration_minutes": duration,
        "Workout_Frequency_days_per_week": freq,
        "BMI": bmi,
        "Weight_Height_Ratio": weight_height_ratio,
        "Duration_per_Week": duration_per_week,
        "BMI_Age_Ratio": bmi_age_ratio
    }

    X = pd.DataFrame([row])

    # Ensure correct column order
    X = X[_FEATURE_COLUMNS]

    pred_encoded = _MODEL.predict(X)[0]
    plan_label = _PLAN_ENCODER.inverse_transform([pred_encoded])[0]  # e.g. "Beginner 2"

    plan_id = label_to_plan_id(plan_label)

    return plan_id, plan_label
