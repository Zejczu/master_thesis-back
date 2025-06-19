from config import db
from bson.objectid import ObjectId
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np


def run_basic_analysis(horse_id: Optional[str] = None) -> None:
    """
    Przeprowadza podstawową analizę treningową dla wszystkich koni lub wybranego konia.
    Zapisuje wyniki do kolekcji 'basicanalyses' w MongoDB.
    """
    query = {"trainings": {"$exists": True, "$ne": []}}
    if horse_id:
        query["horseId"] = ObjectId(horse_id)

    try:
        sessions = list(db.sessions.find(query))
    except Exception as e:
        print(f"[ERROR] Błąd przy pobieraniu danych z MongoDB: {e}")
        return

    if not sessions:
        print("[INFO] Brak sesji treningowych spełniających kryteria.")
        return

    print(f"[INFO] Przetwarzanie {len(sessions)} sesji treningowych...")

    horses = {}
    grouped_data = defaultdict(lambda: defaultdict(list))
    time_series_data = defaultdict(lambda: defaultdict(list))

    for session in sessions:
        hid = session.get("horseId")
        horse_id_str = str(hid)
        horse_name = session.get("horseName", "Unknown")
        horses[horse_id_str] = horse_name

        created_at = session.get("createdAt")
        if not horse_id_str or not created_at:
            continue

        for training in session.get("trainings", []):
            if training.get("trainingStatus") != "Completed":
                continue

            training_type = training.get("trainingType")
            if not training_type:
                continue

            record = extract_training_data(training, created_at)
            if record:
                grouped_data[horse_id_str][training_type].append(record)
                time_series_data[horse_id_str][training_type].append(record)

    for horse_id_str, trainings_by_type in grouped_data.items():
        summary = compute_summary(trainings_by_type)
        trends_month, trends_week = compute_trends(time_series_data[horse_id_str])

        try:
            db.basicanalyses.update_one(
                {"horseId": ObjectId(horse_id_str)},
                {
                    "$set": {
                        "horseId": ObjectId(horse_id_str),
                        "horseName": horses.get(horse_id_str, "Unknown"),
                        "analysisType": "training_summary",
                        "generatedAt": datetime.now(),
                        "summary": summary,
                        "trend": {
                            "byMonth": trends_month,
                            "last7Days": trends_week
                        }
                    }
                },
                upsert=True
            )
            print(f"[INFO] Analiza dla konia {horses[horse_id_str]} (ID: {horse_id_str}) zapisana.")
        except Exception as e:
            print(f"[ERROR] Nie udało się zapisać analizy dla horseId={horse_id_str}: {e}")


def extract_training_data(training: Dict[str, Any], created_at: Any) -> Optional[Dict[str, Any]]:
    try:
        return {
            "hr_before": training.get("heartRateBefore"),
            "hr_during": training.get("heartRateDuring"),
            "hr_after": training.get("heartRateAfter"),
            "temperature": training.get("temperatureCelsius"),
            "created_at": pd.to_datetime(created_at)
        }
    except Exception:
        return None


def compute_summary(trainings_by_type: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    summary = []
    for training_type, records in trainings_by_type.items():
        try:
            hr_before_avg = np.mean([r["hr_before"] for r in records if r["hr_before"] is not None])
            hr_during_avg = np.mean([r["hr_during"] for r in records if r["hr_during"] is not None])
            hr_after_avg = np.mean([r["hr_after"] for r in records if r["hr_after"] is not None])
            temp_avg = np.mean([r["temperature"] for r in records if r["temperature"] is not None])

            summary.append({
                "trainingType": training_type,
                "count": len(records),
                "hrBeforeAvg": round(hr_before_avg, 2),
                "hrDuringAvg": round(hr_during_avg, 2),
                "hrAfterAvg": round(hr_after_avg, 2),
                "temperatureAvg": round(temp_avg, 2),
            })
        except Exception as e:
            print(f"[WARN] Błąd przy podsumowaniu typu {training_type}: {e}")
            continue
    return summary


def compute_trends(trainings_by_type: Dict[str, List[Dict[str, Any]]]) -> (Dict[str, Any], Dict[str, Any]):
    trends_by_month = defaultdict(list)
    trends_last_7_days = defaultdict(list)

    for training_type, records in trainings_by_type.items():
        for r in records:
            if not r["hr_during"] or not r["created_at"]:
                continue

            created_date = r["created_at"]
            trends_by_month[training_type].append((created_date.strftime("%Y-%m"), r["hr_during"]))

            if (datetime.now() - created_date).days <= 7:
                trends_last_7_days[training_type].append((created_date.strftime("%Y-%m-%d"), r["hr_during"]))

    trends_month = {k: __average_by_key(v) for k, v in trends_by_month.items()}
    trends_week = {k: __average_by_key(v) for k, v in trends_last_7_days.items()}

    return trends_month, trends_week


def __average_by_key(pairs: List[tuple]) -> List[Dict[str, Any]]:
    df = pd.DataFrame(pairs, columns=["label", "value"])
    return (
        df.groupby("label")["value"]
        .mean()
        .round(2)
        .reset_index()
        .to_dict(orient="records")
    )


if __name__ == "__main__":
    run_basic_analysis()
