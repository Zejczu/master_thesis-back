from config import db
from bson.objectid import ObjectId
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

def run_overload_analysis(horse_id: str = None) -> dict:
    """
    Przeprowadza analizę przeciążenia konia na podstawie danych treningowych.
    Zapisuje wyniki do kolekcji 'overloadanalyses' w MongoDB.
    """
    if not horse_id:
        raise ValueError("Musisz podać horse_id")

    try:
        query = {
            "trainings": {"$exists": True, "$ne": []},
            "horseId": ObjectId(horse_id)
        }
        sessions = list(db.sessions.find(query))
    except Exception as e:
        print(f"Błąd podczas pobierania danych z MongoDB: {e}")
        return {}

    print(f"[INFO] Znaleziono {len(sessions)} sesji treningowych dla horseId: {horse_id}")

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

    if len(data) < 5:
        print("[INFO] Zbyt mało danych treningowych do przeprowadzenia analizy przeciążenia.")
        return {}

    df = pd.DataFrame(data)

    df["overloaded"] = df["ratingScore"].apply(lambda x: 1 if x is not None and x <= 2 else 0)
    df.dropna(subset=["hr_before", "hr_during", "hr_after", "temperature", "duration"], inplace=True)

    features = df.drop(columns=["ratingScore", "overloaded"])
    for col in features.select_dtypes(include=["object"]).columns:
        features[col] = LabelEncoder().fit_transform(features[col].astype(str))

    X = features
    y = df["overloaded"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    df["predictedOverload"] = model.predict(X)

    overload_stats = {
        "total": len(df),
        "predictedOverloaded": int(df["predictedOverload"].sum()),
        "predictedOk": int(len(df) - df["predictedOverload"].sum()),
        "accuracy": round(report["accuracy"], 2),
        "precision": round(report["1"]["precision"], 2) if "1" in report else None,
        "recall": round(report["1"]["recall"], 2) if "1" in report else None,
    }

    detailed_results = df.to_dict(orient="records")

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
                    "details": detailed_results
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
    # Przykład wywołania testowego:
    # run_overload_analysis("66e951701582b84c167f1648")
    pass
