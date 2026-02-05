import streamlit as st
import requests
import base64
import time
from audio_recorder_streamlit import audio_recorder

# =========================
# CONFIG
# =========================
N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/60bbcc46-60c2-484f-a51e-aa0067070f68"

# VERY LONG AUDIO SAFE TIMEOUT
REQUEST_TIMEOUT = None  # No client-side timeout

st.set_page_config(
    page_title="Unlimited Audio Transcription",
    page_icon="🎙️",
    layout="centered",
)

# =========================
# SESSION STATE
# =========================
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "transcription" not in st.session_state:
    st.session_state.transcription = None

if "title" not in st.session_state:
    st.session_state.title = ""

if "filename" not in st.session_state:
    st.session_state.filename = ""

if "stage" not in st.session_state:
    st.session_state.stage = "idle"

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# =========================
# HEADER
# =========================
st.title("🎙️ Unlimited Audio Transcription")
st.markdown(
    "Record **as long as you want** or upload large audio files. "
    "No recording timeout. Built for meetings, podcasts, classes, and long dictation."
)

st.divider()

# =========================
# TITLE INPUT
# =========================
st.subheader("📝 Audio Details")

st.session_state.title = st.text_input(
    "Title",
    value=st.session_state.title,
    placeholder="Podcast episode, class session, coaching call, meeting notes…",
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

    col1, col2 = st.columns(2)
    col1.metric("Words", len(text.split()))
    col2.metric("Characters", len(text))

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
        st.rerun()

# =========================
# FOOTER
# =========================
st.divider()
st.caption(
    "Built for long-form recording • Whisper • n8n • Streamlit"
)
