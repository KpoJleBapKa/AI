import speech_recognition as sr
import openai
import io
import pygame
import time
import webbrowser
import re
import os

OPENAI_API_KEY = "kroll_pena" 
if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY":
    print("ПОМИЛКА: Не знайдено OpenAI API ключ.")
    print("Будь ласка, встановіть змінну середовища OPENAI_API_KEY або вставте ключ безпосередньо у скрипт.")
    exit()

try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("Клієнт OpenAI успішно ініціалізовано.")
except openai.AuthenticationError:
    print("ПОМИЛКА: Неправильний OpenAI API ключ. Перевірте ваш ключ.")
    exit()
except Exception as e:
    print(f"ПОМИЛКА: Не вдалося ініціалізувати клієнт OpenAI: {e}")
    exit()

recognizer = sr.Recognizer()
microphone = sr.Microphone()

conversation_history = [
    {"role": "system", "content": "Ти - корисний голосовий асистент, що відповідає українською мовою. Будь лаконічним та доброзичливим. Якщо ти не знаєш відповідь, скажи про це. Якщо отримуєш команду, яку можеш виконати (наприклад, відкрити сайт), підтвердь дію коротко ('Добре, відкриваю...') і виконай її. В інших випадках відповідай на запитання користувача."}
]

mixer_initialized = False
try:
    pygame.init()
    pygame.mixer.init()
    mixer_initialized = True
    print("Pygame mixer ініціалізовано успішно.")
except Exception as e:
    print(f"ПОПЕРЕДЖЕННЯ: Не вдалося ініціалізувати Pygame mixer: {e}")
    print("Відтворення звуку буде недоступне. Відповіді будуть лише текстовими.")

def listen_for_audio():
    with microphone as source:
        print("Налаштування на фоновий шум...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Помилка при налаштуванні на шум: {e}. Спробую продовжити.")

        print("ЗАПИС: Будь ласка, говоріть (до 10 секунд)...")
        audio_data = None
        try:
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Аудіо отримано, розпізнавання...")
        except sr.WaitTimeoutError:
            print("Час очікування вичерпано, мовлення не виявлено.")
        except Exception as e:
            print(f"Помилка під час прослуховування: {e}")
        return audio_data

def transcribe_audio(audio_data):
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
        recognized_text = transcript.text
        print(f"Розпізнано: {recognized_text}")
        return recognized_text
    except openai.APIError as e:
        print(f"ПОМИЛКА OpenAI API (Whisper): {e}")
        if "Incorrect API key" in str(e):
             print("Перевірте правильність вашого OpenAI API ключа.")
        return None
    except sr.RequestError as e:
         print(f"ПОМИЛКА запиту до сервісу розпізнавання (можливо, мережева): {e}")
         return None
    except Exception as e:
        print(f"ПОМИЛКА: Не вдалося розпізнати мову: {e}")
        return None

def speak_text(text):
    global mixer_initialized

    if not text:
        print("ПОПЕРЕДЖЕННЯ: Немає тексту для озвучення.")
        return

    if not mixer_initialized:
        print(f"Аудіо відповідь (відтворення недоступне): {text}")
        return

    print(f"Озвучення: {text}")
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3"
        )
        audio_bytes = response.content
        print("Обробка аудіо відповіді...")

        audio_stream = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_stream)
        print("Відтворення відповіді...")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        print("Відтворення завершено.")

    except openai.APIError as e:
        print(f"ПОМИЛКА OpenAI API (TTS): {e}")
    except pygame.error as e:
        print(f"ПОМИЛКА Pygame під час завантаження/відтворення: {e}")
        try:
            print("Спроба реініціалізації Pygame mixer...")
            pygame.mixer.quit()
            pygame.mixer.init()
            print("Pygame mixer реініціалізовано (спроба).")
        except Exception as reinit_e:
            print(f"Не вдалося реініціалізувати Pygame mixer: {reinit_e}")
            mixer_initialized = False
            print("Відтворення звуку вимкнено до перезапуску програми.")
    except Exception as e:
        print(f"ПОМИЛКА під час синтезу або відтворення мови: {e}")


