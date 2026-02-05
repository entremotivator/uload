import streamlit as st
import requests
import base64
from audio_recorder_streamlit import audio_recorder
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
from datetime import datetime
import json
import os
import io
import re
import config  # Import our configuration

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
)

# Custom CSS for colorful dashboard with audio player
st.markdown("""
<style>
    /* Dashboard Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.3);
    }
    
    .metric-card h1 {
        font-size: 3em;
        margin: 10px 0;
        font-weight: bold;
    }
    
    .metric-card p {
        font-size: 1.1em;
        opacity: 0.9;
    }
    
    .metric-card-blue {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .metric-card-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .metric-card-purple {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .metric-card-red {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    }
    
    .metric-card-yellow {
        background: linear-gradient(135deg, #f7b733 0%, #fc4a1a 100%);
    }
    
    /* Recording Cards */
    .recording-card {
        background: white;
        border-left: 5px solid #667eea;
        padding: 20px;
        margin: 15px 0;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .recording-card:hover {
        transform: translateX(8px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        border-left-width: 8px;
    }
    
    .recording-card h3 {
        color: #667eea;
        margin-top: 0;
    }
    
    /* Audio Player Container */
    .audio-player-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .audio-player-title {
        color: white;
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    /* Category Badges */
    .category-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.95em;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    
    .category-badge:hover {
        transform: scale(1.05);
    }
    
    .badge-podcast {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .badge-audiobook {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .badge-notes {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .badge-class {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
    }
    
    .badge-businessmeeting {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    
    .badge-meeting {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    
    .badge-random {
        background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
        color: white;
    }
    
    /* Data Table */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        text-align: left;
        position: sticky;
        top: 0;
        z-index: 10;
        font-weight: bold;
    }
    
    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid #eee;
    }
    
    .dataframe tr:hover {
        background-color: #f8f9ff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        transition: all 0.3s;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: bold;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left-width: 5px;
    }
    
    /* Section headers */
    h1, h2, h3 {
        color: #667eea;
    }
    
    /* Audio element styling */
    audio {
        width: 100%;
        border-radius: 10px;
        outline: none;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE API SETUP
# =========================
@st.cache_resource(ttl=config.CACHE_TTL)
def get_google_services_from_file():
    """Initialize Google Sheets and Drive services from file"""
    try:
        if os.path.exists(config.SERVICE_ACCOUNT_FILE):
            credentials = service_account.Credentials.from_service_account_file(
                config.SERVICE_ACCOUNT_FILE,
                scopes=config.GOOGLE_SCOPES
            )
            sheets_service = build('sheets', 'v4', credentials=credentials)
            drive_service = build('drive', 'v3', credentials=credentials)
            return sheets_service, drive_service
    except Exception as e:
        st.error(f"Error loading service account from file: {e}")
    return None, None

@st.cache_resource(ttl=config.CACHE_TTL)
def get_google_services_from_dict(_credentials_dict):
    """Initialize Google Sheets and Drive services from uploaded JSON"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            _credentials_dict,
            scopes=config.GOOGLE_SCOPES
        )
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        return sheets_service, drive_service
    except Exception as e:
        st.error(f"Error loading service account from uploaded file: {e}")
        return None, None

def get_google_services():
    """Get Google services from session state, uploaded file, or local file"""
    # Check if we have credentials in session state (from upload)
    if 'google_credentials' in st.session_state and st.session_state.google_credentials:
        return get_google_services_from_dict(st.session_state.google_credentials)
    
    # Otherwise try to load from file
    return get_google_services_from_file()

