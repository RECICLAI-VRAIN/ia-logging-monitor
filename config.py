import os
from pymongo import MongoClient
import pytz

# Enable modules
ENABLE_LOGS = False
ENABLE_CHARTS = True

# Timezone Configuration
LOCAL_TZ = pytz.timezone("Europe/Madrid")

# Database Configuration
DATABASE_URI = "mongodb://localhost:27017"
DATABASE_NAME = "mlops_labeller_db"

def get_database():
    """
    Get a connection to the MongoDB database.

    Returns:
        Database: A MongoDB database connection.
    """
    client = MongoClient(DATABASE_URI)
    return client[DATABASE_NAME]

# YOLO Model Path
YOLO_MODEL_PATH = os.getenv(
    "YOLO_MODEL_PATH", "../models/x-classify-fusioned.pt"
)

# Allowed File Extensions
ALLOWED_EXTENSIONS = {
    "bmp",
    "dng",
    "jpeg",
    "jpg",
    "mpo",
    "png",
    "tif",
    "tiff",
    "webp",
    "pfm",
}

def is_allowed_extension(filename):
    """
    Check if a file has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Label Dictionaries for YOLOv8
LABEL_DICT = {
    0: "SIGRE",
    1: "blue",
    2: "brown",
    3: "green",
    4: "green_point",
    5: "grey",
    6: "yellow",
}
NUMBER_DICT = {
    "SIGRE": 0,
    "blue": 1,
    "brown": 2,
    "green": 3,
    "green_point": 4,
    "grey": 5,
    "yellow": 6,
}

# Color Dictionary for Visualizations
COLOR_DICT = {
    "SIGRE": "rgb(219, 0, 146)",
    "blue": "blue",
    "brown": "rgb(150, 100, 25)",
    "green": "green",
    "green_point": "rgb(35, 150, 102)",
    "grey": "grey",
    "yellow": "rgb(255, 153, 0)",
}

# Image Upload Folder
UPLOAD_FOLDER = "../uploaded_images/"

# WhyLabs Configuration
WHYLABS_DEFAULT_ORG_ID = "org-bZzgRH"
WHYLABS_API_KEY = "Hnd8k7kOSw.qNmQcvH0S6ETUWRVtZD4qP0PH0L46ELienl2EOfwKuDgUhNnAryqu:org-bZzgRH"
WHYLABS_DEFAULT_DATASET_ID = "model-5"
