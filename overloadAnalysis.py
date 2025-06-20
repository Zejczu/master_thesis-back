from config import db
from bson.objectid import ObjectId
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pandas as pd

def is_overloaded_by_rules(row):
    conditions = [
        row["hr_after"] >= 150,
        row["hr_after"] - row["hr_during"] >= -10,
        row["duration"] >= 60 and row["intensity"] in ["Medium", "High"],
        row["temperature"] >= 30 and row["hr_after"] >= 140
    ]
    return int(any(conditions))

def run_overload_analysis(horse_id: str) -> dict:
    if not horse_id:
        raise ValueError("Musisz podać horse_id")

    query = {
        "trainings": {"$exists": True, "$ne": []},
        "horseId": ObjectId(horse_id)
    }
    sessions = list(db.sessions.find(query))
    if not sessions:
        return {}

    horse_name = sessions[0].get("horseName", "Unknown")

    data = []
    for session in sessions:
        for training in session.get("trainings", []):
            if training.get("trainingStatus") != "Completed":
                continue

            data.append({
                "trainingType": training.get("trainingType"),
                "intensity": training.get("intensity"),
                "temperature": training.get("temperatureCelsius"),
                "duration": training.get("duration"),
                "hr_before": training.get("heartRateBefore"),
                "hr_during": training.get("heartRateDuring"),
                "hr_after": training.get("heartRateAfter"),
                "ratingScore": training.get("ratingScore"),
            })

    df = pd.DataFrame(data)
    df.dropna(subset=["hr_before", "hr_during", "hr_after", "temperature", "duration", "intensity"], inplace=True)

    # Reguły
    df["overloaded_rule"] = df.apply(is_overloaded_by_rules, axis=1)

    # ML: przygotowanie
    df["label"] = df["ratingScore"].apply(lambda x: 1 if x is not None and x <= 2 else 0)
    features = df.drop(columns=["ratingScore", "label", "overloaded_rule"])
    for col in features.select_dtypes(include=["object"]).columns:
        features[col] = LabelEncoder().fit_transform(features[col].astype(str))

    X_train, X_test, y_train, y_test = train_test_split(features, df["label"], test_size=0.25, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    df["ml_prediction"] = model.predict(features)

    # Hybryda
    def final_overload(row):
        if row["overloaded_rule"] == 1:
            return 1
        elif row["ml_prediction"] == 1:
            return 1
        else:
            return 0

    df["final_overloaded"] = df.apply(final_overload, axis=1)

    overload_stats = {
        "total": len(df),
        "overloaded": int(df["final_overloaded"].sum()),
        "ok": int(len(df) - df["final_overloaded"].sum())
    }

    try:
        db.overloadanalyses.update_one(
            {
                "horseId": ObjectId(horse_id),
                "analysisType": "overload"
            },
            {
                "$set": {
                    "horseId": ObjectId(horse_id),
                    "horseName": horse_name,
                    "analysisType": "overload",
                    "generatedAt": datetime.now(timezone.utc),
                    "stats": overload_stats,
                    "details": df.to_dict(orient="records")
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"[ERROR] Błąd zapisu do MongoDB: {e}")
        return {}

    print(f"[INFO] Overload analysis zakończona dla horseId: {horse_id}")
    print(overload_stats)
    return overload_stats

if __name__ == "__main__":
    # run_overload_analysis("66e94fde1582b84c167f1633")
    pass
