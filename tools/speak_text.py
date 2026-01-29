import pyttsx3
import sys

def speak_text(text):
    """
    Synthesizes speech from text using pyttsx3.
    """
    print(f"Speaking: {text}")
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return "Speaking complete."
    except Exception as e:
        print(f"Error initializing TTS engine: {e}")
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        speak_text(text)
    else:
        print("Usage: python speak_text.py <text to speak>")
