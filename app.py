import streamlit as st
import requests
import base64
from audio_recorder_streamlit import audio_recorder
import io

# Configuration
N8N_WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook-test/60bbcc46-60c2-484f-a51e-aa0067070f68"

st.set_page_config(
    page_title="Audio Transcription App",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Audio Transcription")
st.markdown("Upload or record an audio file to transcribe it using OpenAI Whisper")

# Initialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = None
if 'title' not in st.session_state:
    st.session_state.title = None
if 'audio_source' not in st.session_state:
    st.session_state.audio_source = None

# Input section
with st.container():
    st.subheader("Audio Input")
    
    # Title input
    title = st.text_input(
        "Title",
        placeholder="Enter a title for your audio file...",
        help="Give your audio recording a descriptive title"
    )
    
    # Choose between upload and record
    audio_input_type = st.radio(
        "Select audio input method:",
        ["Upload File", "Record Audio"],
        horizontal=True
    )
    
    audio_data = None
    filename = None
    
    if audio_input_type == "Upload File":
        # Audio file uploader
        audio_file = st.file_uploader(
            "Choose an audio file",
            type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
            help="Supported formats: MP3, MP4, MPEG, M4A, WAV, WebM"
        )
        
        if audio_file:
            audio_data = audio_file.read()
            filename = audio_file.name
            st.audio(audio_data, format=f'audio/{audio_file.type.split("/")[1]}')
    
    else:  # Record Audio
        st.markdown("Click the microphone to start/stop recording:")
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="3x",
        )
        
        if audio_bytes:
            audio_data = audio_bytes
            filename = "recorded_audio.wav"
            st.audio(audio_bytes, format='audio/wav')
            st.success("✅ Recording captured!")
    
    # Transcribe button
    transcribe_btn = st.button(
        "🎯 Transcribe Audio",
        type="primary",
        disabled=not (audio_data and title),
        use_container_width=True
    )

# Process transcription
if transcribe_btn and audio_data and title:
    with st.spinner("🔄 Transcribing your audio file..."):
        try:
            # Encode audio file to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare the payload - n8n webhook automatically wraps in body
            payload = {
                "title": title,
                "filename": filename,
                "audioData": audio_base64,
                "language": "en"
            }
            
            # Send to n8n webhook
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2 minutes timeout for longer audio files
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                st.session_state.transcription = result.get('transcription', '')
                st.session_state.title = result.get('title', title)
                st.session_state.audio_source = audio_input_type
                st.success("✅ Transcription completed successfully!")
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                with st.expander("Show debug info"):
                    st.json({"status_code": response.status_code, "response": response.text})
                
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The audio file might be too long.")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
            st.info("💡 Make sure the n8n workflow is activated and the webhook URL is correct.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            with st.expander("Show debug info"):
                st.exception(e)

# Display results
if st.session_state.transcription:
    st.divider()
    st.subheader("📝 Transcription Result")
    
    # Display title
    st.markdown(f"**Title:** {st.session_state.title}")
    
    # Display transcription in a text area
    st.text_area(
        "Transcription",
        value=st.session_state.transcription,
        height=300,
        help="The transcribed text from your audio file"
    )
    
    # Download button for transcription
    st.download_button(
        label="📥 Download Transcription",
        data=st.session_state.transcription,
        file_name=f"{st.session_state.title}_transcription.txt",
        mime="text/plain",
        use_container_width=True
    )
    
    # Clear button
    if st.button("🔄 Start New Transcription", use_container_width=True):
        st.session_state.transcription = None
        st.session_state.title = None
        st.rerun()

# Footer with instructions
st.divider()
with st.expander("ℹ️ Setup Instructions"):
    st.markdown("""
    ### Configuration Steps:
    
    1. **n8n Setup:**
       - Import the workflow JSON into your n8n instance
       - Configure your OpenAI API credentials in the OpenAI Whisper node
       - Activate the workflow
       - The webhook URL is already configured: 
         `https://agentonline-u29564.vm.elestio.app/webhook-test/60bbcc46-60c2-484f-a51e-aa0067070f68`
    
    2. **Streamlit Setup:**
       - Install requirements: `pip install -r requirements.txt`
       - Run: `streamlit run streamlit_app.py`
    
    3. **OpenAI API:**
       - You need an OpenAI API key with access to Whisper
       - Add it to your n8n credentials
    
    ### Audio Input Options:
    
    **Upload File:**
    - MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
    - Maximum file size depends on your OpenAI plan
    
    **Record Audio:**
    - Click the microphone icon to start recording
    - Click again to stop recording
    - Audio is captured as WAV format
    - Perfect for quick voice notes and dictation
    
    ### Tips:
    - Give your audio a descriptive title before transcribing
    - For best results, use clear audio with minimal background noise
    - Longer audio files may take more time to transcribe
    - You can download the transcription as a text file
    """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Powered by OpenAI Whisper & n8n</div>",
    unsafe_allow_html=True
)
