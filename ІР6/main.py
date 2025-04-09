import speech_recognition as sr
import pyttsx3
import sys
import time

def speak(engine, text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Помилка TTS: {e}")

def listen(recognizer, microphone):
    if not isinstance(microphone, sr.Microphone):
        print("Помилка: Неправильний об'єкт мікрофона.")
        return None
    with microphone as source:
        try:
             recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
             print(f"Помилка налаштування шуму: {e}")
        print("Слухаю...")
        audio = None
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("Час очікування мови вичерпано.")
            return None
        except Exception as e:
             print(f"Помилка під час слухання: {e}")
             return None

    if audio:
        try:
            print("Розпізнавання...")
            text = recognizer.recognize_google(audio, language='uk-UA')
            print(f"Ви сказали: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("Не вдалося розпізнати мову.")
            return None
        except sr.RequestError as e:
            print(f"Помилка сервісу Google Speech Recognition; {e}")
            return None
        except Exception as e:
            print(f"Інша помилка розпізнавання: {e}")
            return None
    else:
        return None

def run_simple_voice_bot():
    try:
        recognizer = sr.Recognizer()
    except Exception as e:
        print(f"Помилка ініціалізації розпізнавача: {e}")
        sys.exit(1)

    try:
         if not sr.Microphone.list_microphone_names():
              print("Помилка: Мікрофони не знайдено у системі.")
              sys.exit(1)
         microphone = sr.Microphone() 
    except Exception as e:
        print(f"Помилка доступу до мікрофона: {e}")
        print("Переконайтесь, що мікрофон підключено, налаштовано та встановлено PyAudio.")
        sys.exit(1)


    try:
        engine = pyttsx3.init()
        if engine is None:
             raise Exception("Не вдалося ініціалізувати TTS двигун.")
        engine.setProperty('rate', 180) 
    except Exception as e:
        print(f"Помилка ініціалізації TTS (pyttsx3): {e}")
        sys.exit(1)

    speak(engine, "Голосовий бот запущено. Скажіть команду.")
    time.sleep(0.5) 

    while True:
        command = listen(recognizer, microphone)
        response = ""

        if command:
            if "привіт" in command:
                response = "Вітаю!"
            elif "як тебе звати" in command or "твоє ім'я" in command:
                response = "Я простий голосовий помічник."
            elif "котра година" in command:
                 now = time.strftime("%H:%M", time.localtime())
                 response = f"Зараз {now}"
            elif "дякую" in command:
                 response = "Будь ласка!"
            elif "бувай" in command or "вихід" in command or "до побачення" in command:
                response = "До зустрічі!"
                print(f"Бот: {response}")
                speak(engine, response)
                break
            else:
                response = "Я не зрозумів команду. Повторіть, будь ласка."

            print(f"Бот: {response}")
            speak(engine, response)
            time.sleep(0.5) 
        else:
             print("Очікую наступну команду...")
             time.sleep(1)

if __name__ == "__main__":
    run_simple_voice_bot()