import speech_recognition as sr
import openai
import io
import pygame
import time 


OPENAI_API_KEY = "kroll" 

client = openai.OpenAI(api_key=OPENAI_API_KEY)

recognizer = sr.Recognizer()
microphone = sr.Microphone()

conversation_history = [
    {"role": "system", "content": "Ти - корисний голосовий асистент, що відповідає українською мовою."}
]


def listen_for_audio():
    """Захоплює аудіо з мікрофона і повертає аудіо дані."""
    with microphone as source:
        print("Налаштування на фоновий шум...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("ЗАПИС: Будь ласка, говоріть...")
        try:
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Аудіо отримано, розпізнавання...")
            return audio_data
        except sr.WaitTimeoutError:
            print("Час очікування вичерпано, мовлення не виявлено.")
            return None
        except Exception as e:
            print(f"Помилка під час прослуховування: {e}")
            return None

def transcribe_audio(audio_data):
    """Надсилає аудіо дані до OpenAI Whisper API для розпізнавання."""
    if not audio_data:
        return None
    try:
        wav_bytes = audio_data.get_wav_data()
        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "audio.wav"

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="uk"
        )
        print(f"Розпізнано: {transcript.text}")
        return transcript.text
    except openai.APIError as e:
        print(f"Помилка OpenAI API (Whisper): {e}")
        return None
    except Exception as e:
        print(f"Не вдалося розпізнати мову: {e}")
        return None

def get_gpt_response(text):
    """Надсилає текст до GPT-4o і повертає відповідь українською."""
    if not text:
        return "Вибачте, я не розчув ваш запит."

    conversation_history.append({"role": "user", "content": text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history,
            max_tokens=150
        )
        assistant_response = response.choices[0].message.content
        print(f"GPT Відповідь: {assistant_response}")

        conversation_history.append({"role": "assistant", "content": assistant_response})
        return assistant_response

    except openai.APIError as e:
        print(f"Помилка OpenAI API (GPT): {e}")
        conversation_history.pop()
        return "Вибачте, сталася помилка при обробці вашого запиту."
    except Exception as e:
        print(f"Інша помилка при взаємодії з GPT: {e}")
        conversation_history.pop()
        return "Вибачте, непередбачувана помилка."

def speak_text(text):
    """Перетворює текст на мову за допомогою OpenAI TTS і відтворює його через pygame.mixer."""
    if not text:
        print("Немає тексту для озвучення.")
        return

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        audio_bytes = response.content
        print("Обробка аудіо відповіді...")
        try:
            pygame.mixer.music.load(io.BytesIO(audio_bytes))
            print("Відтворення відповіді...")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except pygame.error as e:
            print(f"Помилка Pygame під час завантаження/відтворення: {e}")

    except openai.APIError as e:
        print(f"Помилка OpenAI API (TTS): {e}")
    except Exception as e:
        print(f"Помилка під час синтезу або відтворення мови: {e}")


if __name__ == "__main__":
    print("Голосовий бот запущено. Скажіть 'прощавай' або 'бувай', щоб завершити.")

    try:
        pygame.init()
        pygame.mixer.init()
        mixer_initialized = True
    except Exception as e:
        print(f"Не вдалося ініціалізувати Pygame: {e}")
        print("Відтворення звуку може не працювати.")
        mixer_initialized = False

    try:
        while True:
            print("\n=== Готовий до запису ===")
            print("Натисніть Enter, щоб почати запис вашого голосового запиту...")
            input() 

            audio = listen_for_audio()

            if audio:
                user_text = transcribe_audio(audio)
                if user_text:
                    if any(word in user_text.lower() for word in ["прощавай", "бувай", "до побачення"]):
                        if mixer_initialized:
                           speak_text("До побачення!")
                        else:
                           print("До побачення!")
                        break 

                    bot_response = get_gpt_response(user_text)
                    if mixer_initialized:
                        speak_text(bot_response)
                    else:
                        print(f"Відповідь (без звуку): {bot_response}")

                else:
                    print("Не вдалося розпізнати мову в записі.")

    except KeyboardInterrupt:
        print("\nЗавершення роботи бота (Ctrl+C).")
    finally:
        if pygame.get_init():
             pygame.quit()
        print("Роботу бота завершено.")