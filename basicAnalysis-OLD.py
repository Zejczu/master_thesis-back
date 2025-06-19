from config import db
from bson.objectid import ObjectId
from collections import defaultdict
from datetime import datetime
import pandas as pd
import numpy as np

def run_basic_analysis(horse_id: str = None):
    
    sessions = list(db.sessions.find({"trainings": {"$exists": True, "$ne": []}}))
    
    horses = {}
    for session in sessions:
        horse_id = str(session.get("horseId"))
        if horse_id and horse_id not in horses:
            horses[horse_id] = session.get("horseName")

    grouped_data = defaultdict(lambda: defaultdict(list))
    time_series_data = defaultdict(lambda: defaultdict(list))

    for session in sessions:
        horse_id = str(session.get("horseId"))
        horse_name = session.get("horseName")
        created_at = session.get("createdAt")

        if not horse_id or not created_at:
            continue

        for training in session.get("trainings", []):
            if training.get("trainingStatus") != "Completed":
                continue

            training_type = training.get("trainingType")
            if not training_type:
                continue

            record = {
                "hr_before": training.get("heartRateBefore"),
                "hr_during": training.get("heartRateDuring"),
                "hr_after": training.get("heartRateAfter"),
                "temperature": training.get("temperatureCelsius"),
                "created_at": created_at
            }

            grouped_data[horse_id][training_type].append(record)
            time_series_data[horse_id][training_type].append(record)

    for horse_id, trainings_by_type in grouped_data.items():
        summary = []
        for training_type, records in trainings_by_type.items():
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

        # Trendy miesięczne i tygodniowe (7 dni)
        trends_by_month = defaultdict(list)
        trends_last_7_days = defaultdict(list)

        for training_type, records in time_series_data[horse_id].items():
            for r in records:
                if not r["hr_during"] or not r["created_at"]:
                    continue

                created_date = pd.to_datetime(r["created_at"])
                trends_by_month[training_type].append((created_date.strftime("%Y-%m"), r["hr_during"]))

                if (datetime.now() - created_date).days <= 7:
                    trends_last_7_days[training_type].append((created_date.strftime("%Y-%m-%d"), r["hr_during"]))

        trends_month = {
            k: __average_by_key(v) for k, v in trends_by_month.items()
        }
        trends_week = {
            k: __average_by_key(v) for k, v in trends_last_7_days.items()
        }

        db.basicanalyses.update_one(
            {"horseId": ObjectId(horse_id)},
            {
                "$set": {
                    "horseId": ObjectId(horse_id),
                    "horseName": horses.get(horse_id, "Unknown"),
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

def __average_by_key(pairs):
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
