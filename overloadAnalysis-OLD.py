from config import db
from bson.objectid import ObjectId
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pandas as pd

def run_overload_analysis(horse_id: str = None):
    
    print("horse_id:", horse_id)
    
    if not horse_id:
        raise ValueError("Musisz podać horse_id")

    query = {"trainings": {"$exists": True, "$ne": []}, "horseId": ObjectId(horse_id)}
    try:
        sessions = list(db.sessions.find(query))
    except Exception as e:
        print(f"Błąd połączenia z MongoDB: {e}")
        return {}
    
    print(f"Znaleziono {len(sessions)} sesji treningowych dla horseId: {horse_id}")

    if not sessions:
            print("Brak sesji dla podanego horseId")
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
                "duration": training.get("duration"),  # <-- dodajemy czas trwania treningu
                "hr_before": training.get("heartRateBefore"),
                "hr_during": training.get("heartRateDuring"),
                "hr_after": training.get("heartRateAfter"),
                "ratingScore": training.get("ratingScore"),
            })

    if len(data) < 1:
        print("Zbyt mało danych treningowych do przeprowadzenia analizy przeciążenia.")
        return {}

    df = pd.DataFrame(data)

    df["overloaded"] = df["ratingScore"].apply(lambda x: 1 if x <= 2 else 0)

    features = df.drop(columns=["ratingScore", "overloaded"])

    for col in features.select_dtypes(include=["object"]).columns:
        features[col] = LabelEncoder().fit_transform(features[col])

    X = features
    y = df["overloaded"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    df["predictedOverload"] = model.predict(X)
    
    detailed_results = df.to_dict(orient="records")

    overload_stats = {
        "total": len(df),
        "predictedOverloaded": int(df["predictedOverload"].sum()),
        "predictedOk": int(len(df) - df["predictedOverload"].sum()),
    }

    db.overloadanalyses.update_one(
        {"horseId": ObjectId(horse_id),
        "horseName": horse_name,
         "analysisType": "overload"
         },
        {
            "$set": {
                "horseId": ObjectId(horse_id),
                "analysisType": "overload",
                "generatedAt": datetime.now(timezone.utc),
                "stats": overload_stats,
                "details": detailed_results,  # szczegółowe dane do wykresów
            }
        },
        upsert=True
    )

    print(f"Overload analysis completed for horseId: {horse_id}")
    print(overload_stats)

    return overload_stats

if __name__ == "__main__":
    # app.run(debug=True)
    # horse_id="66e951701582b84c167f1648"
    run_overload_analysis()
    # result = run_overload_analysis()
    # result = run_overload_analysis(horse_id)
    # from pprint import pprint
    # pprint(result)
