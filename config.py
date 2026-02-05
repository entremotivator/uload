"""
Configuration file for Audio Transcription Hub
Edit these values after setting up Google Cloud services
"""

# =========================
# N8N CONFIGURATION
# =========================
N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/60bbcc46-60c2-484f-a51e-aa0067070f68"

# =========================
# GOOGLE CLOUD CONFIGURATION
# =========================
# Get this from your Google Sheet URL: 
# https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
GOOGLE_SHEETS_ID = "1ZE9Kia1MzSQAekwLOSTRC7ppQ1G5Cbj4vEVvHqa3-n4"

# The name of the sheet tab (usually "Recordings")
SHEET_NAME = "Recordings"

# Sheet GID (tab identifier) - used for direct tab linking
SHEET_GID = "1515801754"

# Path to your service account JSON file
SERVICE_ACCOUNT_FILE = "service_account.json"

# Google Drive folder ID for audio storage
DRIVE_FOLDER_ID = "1X-CBJpOTCQ_auQUyCTFmzb-WlAHXcNw6"

# =========================
# APP CONFIGURATION
# =========================
# Categories for audio recordings
CATEGORIES = [
    "Podcast",
    "Audio Book", 
    "Notes",
    "Class",
    "Business Meeting",
    "Random"
]

# Default category
DEFAULT_CATEGORY = "Notes"

# Supported audio formats for upload
SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "mp4", "webm", "mpeg"]

# Maximum file size warning (in MB)
MAX_FILE_SIZE_WARNING = 100

# =========================
# GOOGLE SHEETS COLUMN MAPPING
# =========================
# If you modify your sheet structure, update these
SHEET_COLUMNS = {
    'timestamp': 'A',
    'title': 'B',
    'category': 'C',
    'filename': 'D',
    'duration': 'E',
    'words': 'F',
    'drive_link': 'G',
    'sheet_link': 'H'
}

# Column headers (must match your Google Sheet)
SHEET_HEADERS = [
    'Timestamp',
    'Title', 
    'Category',
    'Filename',
    'Duration',
    'Words',
    'Drive Link',
    'Sheet Link'
]

# =========================
# UI CONFIGURATION
# =========================
PAGE_TITLE = "Audio Transcription Hub"
PAGE_ICON = "🎙️"

# Sidebar width
SIDEBAR_WIDTH = 300

# Transcript text area height
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
# Request timeout (None = no timeout)
REQUEST_TIMEOUT = None

# Google API scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Cache duration for Google services (in seconds)
CACHE_TTL = 300

# Number of recordings to show per page in library
RECORDINGS_PER_PAGE = 50
