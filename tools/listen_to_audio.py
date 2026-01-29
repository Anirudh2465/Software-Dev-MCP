import speech_recognition as sr
import sys

def listen_to_audio():
    """
    Listens to the default microphone and returns the recognized text.
    Uses Google Speech Recognition API (requires internet).
    """
    recognizer = sr.Recognizer()
    
    print("Adjusting for ambient noise... Please wait.")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... Speak now.")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing audio...")
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out. No speech detected.")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""
        except Exception as e:
            print(f"Error accessing microphone: {e}")
            return ""

if __name__ == "__main__":
    result = listen_to_audio()
    if result:
        print(f"OUTPUT: {result}")
