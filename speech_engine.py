import os
import threading
import queue
import speech_recognition as sr
import pyttsx3

def get_best_microphone_index():
    """Finds the best physical microphone index (e.g. Intel Array or Realtek)."""
    try:
        names = sr.Microphone.list_microphone_names()
        # Look for active digital mic array
        for idx, name in enumerate(names):
            if "microphone array" in name.lower() and "intel" in name.lower():
                return idx
        for idx, name in enumerate(names):
            if "microphone array" in name.lower():
                return idx
        for idx, name in enumerate(names):
            if "realtek" in name.lower() and "input" in name.lower():
                return idx
    except Exception:
        pass
    return None

class SpeechEngine:
    def __init__(self, device_index=None):
        self.recognizer = sr.Recognizer()
        
        # High sensitivity & fast reaction settings
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

        # Select microphone device index
        self.device_index = device_index if device_index is not None else get_best_microphone_index()
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
        # Background TTS thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def set_device_index(self, index: int | None):
        self.device_index = index

    def _tts_worker(self):
        """Worker thread for thread-safe text-to-speech."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            engine.setProperty('volume', 1.0)
            
            voices = engine.getProperty('voices')
            for v in voices:
                if "David" in v.name or "Mark" in v.name or "English" in v.name:
                    engine.setProperty('voice', v.id)
                    break

            while True:
                text = self.speech_queue.get()
                if text is None:
                    break
                self.is_speaking = True
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"[TTS Error] {e}")
                finally:
                    self.is_speaking = False
                    self.speech_queue.task_done()
        except Exception as e:
            print(f"[TTS Worker Error] {e}")

    def speak(self, text: str):
        """Queue text to be spoken asynchronously."""
        if not text:
            return
        self.speech_queue.put(text)

    def listen(self, timeout=7, phrase_time_limit=10) -> str:
        """Listen to the microphone and convert speech to text with multi-accent support."""
        try:
            mic_kwargs = {}
            if self.device_index is not None:
                mic_kwargs["device_index"] = self.device_index

            with sr.Microphone(**mic_kwargs) as source:
                # Listen without blocking calibration delay
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                # Multi-language recognition (try standard English, fallback to South Asian English)
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    if text:
                        return text.strip()
                except (sr.UnknownValueError, sr.RequestError):
                    pass

                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN")
                    if text:
                        return text.strip()
                except Exception:
                    pass

                return ""
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"[STT Error] {e}")
            return ""
