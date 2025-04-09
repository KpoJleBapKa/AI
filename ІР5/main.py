from openai import OpenAI, APIError
import os
import sys

def chat_with_gpt4o():

    bob_api_key = "kroll_pena"

    try:
        client = OpenAI(api_key=bob_api_key)
    except Exception as e:
        print(f"Помилка при ініціалізації клієнта OpenAI або перевірці ключа: {e}")
        sys.exit(1)

    messages = [
        {"role": "system", "content": "Ти корисний помічник."}
    ]

    print("Розпочато діалог з ChatGPT 4o. Введіть 'вихід', щоб завершити.")

    while True:
        try:
            user_input = input("Ви: ")
        except EOFError:
            print("\nЗавершення діалогу.")
            break

        if user_input.lower() in ["вихід", "exit", "quit"]:
            print("Діалог завершено користувачем.")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7
            )

            assistant_message = response.choices[0].message.content
            print(f"ChatGPT: {assistant_message}")

            messages.append({"role": "assistant", "content": assistant_message})

        except APIError as e:
            print(f"\nПомилка API OpenAI: {e}")
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            print("Спробуйте ще раз або введіть 'вихід'.")
        except Exception as e:
            print(f"\nНеочікувана помилка: {e}")
            if messages and messages[-1]["role"] == "user":
                 messages.pop()
            print("Спробуйте ще раз або введіть 'вихід'.")

if __name__ == "__main__":
    chat_with_gpt4o()