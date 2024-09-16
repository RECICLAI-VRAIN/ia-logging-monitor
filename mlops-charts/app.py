import os
import sys
from datetime import datetime, time, timedelta

import numpy as np
from flask import Flask, jsonify, render_template, request
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Append parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    COLOR_DICT,
    ENABLE_CHARTS,
    LABEL_DICT,
    LOCAL_TZ,
    NUMBER_DICT,
    TRAINING_DATA,
    get_database,
)

app = Flask(__name__)


@app.route("/")
def index():
    """
    Render the index page.

    Returns:
        Rendered HTML page.
    """
    return render_template("index.html")


@app.route("/training-data", methods=["GET"])
def get_training_data():
    """
    Provide precomputed training data statistics.

    Returns:
        JSON response with training data statistics.
    """
    training_data = {
        "class_counts": TRAINING_DATA,
        "color_dict": COLOR_DICT,
    }
    return jsonify(training_data)


@app.route("/min-date", methods=["GET"])
def get_min_date():
    """
    Provides minimum available date to select.

    Returns:
        JSON response with minimum date.
    """
    min_date = datetime.date(2024, 5, 8)

    return jsonify({"min_date": min_date.isoformat()})


@app.route("/data", methods=["GET"])
def get_data():
    """
    Retrieve and compute metrics for validated data within a date range.

    Query Parameters:
        start_date (str): Start date for the query in YYYY-MM-DD format.
        end_date (str): End date for the query in YYYY-MM-DD format.

    Returns:
        JSON response with data metrics and counts.
    """
    db = get_database()
    now = datetime.now(LOCAL_TZ)
    class_labels = list(NUMBER_DICT.keys())
    start_date_str = request.args.get(
        "start_date", (now - timedelta(days=7)).strftime("%Y-%m-%d")
    )
    end_date_str = request.args.get("end_date", now.strftime("%Y-%m-%d"))

    start_date = datetime.combine(
        datetime.strptime(start_date_str, "%Y-%m-%d"), time.min
    ).replace(tzinfo=LOCAL_TZ)
    end_date = datetime.combine(
        datetime.strptime(end_date_str, "%Y-%m-%d"), time.max
    ).replace(tzinfo=LOCAL_TZ)

    query = {"timestamp_validated": {"$gte": start_date, "$lt": end_date}}
    data = list(db.image_logs.find(query))

    validated_data = [d for d in data if d.get("output_validated") is not None]
    total_validated = len(validated_data)

    class_counts = {label: 0 for label in class_labels}
    for d in validated_data:
        class_counts[LABEL_DICT[d["output_validated"]]] += 1

    daily_metrics = {}
    for d in validated_data:
        day_str = d["timestamp_validated"].strftime("%Y-%m-%d")
        if day_str not in daily_metrics:
            daily_metrics[day_str] = {"y_true": [], "y_pred": [], "entries": 0}
        daily_metrics[day_str]["y_true"].append(d["output_validated"])
        daily_metrics[day_str]["y_pred"].append(d["output_prediction"])
        daily_metrics[day_str]["entries"] += 1

    current_date = start_date
    previous_metrics = {
        "precision": 0.75,
        "accuracy": 0.75,
        "recall": 0.75,
        "f1": 0.75,
    }

    while current_date <= end_date:
        day_str = current_date.strftime("%Y-%m-%d")
        if day_str not in daily_metrics:
            daily_metrics[day_str] = {
                "entries": 0,
                "precision": previous_metrics["precision"],
                "accuracy": previous_metrics["accuracy"],
                "recall": previous_metrics["recall"],
                "f1": previous_metrics["f1"],
            }
        else:
            if daily_metrics[day_str]["entries"] > 0:
                y_true = daily_metrics[day_str]["y_true"]
                y_pred = daily_metrics[day_str]["y_pred"]
                if len(y_true) > 0 and len(y_pred) > 0:
                    current_metrics = {
                        "precision": precision_score(
                            y_true, y_pred, average="weighted", zero_division=1
                        ),
                        "accuracy": accuracy_score(y_true, y_pred),
                        "recall": recall_score(
                            y_true, y_pred, average="micro", zero_division=1
                        ),
                        "f1": f1_score(
                            y_true, y_pred, average="weighted", zero_division=1
                        ),
                    }
                else:
                    current_metrics = previous_metrics
                daily_metrics[day_str].update(current_metrics)
                previous_metrics = current_metrics
        current_date += timedelta(days=1)

    y_true_all = []
    y_pred_all = []

    for d in validated_data:
        y_true_all.append(d["output_validated"])
        y_pred_all.append(d["output_prediction"])

    class_metrics = {}
    for label in class_labels:
        y_true_class = [1 if x == NUMBER_DICT[label] else 0 for x in y_true_all]
        y_pred_class = [1 if x == NUMBER_DICT[label] else 0 for x in y_pred_all]
        class_metrics[label] = {
            "precision": precision_score(y_true_class, y_pred_class, zero_division=1),
            "recall": recall_score(y_true_class, y_pred_class, zero_division=1),
            "f1": f1_score(y_true_class, y_pred_class, zero_division=1),
        }

    metrics = {
        "precision": precision_score(
            y_true_all, y_pred_all, average="weighted", zero_division=1
        ),
        "accuracy": accuracy_score(y_true_all, y_pred_all),
        "recall": recall_score(
            y_true_all, y_pred_all, average="micro", zero_division=1
        ),
        "f1": f1_score(y_true_all, y_pred_all, average="weighted", zero_division=1),
    }

    return jsonify(
        {
            "total_validated": total_validated,
            "class_counts": class_counts,
            "metrics": metrics,
            "daily_metrics": daily_metrics,
            "class_metrics": class_metrics,
            "color_dict": COLOR_DICT,
        }
    )


if __name__ == "__main__":
    if ENABLE_CHARTS:
        app.run(debug=True, host="0.0.0.0", port=5004)
