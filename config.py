"""
Configuration file for Audio Transcription Hub
Edit these values after setting up Google Cloud services
"""
# =========================
# N8N CONFIGURATION
# =========================
N8N_WEBHOOK_URL = (
    "https://agentonline-u29564.vm.elestio.app/webhook-test/"
    "60bbcc46-60c2-484f-a51e-aa0067070f68"
)
# =========================
# GOOGLE SHEETS CONFIGURATION
# =========================
# Spreadsheet ID from:
# https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = "1ZE9Kia1MzSQAekwLOSTRC7ppQ1G5Cbj4vEVvHqa3-n4"
# 🔒 Backward compatibility (prevents AttributeError)
GOOGLE_SHEETS_ID = SPREADSHEET_ID
# Sheet tab name (must match exactly)
# NOTE: Change this to match your actual sheet tab name (e.g., "Sheet1")
# or create a tab named "Recordings" in your Google Sheet
SHEET_NAME = "Recordings"
# Use sheet name only (prevents 404 range errors)
RANGE_NAME = SHEET_NAME
# =========================
# GOOGLE CLOUD AUTH
# =========================
SERVICE_ACCOUNT_FILE = "service_account.json"
# Google Drive folder ID for audio storage
DRIVE_FOLDER_ID = "1X-CBJpOTCQ_auQUyCTFmzb-WlAHXcNw6"
# =========================
# APP CONFIGURATION
# =========================
CATEGORIES = [
    "Podcast",
    "Audio Book",
    "Notes",
    "Class",
    "Business Meeting",
    "Random",
]
DEFAULT_CATEGORY = "Notes"
SUPPORTED_AUDIO_FORMATS = [
    "wav",
    "mp3",
    "m4a",
    "mp4",
    "webm",
    "mpeg",
]
MAX_FILE_SIZE_WARNING = 100  # MB
# =========================
# GOOGLE SHEETS STRUCTURE
# =========================
SHEET_HEADERS = [
    "Timestamp",
    "Title",
    "Category",
    "Filename",
    "Duration",
    "Words",
    "Drive Link",
    "Sheet Link",
]
SHEET_COLUMNS = {
    "timestamp": "A",
    "title": "B",
    "category": "C",
    "filename": "D",
    "duration": "E",
    "words": "F",
    "drive_link": "G",
    "sheet_link": "H",
}
# =========================
# UI CONFIGURATION
# =========================
PAGE_TITLE = "Audio Transcription Hub"
PAGE_ICON = "🎙️"
SIDEBAR_WIDTH = 300
TRANSCRIPT_HEIGHT = 400
# =========================
# FEATURE FLAGS
# =========================
ENABLE_DASHBOARD = True
ENABLE_AUDIO_PLAYBACK = True
ENABLE_CATEGORY_FILTER = True
ENABLE_SEARCH = True
# =========================
# ADVANCED SETTINGS
# =========================
REQUEST_TIMEOUT = None  # No timeout for long audio
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
CACHE_TTL = 300
RECORDINGS_PER_PAGE = 50
