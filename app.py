import streamlit as st
import requests
import base64
from pathlib import Path

# Configuration
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/60bbcc46-60c2-484f-a51e-aa0067070f68"

st.set_page_config(
    page_title="Audio Transcription App",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Audio Transcription")
st.markdown("Upload an audio file to transcribe it using OpenAI Whisper")

# Initialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = None
if 'title' not in st.session_state:
    st.session_state.title = None

# Input section
with st.container():
    st.subheader("Upload Audio")
    
    # Title input
    title = st.text_input(
        "Title",
        placeholder="Enter a title for your audio file...",
        help="Give your audio recording a descriptive title"
    )
    
    # Audio file uploader
    audio_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
        help="Supported formats: MP3, MP4, MPEG, M4A, WAV, WebM"
    )
    
    # Transcribe button
    transcribe_btn = st.button(
        "🎯 Transcribe Audio",
        type="primary",
        disabled=not (audio_file and title),
        use_container_width=True
    )

# Process transcription
if transcribe_btn and audio_file and title:
    with st.spinner("🔄 Transcribing your audio file..."):
        try:
            # Read the audio file
            audio_bytes = audio_file.read()
            
            # Encode audio file to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Prepare the payload
            payload = {
                "title": title,
                "filename": audio_file.name,
                "data": audio_base64,
                "mimeType": audio_file.type
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
                st.success("✅ Transcription completed successfully!")
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The audio file might be too long.")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

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
       - Copy the webhook URL
    
    2. **Streamlit Setup:**
       - Update the `N8N_WEBHOOK_URL` variable at the top of this file
       - Replace with your actual n8n webhook URL
       - Install requirements: `pip install streamlit requests`
       - Run: `streamlit run app.py`
    
    3. **OpenAI API:**
       - You need an OpenAI API key with access to Whisper
       - Add it to your n8n credentials
    
    ### Supported Audio Formats:
    - MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
    - Maximum file size depends on your OpenAI plan
    """)
