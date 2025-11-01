import speech_recognition as sr
from gtts import gTTS
import os

def recognize_speech(language='en-US'):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak something...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return "Sorry, I didn't catch that."
    except sr.RequestError:
        return "Speech recognition service not available."

def text_to_speech(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    tts.save("output.mp3")
    os.system("start output.mp3")
