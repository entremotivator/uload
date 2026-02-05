import streamlit as st
import requests
import base64
from audio_recorder_streamlit import audio_recorder
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime
import json
import os
import config  # Import our configuration

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
)

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
# GOOGLE SHEETS FUNCTIONS
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
        return df
    except Exception as e:
        st.error(f"Error reading sheets: {e}")
        return pd.DataFrame()

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
        "page": "Record",
        "response_data": None,
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
        st.title("📊 Dashboard")
        
        # Google Authentication Section
        render_google_auth_section()
        
        st.divider()
        
        # Page Navigation
        page = st.radio(
            "Navigation",
            ["🎙️ Record", "📚 Library"],
            label_visibility="collapsed"
        )
        
        st.session_state.page = "Record" if "Record" in page else "Library"
        
        st.divider()
        
        if config.ENABLE_DASHBOARD:
            render_dashboard_stats()

def render_google_auth_section():
    """Render Google authentication/login section in sidebar"""
    st.subheader("🔐 Google Login")
    
    # Check if already authenticated
    sheets_service, drive_service = get_google_services()
    
    if sheets_service:
        st.success("✅ Connected to Google")
        
        # Show which method is being used
        if 'google_credentials' in st.session_state and st.session_state.google_credentials:
            st.caption("Using uploaded credentials")
        elif os.path.exists(config.SERVICE_ACCOUNT_FILE):
            st.caption("Using local service_account.json")
        
        # Logout button
        if st.button("🚪 Disconnect", use_container_width=True):
            if 'google_credentials' in st.session_state:
                del st.session_state.google_credentials
            st.cache_resource.clear()
            st.rerun()
    else:
        st.warning("⚠️ Not connected")
        
        # File upload option
        with st.expander("📤 Upload Service Account JSON", expanded=True):
            uploaded_json = st.file_uploader(
                "Choose your service_account.json file",
                type=['json'],
                help="Upload the service account JSON file from Google Cloud Console",
                label_visibility="collapsed"
            )
            
            if uploaded_json is not None:
                try:
                    # Read and parse the JSON
                    credentials_dict = json.load(uploaded_json)
                    
                    # Validate required fields
                    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                    if all(field in credentials_dict for field in required_fields):
                        st.session_state.google_credentials = credentials_dict
                        st.success("✅ Credentials loaded successfully!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("❌ Invalid service account file - missing required fields")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file")
                except Exception as e:
                    st.error(f"❌ Error loading credentials: {e}")
        
        # Instructions
        with st.expander("📖 Setup Instructions"):
            st.markdown("""
            **To get your service account JSON:**
            
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Select your project
            3. Go to **IAM & Admin > Service Accounts**
            4. Click on your service account
            5. Go to **Keys** tab
            6. Click **Add Key > Create New Key**
            7. Choose **JSON** format
            8. Upload the downloaded file here
            
            Or place the file as `service_account.json` in the app directory.
            """)


def render_dashboard_stats():
    """Render dashboard statistics in sidebar"""
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.info("👆 Connect to Google to view statistics")
        return
    
    with st.spinner("Loading stats..."):
        df = read_sheets_data(sheets_service)
    
    st.subheader("📈 Statistics")
    
    col1, col2 = st.columns(2)
    col1.metric("Total Recordings", len(df))
    
    if not df.empty and 'Words' in df.columns:
        try:
            # Clean and convert words column
            total_words = df['Words'].astype(str).str.replace(',', '').replace('', '0')
            total_words = pd.to_numeric(total_words, errors='coerce').fillna(0).sum()
            col2.metric("Total Words", f"{int(total_words):,}")
        except:
            col2.metric("Total Words", "N/A")
    
    st.divider()
    
    # Category breakdown
    if not df.empty and 'Category' in df.columns and config.ENABLE_CATEGORY_FILTER:
        st.subheader("📂 By Category")
        category_counts = df['Category'].value_counts()
        for cat, count in category_counts.items():
            st.write(f"**{cat}**: {count}")
    
    # Recent recordings
    if not df.empty and len(df) > 0:
        st.divider()
        st.subheader("🕐 Recent")
        recent = df.head(5)
        for idx, row in recent.iterrows():
            with st.expander(f"📝 {row.get('Title', 'Untitled')[:30]}..."):
                st.caption(f"Category: {row.get('Category', 'N/A')}")
                st.caption(f"Date: {row.get('Timestamp', 'N/A')}")

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
    """Render the recording library/dashboard"""
    st.title("📚 Recording Library")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("❌ Google Sheets not configured.")
        st.info("👈 Please upload your service_account.json file in the sidebar to continue.")
        st.stop()
    
    # Refresh Button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    with col2:
        if st.button("📥 Export CSV", use_container_width=True):
            df = read_sheets_data(sheets_service)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "recordings.csv",
                "text/csv",
                use_container_width=True
            )
    
    df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("📭 No recordings yet. Go to the Record page to create your first transcription!")
        return

    # Filters
    st.subheader("🔍 Filters")
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
            ["Newest First", "Oldest First", "Title A-Z", "Title Z-A"]
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

    # Results Summary
    st.write(f"**Showing {len(filtered_df)} of {len(df)} recordings**")
    
    # Display Recordings
    st.divider()
    
    for idx, row in filtered_df.iterrows():
        render_recording_card(row)

def render_recording_card(row):
    """Render a single recording card"""
    with st.expander(f"🎙️ {row.get('Title', 'Untitled')} ({row.get('Category', 'N/A')})"):
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"**Date:** {row.get('Timestamp', 'N/A')}")
        col2.write(f"**Words:** {row.get('Words', 'N/A')}")
        col3.write(f"**Duration:** {row.get('Duration', 'N/A')}")
        col4.write(f"**File:** {row.get('Filename', 'N/A')}")
        
        # Action Links
        link_col1, link_col2 = st.columns(2)
        
        drive_link = row.get('Drive Link', '')
        doc_link = row.get('Sheet Link', '')
        
        if drive_link and drive_link.strip():
            with link_col1:
                st.link_button(
                    "🎵 Open Audio",
                    drive_link,
                    use_container_width=True
                )
        
        if doc_link and doc_link.strip():
            with link_col2:
                st.link_button(
                    "📄 View Transcript",
                    doc_link,
                    use_container_width=True
                )

# =========================
# FOOTER
# =========================
def render_footer():
    """Render page footer"""
    st.divider()
    st.caption(
        "Built for long-form recording • Whisper • n8n • Google Drive • Streamlit"
    )

# =========================
# MAIN APP LOGIC
# =========================
def main():
    """Main application logic"""
    render_sidebar()
    
    if st.session_state.page == "Record":
        render_record_page()
    else:
        render_library_page()
    
    render_footer()

if __name__ == "__main__":
    main()
