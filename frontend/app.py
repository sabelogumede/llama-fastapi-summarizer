# Streamlit frontend for local LLaMA2-powered text summarizer
# Features:
# - Live input word/character count
# - AI-generated summary
# - Summary word/character count
# - "Clear Input" button
# - Full error handling and UX polish

import streamlit as st
import requests

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LLaMA FastAPI Text Summarizer",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto"
)

# -----------------------------------------------------------------------------
# App Title and Description
# -----------------------------------------------------------------------------
st.title("LLaMA FastAPI Text Summarizer")
st.markdown(
    """
    ✏️ **Provide your text for summarization**  
    Simply paste any article, document, or message below and click **"Summarize"**.

    ⏳ **Please be patient**, summarization can takes **10–60 seconds**, depending on the length of your text.  
    The AI is running locally on your machine, so everything stays **private and secure**.  
    No data is sent to the cloud, your privacy is guaranteed.
    """
)

# -----------------------------------------------------------------------------
# Input Section with Live Word & Character Count
# -----------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### Enter the text you want summarized:")

# Get user input (can be None on first load)
raw_input = st.text_area(
    "Input text area",
    value=st.session_state.get("input_text", ""),
    height=200,
    placeholder="Paste an article, email, report, or any long text here...",
    label_visibility="collapsed"
)

# ✅ Safely handle None and normalize input
current_text = (raw_input or "").strip()
st.session_state.input_text = current_text  # Save clean version

# ✅ Compute counts for input
input_word_count = len(current_text.split()) if current_text else 0
input_char_count = len(current_text)

# ✅ Display live input count below the text area
st.markdown(
    
    
    f"<p style='text-align: right; color: #666; font-size: 0.9em; margin-top: -10px;'>"
    f"Words: {input_word_count} | Characters: {input_char_count}"
    "</p>",
    unsafe_allow_html=True
   
)

# -----------------------------------------------------------------------------
# Initialize Session State for Summary
# -----------------------------------------------------------------------------
if "summary_generated" not in st.session_state:
    st.session_state.summary_generated = False
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""

# -----------------------------------------------------------------------------
# Summarize Button and Logic
# -----------------------------------------------------------------------------
if st.button("✨ Summarize", type="primary"):
    if not current_text:
        st.error("❌ Please enter some text to summarize.")
    elif len(current_text) < 10:
        st.error("❌ Text must be at least 10 characters long.")
    else:
        with st.spinner("🧠 AI is reading and summarizing your text..."):
            try:
                response = requests.post(
                    url="http://localhost:8000/summarize/",
                    json={"text": current_text},
                    timeout=65
                )

                if response.status_code == 200:
                    summary = response.json().get("summary", "").strip()
                    if not summary:
                        st.error("❌ The AI returned an empty summary. Please try again.")
                    else:
                        # ✅ Save summary and mark as generated
                        st.session_state.summary_text = summary
                        st.session_state.summary_generated = True
                else:
                    try:
                        error_detail = response.json().get("detail", "Unknown error")
                    except:
                        error_detail = response.text
                    st.error(f"❌ Failed to generate summary: {error_detail}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Is FastAPI running at http://localhost:8000?")
            except requests.exceptions.Timeout:
                st.error("⏰ Request timed out. Try a shorter text.")
            except Exception as e:
                st.error(f"💥 An unexpected error occurred: {e}")

# -----------------------------------------------------------------------------
# Display Summary and Its Word/Character Count
# -----------------------------------------------------------------------------
if st.session_state.summary_generated:
    st.subheader("✅ Summary")
    st.write(st.session_state.summary_text)

    # ✅ Compute summary word and character count
    summary_word_count = len(st.session_state.summary_text.split())
    summary_char_count = len(st.session_state.summary_text)

    # ✅ Display count in a clean, right-aligned, subtle style
    st.markdown(
        f"<p style='text-align: right; color: #666; font-size: 0.9em; margin-top: -10px;'>"
        f"Summary — Words: {summary_word_count} | Characters: {summary_char_count}"
        "</p>",
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# Clear Input Button (Appears only after summarization)
# -----------------------------------------------------------------------------
if st.session_state.summary_generated and st.session_state.input_text:
    if st.button("🗑️ Clear Summary + Input", type="secondary"):
        # Reset all session state fields
        st.session_state.input_text = ""
        st.session_state.summary_text = ""
        st.session_state.summary_generated = False
        st.rerun()  # Immediately refresh the UI

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("🔒 Your data stays local. No text is sent to external servers.")