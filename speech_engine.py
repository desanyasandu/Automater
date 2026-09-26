import threading
import queue
import speech_recognition as sr
import pyttsx3


def get_best_microphone_index() -> int | None:
    """Find the best physical microphone (Digital Array preferred)."""
    try:
        names = sr.Microphone.list_microphone_names()
        for priority_kw in ["microphone array", "realtek", "usb audio", "headset"]:
            for idx, name in enumerate(names):
                if priority_kw in name.lower():
                    return idx
    except Exception:
        pass
    return None  # Default system mic


class SpeechEngine:
    def __init__(self, device_index=None):
        self.recognizer = sr.Recognizer()

        # Fast, sensitive mic settings
        self.recognizer.energy_threshold = 250          # Sensitive to quiet speech
        self.recognizer.dynamic_energy_threshold = False # Don't auto-adjust (keeps it fast)
        self.recognizer.pause_threshold = 0.6           # Stop listening 0.6s after speech ends
        self.recognizer.phrase_threshold = 0.2          # Minimum speech length
        self.recognizer.non_speaking_duration = 0.4     # Trim silence at start

        self.device_index = device_index if device_index is not None else get_best_microphone_index()
        self.tts_queue = queue.Queue()
        self.is_speaking = False

        # Launch background TTS worker
        tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        tts_thread.start()

    def set_device_index(self, index: int | None):
        self.device_index = index

    # ── TTS ────────────────────────────────────────────────────────────────────

    def _tts_worker(self):
        """Runs pyttsx3 in its own dedicated thread (required on Windows)."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)     # Natural speech speed
            engine.setProperty('volume', 1.0)

            # Pick best English voice (David or Mark on Windows)
            voices = engine.getProperty('voices')
            for v in voices:
                if any(name in v.name for name in ["David", "Mark", "Zira", "George"]):
                    engine.setProperty('voice', v.id)
                    break

            while True:
                text = self.tts_queue.get()
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
                    self.tts_queue.task_done()
        except Exception as e:
            print(f"[TTS Worker Fatal] {e}")

    def speak(self, text: str):
        """Queue text for non-blocking speech output."""
        if text and text.strip():
            self.tts_queue.put(text.strip())

    # ── STT ────────────────────────────────────────────────────────────────────

    def listen(self, timeout: int = 6, phrase_time_limit: int = 10) -> str:
        """
        Record microphone input and convert to text.
        Returns the recognised text or '' if nothing heard.
        """
        mic_kwargs = {}
        if self.device_index is not None:
            mic_kwargs["device_index"] = self.device_index

        try:
            with sr.Microphone(**mic_kwargs) as source:
                # Quick ambient noise adjustment (50ms only)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.05)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            # Try primary language first
            for lang in ("en-US", "en-IN", "en-GB"):
                try:
                    text = self.recognizer.recognize_google(audio, language=lang)
                    if text:
                        return text.strip()
                except sr.UnknownValueError:
                    continue  # Try next language
                except sr.RequestError as e:
                    print(f"[STT Network Error] {e}")
                    return ""

        except sr.WaitTimeoutError:
            return ""          # No speech within timeout — not an error
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"[STT Error] {e}")

        return ""