def handle_command(text):
    text_lower = text.lower().strip()
    print(f"Перевірка на команди: '{text_lower}'")

    if "youtube" in text_lower and any(verb in text_lower for verb in ["включи", "відкрий", "запусти", "покажи"]):
        youtube_url = "https://www.youtube.com"
        confirmation_message = "Добре, відкриваю YouTube."
        speak_text(confirmation_message)
        try:
            webbrowser.open(youtube_url)
            print(f"Відкрито URL: {youtube_url} у браузері за замовчуванням.")
            return True
        except Exception as e:
            error_message = f"Не вдалося відкрити YouTube: {e}"
            print(error_message)
            speak_text("Вибачте, не вдалося відкрити YouTube.")
            return True

    open_match = re.search(r"(відкрий|покажи)\s+(сайт|сторінку|вебсайт)\s+(.+)", text_lower)
    if open_match:
        target = open_match.group(3).strip()
        if target.endswith('.'):
            target = target[:-1]

        if not target:
             speak_text("Будь ласка, вкажіть, який сайт чи сторінку відкрити.")
             return True

        if '.' in target and len(target) > 2 and not target.startswith('.') and not target.endswith('.'):
            url = target if target.startswith(('http://', 'https://')) else f"https://{target}"
            speak_text(f"Добре, відкриваю сайт {target}")
            try:
                webbrowser.open(url)
                print(f"Відкрито URL: {url}")
                return True
            except Exception as e:
                print(f"Не вдалося відкрити URL {url}: {e}")
                speak_text(f"Вибачте, не вдалося відкрити сайт {target}.")
                return True
        else:
            speak_text(f"Добре, шукаю '{target}' в інтернеті, щоб відкрити.")
            try:
                search_url = f"https://www.google.com/search?q={target.replace(' ', '+')}"
                webbrowser.open(search_url)
                print(f"Відкрито пошук Google для: {target}")
                return True
            except Exception as e:
                print(f"Не вдалося відкрити пошук Google для '{target}': {e}")
                speak_text(f"Вибачте, не вдалося виконати пошук для '{target}'.")
                return True

    search_match_complex = re.search(r"(знайди|пошукай)\s+(.+?)\s+(в інтернеті|в гуглі|в мережі)", text_lower)
    search_match_simple = re.search(r"(знайди|пошукай)\s+(.+)", text_lower)
    search_match = search_match_complex if search_match_complex else search_match_simple
    if search_match:
        query = search_match.group(2).strip()
        if query.endswith('.'):
            query = query[:-1]
        if query:
            speak_text(f"Добре, шукаю '{query}' в інтернеті.")
            try:
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(search_url)
                print(f"Відкрито пошук Google для: {query}")
                return True
            except Exception as e:
                print(f"Не вдалося відкрити пошук Google для '{query}': {e}")
                speak_text(f"Вибачте, не вдалося виконати пошук для '{query}'.")
                return True

    print("Текст не розпізнано як команду, буде передано до GPT.")
    return False

def get_gpt_response(text):
    if not text:
        print("ПОПЕРЕДЖЕННЯ: Спроба отримати відповідь GPT на порожній текст.")
        return "Вибачте, сталася внутрішня помилка."

    conversation_history.append({"role": "user", "content": text})
    print(f"Надсилання до GPT: {text}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history,
            max_tokens=150,
            temperature=0.7
        )
        assistant_response = response.choices[0].message.content.strip()
        print(f"GPT Відповідь: {assistant_response}")

        conversation_history.append({"role": "assistant", "content": assistant_response})
        return assistant_response

    except openai.APIError as e:
        print(f"ПОМИЛКА OpenAI API (GPT): {e}")
        if conversation_history and conversation_history[-1]["role"] == "user":
             conversation_history.pop()
        return "Вибачте, сталася помилка при зверненні до мовного сервісу OpenAI."
    except Exception as e:
        print(f"ПОМИЛКА: Інша помилка при взаємодії з GPT: {e}")
        if conversation_history and conversation_history[-1]["role"] == "user":
             conversation_history.pop()
        return "Вибачте, сталася непередбачувана помилка при генерації відповіді."

if __name__ == "__main__":
    print("\n" + "="*40)
    print("      Голосовий асистент запущено")
    print("="*40)
    speak_text("Вітаю! Я ваш голосовий помічник. Чим можу допомогти?")
    print("\nСкажіть 'прощавай', 'бувай' або 'до побачення', щоб завершити.")
    print("Коли будете готові говорити, натисніть Enter.")

    first_request = True

    try:
        while True:
            if not first_request:
                print("\n=== Готовий до наступного запиту ===")
                print("Натисніть Enter для запису...")
                input()
            else:
                print("\n=== Очікую ваш перший запит... ===")
                first_request = False

            audio_input = listen_for_audio()

            if audio_input:
                user_text = transcribe_audio(audio_input)

                if user_text:
                    if any(word in user_text.lower() for word in ["прощавай", "бувай", "до побачення", "завершити роботу"]):
                        farewell_message = "До побачення! Гарного дня!"
                        print(farewell_message)
                        speak_text(farewell_message)
                        break

                    command_handled = handle_command(user_text)

                    if not command_handled:
                        bot_response = get_gpt_response(user_text)
                        speak_text(bot_response)

                else:
                    speak_text("Вибачте, не вдалося розпізнати вашу мову. Спробуйте ще раз, говорячи чіткіше.")
            else:
                print("Мовлення не виявлено або сталася помилка запису.")

    except KeyboardInterrupt:
        print("\nЗавершення роботи бота за командою користувача (Ctrl+C).")
        farewell_message = "Роботу завершено."
        print(farewell_message)
    except Exception as e:
        print(f"\nПОМИЛКА: Виникла неочікувана помилка у головному циклі: {e}")
    finally:
        if pygame.get_init():
            print("Зупинка Pygame...")
            pygame.quit()
        print("Роботу голосового асистента завершено.")