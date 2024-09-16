import os
import sys
from datetime import datetime

import pandas as pd
import whylogs as why
from apscheduler.schedulers.blocking import BlockingScheduler

# Append parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    ENABLE_LOGS,
    LABEL_DICT,
    LOCAL_TZ,
    WHYLABS_API_KEY,
    WHYLABS_DEFAULT_DATASET_ID,
    WHYLABS_DEFAULT_ORG_ID,
    get_database,
)

# Environment variables for WhyLabs
os.environ["WHYLABS_DEFAULT_ORG_ID"] = WHYLABS_DEFAULT_ORG_ID
os.environ["WHYLABS_API_KEY"] = WHYLABS_API_KEY
os.environ["WHYLABS_DEFAULT_DATASET_ID"] = WHYLABS_DEFAULT_DATASET_ID


def check_and_log_new_entries():
    """
    Check for new log entries in the database, log metrics using WhyLabs, and update the entries as logged.

    Connects to the database, retrieves new entries that have not been logged, processes them,
    logs metrics to WhyLabs, and updates the entries as logged in the database.
    """
    # Get the database
    db = get_database()
    if db is None:
        print("Database connection failed.")
        return

    # Query to find new entries that have not been logged
    query = {
        "logged": {"$ne": True},
        "output_validated": {"$ne": None},
    }

    new_entries_count = db.image_logs.count_documents(query)

    if new_entries_count > 0:
        new_entries = db.image_logs.find(query)
        df = pd.DataFrame(list(new_entries))
        df = df.drop(columns=["trained", "logged", "filename"])

        # Replace numerical labels with class names
        df["output_validated"] = df["output_validated"].replace(LABEL_DICT)
        df["output_prediction"] = df["output_prediction"].replace(LABEL_DICT)

        results = why.log_classification_metrics(
            df,
            target_column="output_validated",
            prediction_column="output_prediction",
            score_column="output_confidence",
            log_full_data=True,
            dataset_timestamp=datetime.now(LOCAL_TZ),
        )

        results.writer("whylabs").write()

        # Update the "logged" field for the entries processed
        ids_to_update = df["_id"]
        db.image_logs.update_many(
            {"_id": {"$in": list(ids_to_update)}}, {"$set": {"logged": True}}
        )

    print(
        f"Checked at {datetime.now(LOCAL_TZ)}, found {new_entries_count} new entries."
    )


if __name__ == "__main__":
    if ENABLE_LOGS:
        scheduler = BlockingScheduler()
        scheduler.add_job(check_and_log_new_entries, "interval", minutes=2, max_instances=1)
        scheduler.start()