# =========================
# AUDIO PLAYBACK FUNCTIONS
# =========================
def extract_drive_file_id(drive_link):
    """Extract file ID from various Google Drive URL formats"""
    if not drive_link or not drive_link.strip():
        return None
    
    # Pattern 1: /file/d/FILE_ID/view
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    # Pattern 2: id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    # Pattern 3: /open?id=FILE_ID
    match = re.search(r'/open\?id=([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)
    
    # Pattern 4: direct file ID (if just the ID is provided)
    if re.match(r'^[a-zA-Z0-9_-]+$', drive_link.strip()):
        return drive_link.strip()
    
    return None

@st.cache_data(ttl=3600)
def get_audio_from_drive(_drive_service, file_id):
    """Download audio file from Google Drive and return as bytes"""
    try:
        request = _drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        return file_buffer.read()
    except Exception as e:
        st.error(f"Error downloading audio from Drive: {e}")
        return None

def play_audio_inline(drive_link, drive_service, title="Audio Playback"):
    """Display audio player inline for Google Drive audio file"""
    if not drive_link or not drive_link.strip():
        st.warning("⚠️ No audio link available")
        return
    
    file_id = extract_drive_file_id(drive_link)
    
    if not file_id:
        st.error("❌ Could not extract file ID from Drive link")
        st.caption(f"Link: {drive_link}")
        return
    
    with st.spinner("🎵 Loading audio from Drive..."):
        audio_bytes = get_audio_from_drive(drive_service, file_id)
    
    if audio_bytes:
        st.markdown(f"""
        <div class="audio-player-container">
            <div class="audio-player-title">🎧 {title}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.audio(audio_bytes, format='audio/wav')
        
        # Show audio info
        size_mb = len(audio_bytes) / (1024 * 1024)
        st.caption(f"📊 Audio size: {size_mb:.2f} MB")
    else:
        st.error("❌ Failed to load audio from Drive")
        st.info("💡 Make sure the file is shared with the service account")

# =========================
# GOOGLE SHEETS FUNCTIONS (WITH CRUD)
# =========================
def read_sheets_data(sheets_service):
    """Read all recordings from Google Sheets"""
    if not sheets_service:
        return pd.DataFrame()
    
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range=f'{config.SHEET_NAME}!A2:H'
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame(columns=config.SHEET_HEADERS)
        
        # Pad rows that have missing columns
        max_cols = len(config.SHEET_HEADERS)
        padded_values = [row + [''] * (max_cols - len(row)) for row in values]
        
        df = pd.DataFrame(padded_values, columns=config.SHEET_HEADERS)
        # Add row index for reference
        df['Row'] = range(2, len(df) + 2)  # Starting from row 2 (after header)
        return df
    except Exception as e:
        st.error(f"Error reading sheets: {e}")
        return pd.DataFrame()

def update_sheet_row(sheets_service, row_number, data):
    """Update a specific row in Google Sheets"""
    if not sheets_service:
        return False
    
    try:
        range_name = f'{config.SHEET_NAME}!A{row_number}:H{row_number}'
        body = {'values': [data]}
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error updating row: {e}")
        return False

def delete_sheet_row(sheets_service, row_number):
    """Delete a specific row in Google Sheets"""
    if not sheets_service:
        return False
    
    try:
        # Get sheet ID (assuming first sheet, ID = 0)
        sheet_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=config.GOOGLE_SHEETS_ID
        ).execute()
        
        sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']
        
        request = {
            'deleteDimension': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'ROWS',
                    'startIndex': row_number - 1,
                    'endIndex': row_number
                }
            }
        }
        
        body = {'requests': [request]}
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting row: {e}")
        return False

def add_sheet_row(sheets_service, data):
    """Add a new row to Google Sheets"""
    if not sheets_service:
        return False
    
    try:
        range_name = f'{config.SHEET_NAME}!A:H'
        body = {'values': [data]}
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error adding row: {e}")
        return False

# =========================
# SESSION STATE INITIALIZATION
# =========================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "audio_bytes": None,
        "transcription": None,
        "title": "",
        "category": config.DEFAULT_CATEGORY,
        "filename": "",
        "stage": "idle",
        "submitted": False,
        "page": "Dashboard",
        "response_data": None,
        "edit_mode": False,
        "edit_row": None,
        "view_mode": "cards",
        "playing_audio": None,
        "selected_recording": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =========================
# SIDEBAR - NAVIGATION & STATS
# =========================
def render_sidebar():
    """Render sidebar with navigation and statistics"""
    with st.sidebar:
        st.title("🎙️ Audio Hub")
        
        # Google Authentication Section
        render_google_auth_section()
        
        st.divider()
        
        # Page Navigation
        page = st.radio(
            "📍 Navigation",
            ["📊 Dashboard", "🎙️ Record", "📚 Library", "🎵 Player", "📈 Analytics"],
            label_visibility="visible"
        )
        
        page_map = {
            "📊 Dashboard": "Dashboard",
            "🎙️ Record": "Record",
            "📚 Library": "Library",
            "🎵 Player": "Player",
            "📈 Analytics": "Analytics"
        }
        st.session_state.page = page_map[page]
        
        st.divider()
        
        render_quick_stats()

def render_google_auth_section():
    """Render Google authentication/login section in sidebar"""
    st.subheader("🔐 Connection")
    
    # Check if already authenticated
    sheets_service, drive_service = get_google_services()
    
    if sheets_service:
        st.success("✅ Connected")
        
        # Show which method is being used
        if 'google_credentials' in st.session_state and st.session_state.google_credentials:
            st.caption("📤 Uploaded credentials")
        elif os.path.exists(config.SERVICE_ACCOUNT_FILE):
            st.caption("📁 Local credentials")
        
        # Logout button
        if st.button("🚪 Disconnect", use_container_width=True):
            if 'google_credentials' in st.session_state:
                del st.session_state.google_credentials
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("⚠️ Not connected")
        
        # File upload option
        with st.expander("📤 Upload JSON", expanded=True):
            uploaded_json = st.file_uploader(
                "Service Account JSON",
                type=['json'],
                help="Upload service_account.json",
                label_visibility="collapsed"
            )
            
            if uploaded_json is not None:
                try:
                    credentials_dict = json.load(uploaded_json)
                    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                    if all(field in credentials_dict for field in required_fields):
                        st.session_state.google_credentials = credentials_dict
                        st.success("✅ Loaded!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("❌ Invalid file")
                except:
                    st.error("❌ Error loading")

def render_quick_stats():
    """Render quick statistics in sidebar"""
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.info("👆 Connect to view stats")
        return
    
    with st.spinner("Loading..."):
        df = read_sheets_data(sheets_service)
    
    st.subheader("⚡ Quick Stats")
    
    # Total recordings
    st.metric("📼 Recordings", len(df))
    
    # Total words
    if not df.empty and 'Words' in df.columns:
        try:
            total_words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
            total_words = pd.to_numeric(total_words, errors='coerce').fillna(0).sum()
            st.metric("📝 Total Words", f"{int(total_words):,}")
        except:
            st.metric("📝 Total Words", "N/A")
    
    # Today's recordings
    if not df.empty and 'Timestamp' in df.columns:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_count = df['Timestamp'].str.contains(today, na=False).sum()
            st.metric("🎯 Today", today_count)
        except:
            pass
    
    # Latest recording
    if not df.empty:
        st.divider()
        st.caption("🎵 Latest Recording")
        latest = df.iloc[0]
        st.caption(f"**{latest.get('Title', 'Untitled')[:25]}...**")
        st.caption(f"📂 {latest.get('Category', 'N/A')}")

# =========================
# DASHBOARD PAGE
# =========================
def render_dashboard_page():
    """Render colorful dashboard with full data view"""
    st.title("📊 Dashboard Overview")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("❌ Google Sheets not configured.")
        st.info("👈 Upload your service_account.json in the sidebar")
        st.stop()
    
    # Load data
    with st.spinner("Loading dashboard data..."):
        df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("📭 No recordings yet. Go to the Record page!")
        return
    
    # Metrics Row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card metric-card-blue">
            <h1>{len(df)}</h1>
            <p>Total Recordings</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if 'Words' in df.columns:
            try:
                total_words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
                total_words = pd.to_numeric(total_words, errors='coerce').fillna(0).sum()
                st.markdown(f"""
                <div class="metric-card metric-card-green">
                    <h1>{int(total_words):,}</h1>
                    <p>Total Words</p>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.metric("Total Words", "N/A")
    
    with col3:
        if 'Category' in df.columns:
            unique_cats = df['Category'].nunique()
            st.markdown(f"""
            <div class="metric-card metric-card-orange">
                <h1>{unique_cats}</h1>
                <p>Categories</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_count = df['Timestamp'].str.contains(today, na=False).sum()
            st.markdown(f"""
            <div class="metric-card metric-card-purple">
                <h1>{today_count}</h1>
                <p>Today</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("Today", "0")
    
    with col5:
        # Average words per recording
        if 'Words' in df.columns:
            try:
                words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
                words = pd.to_numeric(words, errors='coerce').fillna(0)
                avg_words = int(words.mean())
                st.markdown(f"""
                <div class="metric-card metric-card-red">
                    <h1>{avg_words:,}</h1>
                    <p>Avg Words</p>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass
    
    with col6:
        # This week's recordings
        try:
            from datetime import timedelta
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            week_count = df['Timestamp'].apply(lambda x: x >= week_ago if isinstance(x, str) else False).sum()
            st.markdown(f"""
            <div class="metric-card metric-card-yellow">
                <h1>{week_count}</h1>
                <p>This Week</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass
    
    st.divider()
    
    # Category Distribution & Recent Activity
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if 'Category' in df.columns:
            st.subheader("📂 Category Distribution")
            category_counts = df['Category'].value_counts()
            
            for cat, count in category_counts.items():
                badge_class = f"badge-{cat.lower().replace(' ', '')}"
                percentage = (count / len(df)) * 100
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <span class="category-badge {badge_class}">{cat}</span>
                    <span style="margin-left: 10px;"><strong>{count}</strong> recordings ({percentage:.1f}%)</span>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🕐 Recent Recordings")
        recent = df.head(5)
        for idx, row in recent.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background: #f8f9ff; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #667eea;">
                    <strong>🎙️ {row.get('Title', 'Untitled')[:40]}...</strong><br>
                    <small>📅 {row.get('Timestamp', 'N/A')} | 📂 {row.get('Category', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # Full Data Table
    st.subheader("📋 All Recordings")
    
    # View toggle
    view_col1, view_col2, view_col3, view_col4 = st.columns([1, 1, 1, 3])
    with view_col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
    
    with view_col2:
        view_mode = st.selectbox(
            "View",
            ["Table View", "Card View"],
            label_visibility="collapsed"
        )
    
    with view_col3:
        csv = df.drop('Row', axis=1).to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "recordings.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Display data
    if view_mode == "Table View":
        render_data_table(df, sheets_service, drive_service)
    else:
        render_data_cards(df, sheets_service, drive_service)

def render_data_table(df, sheets_service, drive_service):
    """Render data as an interactive table with edit/delete/play"""
    
    # Make a copy for display
    display_df = df.drop('Row', axis=1) if 'Row' in df.columns else df
    
    # Display the dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "Timestamp": st.column_config.DatetimeColumn(
                "Date",
                format="YYYY-MM-DD HH:mm",
            ),
            "Drive Link": st.column_config.LinkColumn("Audio"),
            "Sheet Link": st.column_config.LinkColumn("Doc"),
            "Words": st.column_config.NumberColumn("Words", format="%d"),
        }
    )
    
    # Action buttons below table
    st.divider()
    st.subheader("🎯 Actions")
    
    action_col1, action_col2 = st.columns([1, 3])
    
    with action_col1:
        selected_row = st.number_input(
            "Row to Act On",
            min_value=2,
            max_value=len(df) + 1,
            value=2,
            help="Row number from the sheet (starts at 2)"
        )
    
    with action_col2:
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        with btn_col1:
            if st.button("🎵 Play Audio", use_container_width=True, type="primary"):
                row_data = df[df['Row'] == selected_row]
                if not row_data.empty:
                    st.session_state.selected_recording = row_data.iloc[0].to_dict()
                    st.rerun()
        
        with btn_col2:
            if st.button("✏️ Edit Row", use_container_width=True):
                st.session_state.edit_mode = True
                st.session_state.edit_row = selected_row
                st.rerun()
        
        with btn_col3:
            if st.button("🗑️ Delete Row", use_container_width=True):
                if delete_sheet_row(sheets_service, selected_row):
                    st.success(f"✅ Deleted row {selected_row}")
                    st.cache_resource.clear()
                    st.cache_data.clear()
                    st.rerun()
        
        with btn_col4:
            row_data = df[df['Row'] == selected_row]
            if not row_data.empty:
                doc_link = row_data.iloc[0].get('Sheet Link', '')
                if doc_link and doc_link.strip():
                    st.link_button("📄 View Doc", doc_link, use_container_width=True)
    
    # Play audio inline if selected
    if st.session_state.get('selected_recording'):
        st.divider()
        recording = st.session_state.selected_recording
        st.subheader(f"🎵 Now Playing: {recording.get('Title', 'Untitled')}")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            play_audio_inline(recording.get('Drive Link', ''), drive_service, recording.get('Title', 'Audio'))
        
        with col2:
            st.markdown(f"""
            <div style="background: #f8f9ff; padding: 20px; border-radius: 10px;">
                <h4>📋 Recording Info</h4>
                <p><strong>Category:</strong> {recording.get('Category', 'N/A')}</p>
                <p><strong>Date:</strong> {recording.get('Timestamp', 'N/A')}</p>
                <p><strong>Words:</strong> {recording.get('Words', 'N/A')}</p>
                <p><strong>Duration:</strong> {recording.get('Duration', 'N/A')}</p>
                <p><strong>File:</strong> {recording.get('Filename', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("❌ Close Player"):
            st.session_state.selected_recording = None
            st.rerun()
    
    # Edit form
    if st.session_state.get('edit_mode') and st.session_state.get('edit_row'):
        render_edit_form(df, sheets_service)

def render_edit_form(df, sheets_service):
    """Render edit form for a specific row"""
    st.divider()
    st.subheader("✏️ Edit Recording")
    
    row_num = st.session_state.edit_row
    row_data = df[df['Row'] == row_num]
    
    if row_data.empty:
        st.error("Row not found")
        return
    
    row_data = row_data.iloc[0]
    
    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_title = st.text_input("Title", value=row_data['Title'])
            new_category = st.selectbox("Category", config.CATEGORIES, 
                                       index=config.CATEGORIES.index(row_data['Category']) if row_data['Category'] in config.CATEGORIES else 0)
            new_filename = st.text_input("Filename", value=row_data['Filename'])
            new_duration = st.text_input("Duration", value=row_data['Duration'])
        
        with col2:
            new_words = st.text_input("Words", value=row_data['Words'])
            new_drive_link = st.text_input("Drive Link", value=row_data['Drive Link'])
            new_doc_link = st.text_input("Doc Link", value=row_data['Sheet Link'])
        
        submit_col1, submit_col2 = st.columns(2)
        
        with submit_col1:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        
        with submit_col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            new_data = [
                row_data['Timestamp'],  # Keep original timestamp
                new_title,
                new_category,
                new_filename,
                new_duration,
                new_words,
                new_drive_link,
                new_doc_link
            ]
            
            if update_sheet_row(sheets_service, row_num, new_data):
                st.success("✅ Updated successfully!")
                st.session_state.edit_mode = False
                st.session_state.edit_row = None
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
        
        if cancelled:
            st.session_state.edit_mode = False
            st.session_state.edit_row = None
            st.rerun()

def render_data_cards(df, sheets_service, drive_service):
    """Render data as colorful cards with inline playback"""
    for idx, row in df.iterrows():
        category_class = f"badge-{row['Category'].lower().replace(' ', '')}"
        
        with st.expander(f"🎙️ {row['Title']}", expanded=False):
            # Header
            st.markdown(f"""
            <span class="category-badge {category_class}">{row['Category']}</span>
            """, unsafe_allow_html=True)
            
            # Info
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**📅 Date:** {row['Timestamp']}")
            col2.write(f"**📝 Words:** {row['Words']}")
            col3.write(f"**⏱️ Duration:** {row['Duration']}")
            col4.write(f"**📁 File:** {row['Filename']}")
            
            st.divider()
            
            # Audio player
            if row.get('Drive Link') and row['Drive Link'].strip():
                play_audio_inline(row['Drive Link'], drive_service, row['Title'])
            
            st.divider()
            
            # Action buttons
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if row.get('Drive Link') and row['Drive Link'].strip():
                    st.link_button("🔗 Open in Drive", row['Drive Link'], use_container_width=True)
            
            with btn_col2:
                if row.get('Sheet Link') and row['Sheet Link'].strip():
                    st.link_button("📄 View Doc", row['Sheet Link'], use_container_width=True)
            
            with btn_col3:
                if st.button(f"🗑️ Delete", key=f"del_{row['Row']}", use_container_width=True):
                    if delete_sheet_row(sheets_service, row['Row']):
                        st.success(f"✅ Deleted!")
                        st.cache_resource.clear()
                        st.cache_data.clear()
                        st.rerun()

# =========================
# PLAYER PAGE
# =========================
def render_player_page():
    """Render dedicated audio player page"""
    st.title("🎵 Audio Player")
    st.markdown("Browse and play all your recordings in one place")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("❌ Google Sheets not configured.")
        st.info("👈 Upload your service_account.json in the sidebar")
        st.stop()
    
    df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("📭 No recordings yet")
        return
    
    # Playlist section
    st.subheader("📋 Playlist")
    
    # Filter controls
    col1, col2 = st.columns([1, 2])
    with col1:
        if 'Category' in df.columns:
            category_filter = st.multiselect(
                "Filter by Category",
                options=['All'] + sorted(df['Category'].unique().tolist()),
                default=['All']
            )
    
    with col2:
        search = st.text_input("🔍 Search titles", "")
    
    # Apply filters
    filtered_df = df.copy()
    if category_filter and 'All' not in category_filter:
        filtered_df = filtered_df[filtered_df['Category'].isin(category_filter)]
    
    if search:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search, case=False, na=False)]
    
    st.write(f"**{len(filtered_df)} recordings available**")
    
    st.divider()
    
    # Playlist with play buttons
    for idx, row in filtered_df.iterrows():
        category_class = f"badge-{row['Category'].lower().replace(' ', '')}"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: #f8f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
                <h4 style="margin: 0;">🎙️ {row['Title']}</h4>
                <span class="category-badge {category_class}" style="font-size: 0.8em;">{row['Category']}</span>
                <p style="margin: 5px 0 0 0; color: #666;">
                    📅 {row['Timestamp']} | 📝 {row['Words']} words | ⏱️ {row['Duration']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button(f"▶️ Play", key=f"play_{row['Row']}", use_container_width=True, type="primary"):
                st.session_state.playing_audio = row.to_dict()
                st.rerun()
        
        with col3:
            if row.get('Sheet Link') and row['Sheet Link'].strip():
                st.link_button("📄 Doc", row['Sheet Link'], use_container_width=True, key=f"doc_{row['Row']}")
    
    # Now Playing section
    if st.session_state.get('playing_audio'):
        st.divider()
        render_now_playing(drive_service)

def render_now_playing(drive_service):
    """Render now playing section"""
    recording = st.session_state.playing_audio
    
    st.subheader("🎵 Now Playing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="audio-player-container">
            <div class="audio-player-title">🎧 {recording.get('Title', 'Untitled')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        play_audio_inline(recording.get('Drive Link', ''), drive_service, recording.get('Title', 'Audio'))
    
    with col2:
        category_class = f"badge-{recording.get('Category', 'Random').lower().replace(' ', '')}"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3>📋 Details</h3>
            <span class="category-badge {category_class}">{recording.get('Category', 'N/A')}</span>
            <p><strong>📅 Date:</strong> {recording.get('Timestamp', 'N/A')}</p>
            <p><strong>📝 Words:</strong> {recording.get('Words', 'N/A')}</p>
            <p><strong>⏱️ Duration:</strong> {recording.get('Duration', 'N/A')}</p>
            <p><strong>📁 File:</strong> {recording.get('Filename', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        if recording.get('Sheet Link') and recording['Sheet Link'].strip():
            st.link_button("📄 View Transcript", recording['Sheet Link'], use_container_width=True)
        
        if recording.get('Drive Link') and recording['Drive Link'].strip():
            st.link_button("🔗 Open in Drive", recording['Drive Link'], use_container_width=True)
        
        if st.button("❌ Stop Playing", use_container_width=True):
            st.session_state.playing_audio = None
            st.rerun()

# =========================
# RECORD PAGE
# =========================
def render_record_page():
    """Render the main recording interface"""
    st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")
    st.markdown(
        "Record **as long as you want** or upload large audio files. "
        "No recording timeout. Built for meetings, podcasts, classes, and long dictation."
    )

    st.divider()

    # Audio Details Section
    st.subheader("📝 Audio Details")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.session_state.title = st.text_input(
            "Title",
            value=st.session_state.title,
            placeholder="Podcast episode, class session, coaching call, meeting notes…",
        )
    
    with col2:
        st.session_state.category = st.selectbox(
            "Category",
            config.CATEGORIES,
            index=config.CATEGORIES.index(st.session_state.category)
        )

    # Audio Input Section
    st.subheader("🎧 Audio Input")
    mode = st.radio(
        "Select input method",
        ["Record Audio", "Upload File"],
        horizontal=True,
    )

    audio_data = None
    filename = None

    # Recording Mode
    if mode == "Record Audio":
        st.markdown("""
        **Recording notes**
        - Click once to start recording
        - Click again to stop
        - You may record **for hours**
        - Keep the tab open while recording
        """)

        audio_bytes = audio_recorder(
            recording_color="#ef4444",
            neutral_color="#2563eb",
            icon_name="microphone",
            icon_size="3x",
        )

        if audio_bytes:
            audio_data = audio_bytes
            filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            st.audio(audio_bytes)
            st.success("✅ Recording ready")

    # Upload Mode
    else:
        uploaded = st.file_uploader(
            "Upload audio file",
            type=config.SUPPORTED_AUDIO_FORMATS,
            help="Large files supported (depends on server limits)",
        )

        if uploaded:
            audio_data = uploaded.read()
            filename = uploaded.name
            st.audio(audio_data)
            st.success("✅ File loaded")

    # Audio Info
    if audio_data:
        size_mb = round(len(audio_data) / (1024 * 1024), 2)
        if size_mb > config.MAX_FILE_SIZE_WARNING:
            st.warning(f"⚠️ Large file detected: **{size_mb} MB** - Processing may take several minutes")
        else:
            st.info(f"📊 Audio size: **{size_mb} MB**")

    # Submit Button
    can_submit = bool(audio_data and st.session_state.title)
    
    submit = st.button(
        "🚀 Transcribe Audio",
        type="primary",
        disabled=not can_submit,
        use_container_width=True,
    )

    # Process Transcription
    if submit:
        st.session_state.audio_bytes = audio_data
        st.session_state.filename = filename
        st.session_state.stage = "processing"
        st.session_state.submitted = True

    if st.session_state.submitted and st.session_state.audio_bytes:
        process_transcription()

    # Display Results
    if st.session_state.transcription:
        display_transcription_results()

def process_transcription():
    """Handle the transcription process"""
    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("🔄 Encoding audio (this may take time for very large files)…")
        progress.progress(20)

        audio_b64 = base64.b64encode(st.session_state.audio_bytes).decode("utf-8")

        payload = {
            "title": st.session_state.title,
            "category": st.session_state.category,
            "filename": st.session_state.filename,
            "audioData": audio_b64,
            "language": "en",
        }

        status.info("📡 Sending audio to transcription engine…")
        progress.progress(50)

        response = requests.post(
            config.N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=config.REQUEST_TIMEOUT,
        )

        progress.progress(85)

        if response.status_code == 200:
            data = response.json()
            st.session_state.transcription = data.get("transcription", "")
            st.session_state.response_data = data
            status.success("✅ Transcription completed successfully!")
            progress.progress(100)
        else:
            st.error(f"❌ Transcription failed (Status: {response.status_code})")
            st.code(response.text)

    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Try a smaller file or increase timeout.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection error. Check your network and n8n webhook URL.")
    except Exception as e:
        st.error("❌ Unexpected error")
        st.exception(e)
    finally:
        st.session_state.submitted = False

def display_transcription_results():
    """Display transcription results and actions"""
    st.divider()
    st.subheader("📝 Transcription Results")

    text = st.session_state.transcription
    response_data = st.session_state.response_data or {}

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Words", len(text.split()))
    col2.metric("Characters", len(text))
    col3.metric("Category", st.session_state.category)
    
    # Show duration if available
    if response_data.get('duration'):
        col4.metric("Duration", response_data['duration'])

    # Transcript Display
    st.text_area(
        "Transcript",
        value=text,
        height=config.TRANSCRIPT_HEIGHT,
        help="Copy or download this transcript"
    )

    # Action Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "⬇️ Download TXT",
            data=text,
            file_name=f"{st.session_state.title}_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )
    
    with col2:
        if response_data.get('drive_link'):
            st.link_button(
                "🔗 Open in Drive",
                response_data['drive_link'],
                use_container_width=True,
            )
    
    with col3:
        if response_data.get('doc_link'):
            st.link_button(
                "📄 Open Doc",
                response_data['doc_link'],
                use_container_width=True,
            )

    # New Session Button
    if st.button("🔄 Start New Recording", use_container_width=True, type="secondary"):
        reset_session()

def reset_session():
    """Reset session state for new recording"""
    keys_to_reset = ["audio_bytes", "transcription", "title", "filename", "stage", "submitted", "response_data"]
    for key in keys_to_reset:
        st.session_state[key] = None
    st.session_state.category = config.DEFAULT_CATEGORY
    st.rerun()

# =========================
# LIBRARY PAGE
# =========================
def render_library_page():
    """Render the recording library with playback"""
    st.title("📚 Recording Library")
    st.markdown("Browse, search, and manage all your recordings")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("❌ Google Sheets not configured.")
        st.info("👈 Please upload your service_account.json file in the sidebar to continue.")
        st.stop()
    
    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        df = read_sheets_data(sheets_service)
        csv = df.drop('Row', axis=1).to_csv(index=False) if not df.empty else ""
        st.download_button(
            "📥 Export CSV",
            csv,
            "recordings.csv",
            "text/csv",
            use_container_width=True,
            disabled=df.empty
        )
    
    df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("📭 No recordings yet. Go to the Record page to create your first transcription!")
        return

    # Filters
    st.subheader("🔍 Filters & Search")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if config.ENABLE_CATEGORY_FILTER and 'Category' in df.columns:
            category_filter = st.multiselect(
                "Category",
                options=sorted(df['Category'].unique().tolist()),
                default=[]
            )
        else:
            category_filter = []
    
    with col2:
        if config.ENABLE_SEARCH:
            search_term = st.text_input("Search titles", "")
        else:
            search_term = ""
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First", "Title A-Z", "Title Z-A", "Most Words"]
        )

    # Apply Filters
    filtered_df = df.copy()
    
    if category_filter:
        filtered_df = filtered_df[filtered_df['Category'].isin(category_filter)]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(search_term, case=False, na=False)
        ]
    
    # Apply Sorting
    if sort_by == "Newest First":
        filtered_df = filtered_df.sort_values('Timestamp', ascending=False)
    elif sort_by == "Oldest First":
        filtered_df = filtered_df.sort_values('Timestamp', ascending=True)
    elif sort_by == "Title A-Z":
        filtered_df = filtered_df.sort_values('Title', ascending=True)
    elif sort_by == "Title Z-A":
        filtered_df = filtered_df.sort_values('Title', ascending=False)
    elif sort_by == "Most Words":
        try:
            filtered_df['Words_Num'] = filtered_df['Words'].astype(str).str.replace(',', '').replace('', '0')
            filtered_df['Words_Num'] = pd.to_numeric(filtered_df['Words_Num'], errors='coerce').fillna(0)
            filtered_df = filtered_df.sort_values('Words_Num', ascending=False)
        except:
            pass

    # Results Summary
    st.write(f"**Showing {len(filtered_df)} of {len(df)} recordings**")
    
    # Display Recordings
    st.divider()
    
    for idx, row in filtered_df.iterrows():
        render_recording_card_library(row, sheets_service, drive_service)

def render_recording_card_library(row, sheets_service, drive_service):
    """Render a single recording card in library with all features"""
    category_class = f"badge-{row['Category'].lower().replace(' ', '')}"
    
    with st.expander(f"🎙️ {row.get('Title', 'Untitled')}", expanded=False):
        # Header with category badge
        st.markdown(f"""
        <span class="category-badge {category_class}">{row.get('Category', 'N/A')}</span>
        """, unsafe_allow_html=True)
        
        # Info grid
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"**📅 Date:** {row.get('Timestamp', 'N/A')}")
        col2.write(f"**📝 Words:** {row.get('Words', 'N/A')}")
        col3.write(f"**⏱️ Duration:** {row.get('Duration', 'N/A')}")
        col4.write(f"**📁 File:** {row.get('Filename', 'N/A')}")
        
        st.divider()
        
        # Audio player inline
        if row.get('Drive Link') and row['Drive Link'].strip():
            play_audio_inline(row['Drive Link'], drive_service, row['Title'])
            st.divider()
        
        # Action Links
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        drive_link = row.get('Drive Link', '')
        doc_link = row.get('Sheet Link', '')
        
        with btn_col1:
            if drive_link and drive_link.strip():
                st.link_button(
                    "🔗 Open in Drive",
                    drive_link,
                    use_container_width=True
                )
        
        with btn_col2:
            if doc_link and doc_link.strip():
                st.link_button(
                    "📄 View Transcript",
                    doc_link,
                    use_container_width=True
                )
        
        with btn_col3:
            if st.button(f"✏️ Edit", key=f"edit_{row['Row']}", use_container_width=True):
                st.session_state.edit_mode = True
                st.session_state.edit_row = row['Row']
                st.rerun()
        
        with btn_col4:
            if st.button(f"🗑️ Delete", key=f"del_{row['Row']}", use_container_width=True, type="secondary"):
                if delete_sheet_row(sheets_service, row['Row']):
                    st.success(f"✅ Deleted!")
                    st.cache_resource.clear()
                    st.cache_data.clear()
                    st.rerun()

# =========================
# ANALYTICS PAGE
# =========================
def render_analytics_page():
    """Render analytics and insights"""
    st.title("📈 Analytics & Insights")
    st.markdown("Deep dive into your recording data and trends")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("❌ Google Sheets not configured.")
        st.info("👈 Connect to Google to view analytics")
        st.stop()
    
    with st.spinner("Loading analytics..."):
        df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("📭 No data yet for analytics")
        return
    
    # Summary metrics
    st.subheader("📊 Summary Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Recordings", len(df))
    
    with col2:
        if 'Words' in df.columns:
            try:
                total_words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
                total_words = pd.to_numeric(total_words, errors='coerce').fillna(0).sum()
                st.metric("Total Words", f"{int(total_words):,}")
            except:
                st.metric("Total Words", "N/A")
    
    with col3:
        if 'Words' in df.columns:
            try:
                words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
                words = pd.to_numeric(words, errors='coerce').fillna(0)
                avg_words = int(words.mean())
                st.metric("Avg Words", f"{avg_words:,}")
            except:
                pass
    
    with col4:
        if 'Category' in df.columns:
            most_common = df['Category'].value_counts().idxmax()
            st.metric("Most Common", most_common)
    
    with col5:
        try:
            from datetime import timedelta
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            week_count = df['Timestamp'].apply(lambda x: x >= week_ago if isinstance(x, str) else False).sum()
            st.metric("This Week", week_count)
        except:
            pass
    
    st.divider()
    
    # Time-based analysis
    st.subheader("📅 Timeline Analysis")
    
    if 'Timestamp' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.date
            daily_counts = df.groupby('Date').size().reset_index(name='Count')
            
            st.line_chart(daily_counts.set_index('Date'), height=300)
        except:
            st.info("Timeline data not available")
    
    st.divider()
    
    # Category analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Category Breakdown")
        if 'Category' in df.columns:
            category_data = df['Category'].value_counts()
            st.bar_chart(category_data, height=400)
    
    with col2:
        st.subheader("📈 Word Count by Recording")
        if 'Words' in df.columns:
            try:
                words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
                words = pd.to_numeric(words, errors='coerce').fillna(0)
                st.bar_chart(words, height=400)
            except:
                st.info("Word count data not available")
    
    st.divider()
    
    # Top recordings
    st.subheader("🏆 Top 10 Longest Recordings")
    if 'Words' in df.columns:
        try:
            df_sorted = df.copy()
            df_sorted['Words_Num'] = df_sorted['Words'].astype(str).str.replace(',', '').replace('', '0')
            df_sorted['Words_Num'] = pd.to_numeric(df_sorted['Words_Num'], errors='coerce').fillna(0)
            top_10 = df_sorted.nlargest(10, 'Words_Num')[['Title', 'Category', 'Words', 'Duration', 'Timestamp']]
            
            st.dataframe(
                top_10,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        except:
            st.info("Unable to calculate top recordings")
    
    st.divider()
    
    # Category insights
    st.subheader("📂 Category Insights")
    if 'Category' in df.columns and 'Words' in df.columns:
        try:
            df_analysis = df.copy()
            df_analysis['Words_Num'] = df_analysis['Words'].astype(str).str.replace(',', '').replace('', '0')
            df_analysis['Words_Num'] = pd.to_numeric(df_analysis['Words_Num'], errors='coerce').fillna(0)
            
            category_stats = df_analysis.groupby('Category').agg({
                'Title': 'count',
                'Words_Num': ['sum', 'mean']
            }).round(0)
            
            category_stats.columns = ['Count', 'Total Words', 'Avg Words']
            
            st.dataframe(
                category_stats,
                use_container_width=True,
                height=300
            )
        except:
            st.info("Category insights not available")

# =========================
# FOOTER
# =========================
def render_footer():
    """Render page footer"""
    st.divider()
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666;">
        <p><strong>🎙️ Audio Transcription Hub</strong></p>
        <p>Powered by Whisper • n8n • Google Drive • Streamlit</p>
        <p style="font-size: 0.9em;">Built for long-form audio transcription and management</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# MAIN APP LOGIC
# =========================
def main():
    """Main application logic"""
    render_sidebar()
    
    if st.session_state.page == "Dashboard":
        render_dashboard_page()
    elif st.session_state.page == "Record":
        render_record_page()
    elif st.session_state.page == "Library":
        render_library_page()
    elif st.session_state.page == "Player":
        render_player_page()
    elif st.session_state.page == "Analytics":
        render_analytics_page()
    
    render_footer()

if __name__ == "__main__":
    main()
