import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os
import datetime
import re
from collections import Counter
from database import LinguamateDB

st.set_page_config(page_title="Linguamate AI Storage", page_icon="🤖", layout="centered")

# Initialize database
@st.cache_resource
def init_db():
    return LinguamateDB()

db = init_db()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #ffffff 0%, #ffebee 30%, #ffffff 70%, #fce4ec 100%);
    font-family: 'Arial', sans-serif;
}
.main-header {
    background: linear-gradient(90deg, #d32f2f, #f44336);
    color: white;
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 8px 25px rgba(211, 47, 47, 0.4);
}
.stButton>button {
    background: linear-gradient(45deg, #d32f2f, #f44336);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 15px 35px;
    font-size: 18px;
    font-weight: bold;
    transition: all 0.3s ease;
    box-shadow: 0 6px 20px rgba(211, 47, 47, 0.3);
}
.stButton>button:hover {
    background: linear-gradient(45deg, #b71c1c, #d32f2f);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(211, 47, 47, 0.5);
}
.result-box {
    background: linear-gradient(135deg, #ffffff, #ffebee);
    border-left: 6px solid #f44336;
    border-radius: 15px;
    box-shadow: 0 6px 20px rgba(183, 28, 28, 0.2);
    padding: 25px;
    margin: 20px 0;
}
.ml-feature {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #f44336;
}
.storage-box {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #f44336;
}
</style>
""", unsafe_allow_html=True)

# Global Languages
GLOBAL_LANGUAGES = {
    "🇬🇧 English": {"speech": "en-US", "translate": "en", "tts": "en"},
    "🇪🇸 Spanish": {"speech": "es-ES", "translate": "es", "tts": "es"},
    "🇫🇷 French": {"speech": "fr-FR", "translate": "fr", "tts": "fr"},
    "🇩🇪 German": {"speech": "de-DE", "translate": "de", "tts": "de"},
    "🇮🇳 Hindi": {"speech": "hi-IN", "translate": "hi", "tts": "hi"},
    "🇮🇳 Bhojpuri": {"speech": "hi-IN", "translate": "bho", "tts": "hi"},
    "🇮🇳 Punjabi": {"speech": "pa-IN", "translate": "pa", "tts": "hi"},
    "🇮🇳 Tamil": {"speech": "ta-IN", "translate": "ta", "tts": "ta"},
    "🇮🇳 Telugu": {"speech": "te-IN", "translate": "te", "tts": "te"},
    "🇮🇳 Kannada": {"speech": "kn-IN", "translate": "kn", "tts": "kn"},
    "🇮🇳 Malayalam": {"speech": "ml-IN", "translate": "ml", "tts": "ml"},
    "🇨🇳 Chinese": {"speech": "zh-CN", "translate": "zh", "tts": "zh"},
    "🇯🇵 Japanese": {"speech": "ja-JP", "translate": "ja", "tts": "ja"},
    "🇰🇷 Korean": {"speech": "ko-KR", "translate": "ko", "tts": "ko"},
    "🇸🇦 Arabic": {"speech": "ar-SA", "translate": "ar", "tts": "ar"},
    "🇧🇷 Portuguese": {"speech": "pt-BR", "translate": "pt", "tts": "pt"},
}

# ML Functions
def analyze_text_complexity(text):
    words = len(text.split())
    chars = len(text)
    if words > 10 and chars > 50:
        return "🔥 Complex"
    elif words > 5:
        return "⚡ Medium"
    else:
        return "✨ Simple"

def detect_sentiment_ai(text):
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'like', 'happy', 'best', 'beautiful', 'fantastic']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'worst', 'horrible', 'angry', 'disappointed']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "😊 Positive"
    elif neg_count > pos_count:
        return "😔 Negative"
    else:
        return "😐 Neutral"

def get_ai_confidence(text):
    word_count = len(text.split())
    char_count = len(text)
    has_punctuation = bool(re.search(r'[.!?]', text))
    
    base_score = min(word_count * 8, 85)
    if has_punctuation:
        base_score += 5
    if char_count > 20:
        base_score += 5
    
    return min(base_score, 95)

def ml_language_prediction(text):
    patterns = {
        'English': ['the', 'and', 'is', 'to', 'a'],
        'Hindi': ['है', 'का', 'में', 'को', 'से'],
        'Bhojpuri': ['बा', 'हऽ', 'करे', 'के', 'से'],
        'Spanish': ['el', 'la', 'de', 'que', 'y'],
        'French': ['le', 'de', 'et', 'à', 'un']
    }
    
    text_lower = text.lower()
    scores = {}
    for lang, words in patterns.items():
        score = sum(1 for word in words if word in text_lower)
        scores[lang] = score
    
    if scores:
        predicted = max(scores, key=scores.get)
        return f"🔍 {predicted}" if scores[predicted] > 0 else "🔍 Unknown"
    return "🔍 Unknown"

def record_speech_with_ml(language_code):
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🤖 AI Recording with ML Analysis...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=5)
            
            # Save audio file
            audio_filename = f"recordings/audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            os.makedirs("recordings", exist_ok=True)
            
            with open(audio_filename, "wb") as f:
                f.write(audio.get_wav_data())
            
            try:
                text = r.recognize_google(audio, language=language_code)
                return text, audio_filename
            except sr.UnknownValueError:
                return None, audio_filename
            except sr.RequestError as e:
                st.error(f"Speech recognition service error: {e}")
                return None, audio_filename
    except Exception as e:
        st.error(f"Recording error: {e}")
        return None, None

# ---- App Header ----
st.markdown('<div class="main-header"><h1>🤖 Linguamate AI Storage</h1><h3>ML-Powered Translation with Backend Storage</h3></div>', unsafe_allow_html=True)

# ---- Language Selection ----
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("🎤 Speak in:", list(GLOBAL_LANGUAGES.keys()))
with col2:
    target_lang = st.selectbox("🌐 Translate to:", list(GLOBAL_LANGUAGES.keys()), index=1)

# ML Features Toggle
show_ai_analysis = st.checkbox("🧠 Show AI Analysis & Store ML Data", value=True)

# ---- Main Interface ----
if st.button("🤖 AI Record & Store with ML"):
    if source_lang == target_lang:
        st.warning("Please select different languages.")
    else:
        user_input, audio_path = record_speech_with_ml(GLOBAL_LANGUAGES[source_lang]["speech"])
        if user_input:
            st.markdown(f"<div class='result-box'><h5>🗣 AI Recorded ({source_lang}):</h5><p>{user_input}</p></div>", unsafe_allow_html=True)
            
            # ML Analysis
            complexity = analyze_text_complexity(user_input)
            sentiment = detect_sentiment_ai(user_input)
            confidence = get_ai_confidence(user_input)
            predicted = ml_language_prediction(user_input)
            text_length = len(user_input)
            word_count = len(user_input.split())
            
            if show_ai_analysis:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="ml-feature"><b>🔍 Complexity:</b><br>{complexity}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="ml-feature"><b>💭 Sentiment:</b><br>{sentiment}</div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="ml-feature"><b>🎯 AI Score:</b><br>{confidence}%</div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="ml-feature"><b>🤖 Detected:</b><br>{predicted}</div>', unsafe_allow_html=True)
            
            try:
                translated = GoogleTranslator(
                    source=GLOBAL_LANGUAGES[source_lang]["translate"], 
                    target=GLOBAL_LANGUAGES[target_lang]["translate"]
                ).translate(user_input)
                
                st.markdown(f"<div class='result-box'><h5>🤖 AI Translation ({target_lang}):</h5><p>{translated}</p></div>", unsafe_allow_html=True)
                
                # Generate and save TTS
                tts = gTTS(translated, lang=GLOBAL_LANGUAGES[target_lang]["tts"])
                tts_filename = f"recordings/tts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                tts.save(tts_filename)
                st.audio(tts_filename, format='audio/mp3')
                
                # Save to database with ML data
                recording_id = db.save_recording(user_input, translated, source_lang, target_lang, audio_path)
                if recording_id:
                    db.save_ml_analysis(recording_id, complexity, sentiment, confidence, predicted, text_length, word_count)
                    db.update_user_stats(source_lang, target_lang)
                    st.success("✅ Recording & ML Analysis stored in database!")
                else:
                    st.warning("⚠️ Translation completed but database storage failed.")
                    
            except Exception as e:
                st.error(f"AI Translation failed: {str(e)}")
        else:
            st.error("AI couldn't understand. Please try again.")

# ---- Storage & ML Dashboard ----
st.markdown("### 🤖 AI Storage & ML Dashboard")

tab1, tab2, tab3 = st.tabs(["Recent Recordings", "ML Insights", "Storage Stats"])

with tab1:
    recent_recordings = db.get_recent_recordings(5)
    if recent_recordings:
        for recording in recent_recordings:
            with st.expander(f"🎙 {recording[1][:50]}... ({recording[6]})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Original ({recording[3]}):** {recording[1]}")
                    st.write(f"**Translated ({recording[4]}):** {recording[2]}")
                with col2:
                    st.write(f"**Date:** {recording[6]}")
                    if os.path.exists(recording[5]):
                        st.audio(recording[5])
    else:
        st.info("No recordings yet. Start translating!")

with tab2:
    if st.button("🧠 Generate ML Insights"):
        avg_stats, sentiment_stats, complexity_stats = db.get_ml_insights()
        if avg_stats and avg_stats[0] is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**🤖 ML Analytics:**")
                st.write(f"• Avg Confidence: {avg_stats[0]:.1f}%")
                st.write(f"• Avg Text Length: {avg_stats[1]:.1f} chars")
                st.write(f"• Avg Word Count: {avg_stats[2]:.1f} words")
            
            with col2:
                st.write("**😊 Sentiment Distribution:**")
                for sentiment, count in sentiment_stats:
                    st.write(f"• {sentiment}: {count} times")
                
                st.write("**🔥 Complexity Distribution:**")
                for complexity, count in complexity_stats:
                    st.write(f"• {complexity}: {count} times")
        else:
            st.info("No ML data available yet.")

with tab3:
    recordings = db.get_all_recordings()
    if recordings:
        st.write(f"**📁 Total Stored Recordings:** {len(recordings)}")
        if os.path.exists('linguamate_storage.db'):
            st.write(f"**💾 Database Size:** {os.path.getsize('linguamate_storage.db')} bytes")
        if os.path.exists('recordings'):
            audio_files = [f for f in os.listdir('recordings') if f.endswith('.wav')]
            tts_files = [f for f in os.listdir('recordings') if f.endswith('.mp3')]
            st.write(f"**🎵 Audio Files:** {len(audio_files)}")
            st.write(f"**🔊 TTS Files:** {len(tts_files)}")

# ---- Footer ----
st.markdown("---")
st.markdown('<div style="text-align: center; color: #d32f2f; font-weight: bold;">🤖 AI + ML + Storage | 15+ Languages | Linguamate AI Storage v8.0</div>', unsafe_allow_html=True)