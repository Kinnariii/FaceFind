import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./facefind.db")
DATA_DIR = os.getenv("DATA_DIR", "data")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.40"))
USE_CLAHE = os.getenv("USE_CLAHE", "1") == "1"
DET_SIZE = int(os.getenv("DET_SIZE", "960"))
MAX_SIDE = 1600       # photos are downscaled to this before detection and storage
THUMB_SIDE = 420
MIN_FACE_RATIO = 0.25  # a face counts as "significant" if its area >= 25% of the user's face area
