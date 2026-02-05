import streamlit as st
import requests
import base64
import time
from audio_recorder_streamlit import audio_recorder
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import io
from datetime import datetime

# =========================
# CONFIG
# =========================
N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/60bbcc46-60c2-484f-a51e-aa0067070f68"
GOOGLE_SHEETS_ID = "YOUR_SHEET_ID_HERE"  # Replace with your actual Sheet ID
SERVICE_ACCOUNT_FILE = "service_account.json"  # Place this file in your app directory

# VERY LONG AUDIO SAFE TIMEOUT
REQUEST_TIMEOUT = None  # No client-side timeout

st.set_page_config(
    page_title="Audio Transcription Hub",
    page_icon="🎙️",
    layout="wide",
)

# =========================
# GOOGLE API SETUP
# =========================
@st.cache_resource
def get_google_services():
    """Initialize Google Sheets and Drive services"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        return sheets_service, drive_service
    except Exception as e:
        st.error(f"Failed to initialize Google services: {e}")
        return None, None

# =========================
# GOOGLE SHEETS FUNCTIONS
# =========================
def read_sheets_data(sheets_service):
    """Read all recordings from Google Sheets"""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range='Recordings!A2:H'
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame(columns=['Timestamp', 'Title', 'Category', 'Filename', 
                                        'Duration', 'Words', 'Drive Link', 'Sheet Link'])
        
        df = pd.DataFrame(values, columns=['Timestamp', 'Title', 'Category', 'Filename', 
                                          'Duration', 'Words', 'Drive Link', 'Sheet Link'])
        return df
    except Exception as e:
        st.error(f"Error reading sheets: {e}")
        return pd.DataFrame()

def append_to_sheets(sheets_service, data):
    """Append a new recording to Google Sheets"""
    try:
        values = [[
            data['timestamp'],
            data['title'],
            data['category'],
            data['filename'],
            data['duration'],
            data['words'],
            data['drive_link'],
            data['sheet_link']
        ]]
        
        body = {'values': values}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range='Recordings!A2:H',
            valueInputOption='RAW',
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error writing to sheets: {e}")
        return False

# =========================
# SESSION STATE
# =========================
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "transcription" not in st.session_state:
    st.session_state.transcription = None

if "title" not in st.session_state:
    st.session_state.title = ""

if "category" not in st.session_state:
    st.session_state.category = "Notes"

if "filename" not in st.session_state:
    st.session_state.filename = ""

if "stage" not in st.session_state:
    st.session_state.stage = "idle"

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "page" not in st.session_state:
    st.session_state.page = "Record"

# =========================
# SIDEBAR - DASHBOARD
# =========================
with st.sidebar:
    st.title("📊 Dashboard")
    
    # Page Navigation
    page = st.radio(
        "Navigation",
        ["🎙️ Record", "📚 Library"],
        label_visibility="collapsed"
    )
    
    st.session_state.page = "Record" if "Record" in page else "Library"
    
    st.divider()
    
    # Quick Stats
    sheets_service, drive_service = get_google_services()
    
    if sheets_service:
        df = read_sheets_data(sheets_service)
        
        st.subheader("📈 Statistics")
        
        col1, col2 = st.columns(2)
        col1.metric("Total Recordings", len(df))
        
        if not df.empty and 'Words' in df.columns:
            try:
                total_words = df['Words'].astype(str).str.replace(',', '').astype(int).sum()
                col2.metric("Total Words", f"{total_words:,}")
            except:
                col2.metric("Total Words", "N/A")
        
        st.divider()
        
        # Category breakdown
        if not df.empty and 'Category' in df.columns:
            st.subheader("📂 By Category")
            category_counts = df['Category'].value_counts()
            for cat, count in category_counts.items():
                st.write(f"**{cat}**: {count}")
    else:
        st.warning("Configure service_account.json to enable dashboard")

# =========================
# MAIN CONTENT
# =========================

if st.session_state.page == "Record":
    # =========================
    # RECORDING PAGE
    # =========================
    st.title("🎙️ Audio Transcription Hub")
    st.markdown(
        "Record **as long as you want** or upload large audio files. "
        "No recording timeout. Built for meetings, podcasts, classes, and long dictation."
    )

    st.divider()

    # =========================
    # TITLE AND CATEGORY INPUT
    # =========================
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
            ["Podcast", "Audio Book", "Notes", "Class", "Business Meeting", "Random"],
            index=["Podcast", "Audio Book", "Notes", "Class", "Business Meeting", "Random"].index(st.session_state.category)
        )

    # =========================
    # AUDIO INPUT MODE
    # =========================
    st.subheader("🎧 Audio Input")

    mode = st.radio(
        "Select input method",
        ["Record Audio", "Upload File"],
        horizontal=True,
    )

    audio_data = None
    filename = None

    # =========================
    # RECORD AUDIO (NO LIMITS)
    # =========================
    if mode == "Record Audio":
        st.markdown(
            """
            **Recording notes**
            - Click once to start recording
            - Click again to stop
            - You may record **for hours**
            - Keep the tab open while recording
            """
        )

        audio_bytes = audio_recorder(
            recording_color="#ef4444",
            neutral_color="#2563eb",
            icon_name="microphone",
            icon_size="3x",
        )

        if audio_bytes:
            audio_data = audio_bytes
            filename = "recorded_audio.wav"

            st.audio(audio_bytes)
            st.success("Recording ready")

    # =========================
    # UPLOAD FILE
    # =========================
    else:
        uploaded = st.file_uploader(
            "Upload audio file",
            type=["wav", "mp3", "m4a", "mp4", "webm", "mpeg"],
            help="Large files supported (depends on server limits)",
        )

        if uploaded:
            audio_data = uploaded.read()
            filename = uploaded.name

            st.audio(audio_data)
            st.success("File loaded")

    # =========================
    # AUDIO INSPECTION
    # =========================
    if audio_data:
        size_mb = round(len(audio_data) / (1024 * 1024), 2)
        st.info(f"Audio size: **{size_mb} MB**")

    # =========================
    # SUBMIT
    # =========================
    can_submit = bool(audio_data and st.session_state.title)

    submit = st.button(
        "🚀 Transcribe Audio",
        type="primary",
        disabled=not can_submit,
        use_container_width=True,
    )

    # =========================
    # TRANSCRIPTION PIPELINE
    # =========================
    if submit:
        st.session_state.audio_bytes = audio_data
        st.session_state.filename = filename
        st.session_state.stage = "processing"
        st.session_state.submitted = True

    if st.session_state.submitted and st.session_state.audio_bytes:

        progress = st.progress(0)
        status = st.empty()

        try:
            status.info("Encoding audio (this may take time for very large files)…")
            progress.progress(20)

            audio_b64 = base64.b64encode(
                st.session_state.audio_bytes
            ).decode("utf-8")

            payload = {
                "title": st.session_state.title,
                "category": st.session_state.category,
                "filename": st.session_state.filename,
                "audioData": audio_b64,
                "language": "en",
            }

            status.info("Sending audio to transcription engine…")
            progress.progress(50)

            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,  # NO CLIENT TIMEOUT
            )

            progress.progress(85)

            if response.status_code == 200:
                data = response.json()
                st.session_state.transcription = data.get("transcription", "")
                status.success("Transcription completed")
                progress.progress(100)
            else:
                st.error("Transcription failed")
                st.code(response.text)

        except Exception as e:
            st.error("Unexpected error")
            st.exception(e)

        finally:
            st.session_state.submitted = False

    # =========================
    # RESULTS
    # =========================
    if st.session_state.transcription:
        st.divider()
        st.subheader("📝 Transcription")

        text = st.session_state.transcription

        col1, col2, col3 = st.columns(3)
        col1.metric("Words", len(text.split()))
        col2.metric("Characters", len(text))
        col3.metric("Category", st.session_state.category)

        st.text_area(
            "Transcript",
            value=text,
            height=400,
        )

        st.download_button(
            "⬇️ Download Transcript",
            data=text,
            file_name=f"{st.session_state.title}_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )

        if st.button("🔄 New Session", use_container_width=True):
            for key in [
                "audio_bytes",
                "transcription",
                "title",
                "filename",
                "stage",
                "submitted",
            ]:
                st.session_state[key] = None
            st.session_state.category = "Notes"
            st.rerun()

    # =========================
    # FOOTER
    # =========================
    st.divider()
    st.caption(
        "Built for long-form recording • Whisper • n8n • Google Drive • Streamlit"
    )

else:
    # =========================
    # LIBRARY PAGE
    # =========================
    st.title("📚 Recording Library")
    
    sheets_service, drive_service = get_google_services()
    
    if not sheets_service:
        st.error("Google Sheets not configured. Please add service_account.json file.")
        st.stop()
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()
    
    df = read_sheets_data(sheets_service)
    
    if df.empty:
        st.info("No recordings yet. Go to the Record page to create your first transcription!")
    else:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            category_filter = st.multiselect(
                "Filter by Category",
                options=df['Category'].unique().tolist() if 'Category' in df.columns else [],
                default=[]
            )
        
        with col2:
            search_term = st.text_input("Search titles", "")
        
        # Apply filters
        filtered_df = df.copy()
        
        if category_filter:
            filtered_df = filtered_df[filtered_df['Category'].isin(category_filter)]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['Title'].str.contains(search_term, case=False, na=False)]
        
        st.write(f"**Showing {len(filtered_df)} of {len(df)} recordings**")
        
        # Display recordings
        for idx, row in filtered_df.iterrows():
            with st.expander(f"🎙️ {row['Title']} ({row['Category']})"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Date:** {row['Timestamp']}")
                col2.write(f"**Words:** {row['Words']}")
                col3.write(f"**Duration:** {row.get('Duration', 'N/A')}")
                
                # Links
                link_col1, link_col2 = st.columns(2)
                
                if row.get('Drive Link'):
                    link_col1.markdown(f"[🔗 Open Audio in Drive]({row['Drive Link']})")
                
                if row.get('Sheet Link'):
                    link_col2.markdown(f"[📄 View Transcript]({row['Sheet Link']})")
                
                # Audio playback (if Drive link available)
                if row.get('Drive Link') and drive_service:
                    try:
                        # Extract file ID from Drive link
                        file_id = row['Drive Link'].split('/d/')[1].split('/')[0] if '/d/' in row['Drive Link'] else None
                        
                        if file_id:
                            st.caption("⏯️ Audio Playback")
                            # Note: Direct playback from Drive requires special handling
                            st.info("Click the Drive link above to play audio")
                    except:
                        pass
