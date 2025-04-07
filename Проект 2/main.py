import telebot
import requests
import sqlite3

TOKEN = 'hidden'
WG_API_KEY = 'hidden'
ADMIN_USER_ID = 'kpojlebapka'

bot = telebot.TeleBot(TOKEN)

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('wot_bot.db')
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            feedback_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

create_tables()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('/wothelp')
    item2 = telebot.types.KeyboardButton('/findstat')
    item3 = telebot.types.KeyboardButton('/findclan')
    item4 = telebot.types.KeyboardButton('/feedback')
    markup.add(item1, item2, item3, item4)

    bot.reply_to(message, f"Привіт, {message.from_user.first_name}! 👋\n"
                           "Я бот для відслідковування статистики World of Tanks.\n"
                           "Ось список доступних команд:", reply_markup=markup)

@bot.message_handler(commands=['wothelp'])
def send_help(message):
    help_message = (
        "<b>|--------------------------------------------------------------------------------|</b>\n"
        "<b>Бот</b> для відслідковування статистики <b>World of Tanks</b>\n"
        "\n"
        "<i>Команди: </i>\n"
        "<b>/findstat</b> <i>'нікнейм'</i> - дізнатися статистику гравця \n"
        "<b>/findclan</b> <i>'назва клану'</i> - дізнатися інформацію про клан \n"
        "<b>/gm_battles</b> <i>'тег клану'</i> - дізнатися майбутні бої клану на Глобальній Мапі\n"
        "<b>/gm_stat</b> <i>'тег клану'</i> - дізнатися статистику клану на Глобальній Мапі\n"
        "<b>/clan_members</b> <i>'тег клану'</i> - дізнатися кількість та статистику гравців клану\n"
        "<b>/feedback</b> - залишити відгук про бота\n"
        "<b>/info</b> - інформація про бота\n"
        "<b>|---------------------------------------------------------------------------------|</b>\n"
    )
    bot.send_message(message.chat.id, help_message, parse_mode='HTML')

@bot.message_handler(commands=['info'])
def send_info(message):
    info_message = (
        "<b>|-------------------------------------------------|</b>\n"
        "<b>Інформація про бота</b>\n"
        "<br>\n"
        "Цей бот розроблений для відображення статистики гравців та кланів у грі World of Tanks.\n"
        "Він використовує API World of Tanks для отримання даних.\n"
        "Розробник: [Твоє ім'я/нікнейм]\n"
        "Версія: 1.0\n"
        "<b>|-------------------------------------------------|</b>\n"
    )
    bot.send_message(message.chat.id, info_message, parse_mode='HTML')

@bot.message_handler(commands=['findstat'])
def find_stat(message):
    try:
        player_name = message.text.split(' ', 1)[1]
        wot_api_url = f'https://api.worldoftanks.eu/wot/account/list/?application_id={WG_API_KEY}&search={player_name}'

        response = requests.get(wot_api_url)
        data = response.json()

        if data is None or 'data' not in data or not data['data']:
            bot.reply_to(message, f"Гравець <b>{player_name}</b> не знайдений.", parse_mode='HTML')
            return

        account_id = data['data'][0]['account_id']
        stats_url = f'https://api.worldoftanks.eu/wot/account/info/?application_id={WG_API_KEY}&account_id={account_id}'

        response = requests.get(stats_url)
        stats_data = response.json()

        if stats_data is None or 'data' not in stats_data or str(account_id) not in stats_data['data']:
            bot.reply_to(message, f"Статистика для гравця <b>{player_name}</b> недоступна.", parse_mode='HTML')
            return

        stats = stats_data['data'][str(account_id)]['statistics']['all']

        clan_info_url = f'https://api.worldoftanks.eu/wot/clans/accountinfo/?application_id={WG_API_KEY}&account_id={account_id}'
        response = requests.get(clan_info_url)
        clan_data = response.json()

        try:
            clan_name = clan_data['data'][str(account_id)]['clan']['tag']
        except (KeyError, TypeError):
            clan_name = "без клану"

        message_text = (f"<b>|----------------------------------------------------------------|</b>\n"
                        f"<b>Статистика гравця</b> <i>{player_name}</i>\n"
                        f"<b>Клан:</b> {clan_name}\n"
                        f"<b>Кількість боїв:</b> {stats['battles']}\n"
                        f"<b>% перемог:</b> {stats['wins'] / stats['battles'] * 100:.2f}%\n"
                        f"<b>% влучень:</b> {stats['hits'] / stats['shots'] * 100:.2f}%\n"
                        f"<b>Середня шкода:</b> {stats['damage_dealt'] / stats['battles']:.2f}\n"
                        f"<b>Середній досвід:</b> {stats['xp'] / stats['battles']:.2f}\n"
                        f"<b>Максимум знищено за бій:</b> {stats['max_frags']}\n"
                        f"<b>Максимальний досвід за бій:</b> {stats['max_xp']}\n"
                        f"<b>|----------------------------------------------------------------|</b>")
        bot.send_message(message.chat.id, message_text, parse_mode='HTML')

    except IndexError:
        bot.reply_to(message, "Невірно введена команда. Приклад: /findstat KpoJleBapKa", parse_mode='HTML')
    except Exception as e:
        print(f"Помилка в команді findstat: {e}")
        bot.reply_to(message, f"Виникла помилка: {e}", parse_mode='HTML')

@bot.message_handler(commands=['findclan'])
def find_clan(message):
    try:
        clan_name = message.text.split(' ', 1)[1]
        clan_info_url = f'https://api.worldoftanks.eu/wot/clans/list/?application_id={WG_API_KEY}&search={clan_name}'
        response = requests.get(clan_info_url)
        clan_data = response.json()

        if clan_data is None or 'data' not in clan_data or not clan_data['data']:
            bot.reply_to(message, f"Клан <b>{clan_name}</b> не знайдений.", parse_mode='HTML')
            return

        clan_info = clan_data['data'][0]

        clan_members_url = f'https://api.worldoftanks.eu/wot/clans/info/?application_id={WG_API_KEY}&clan_id={clan_info["clan_id"]}&fields=members'
        response = requests.get(clan_members_url)
        clan_members_data = response.json()

        if clan_members_data is None or 'data' not in clan_members_data or str(clan_info["clan_id"]) not in clan_members_data['data']:
            bot.reply_to(message, f"Інформація про гравців клану <b>{clan_name}</b> недоступна.", parse_mode='HTML')
            return

        message_text = (f"<b>|----------------------------------------------------------------|</b>\n"
                        f"<b>Інформація про клан</b> <i>{clan_name}</i>\n"
                        f"<b>Тег клану:</b> {clan_info['tag']}\n"
                        f"<b>Назва клану:</b> {clan_info['name']}\n"
                        f"<b>Учасники клану:</b> {clan_info['members_count']}\n"
                        f"<b>|----------------------------------------------------------------|</b>")
        bot.send_message(message.chat.id, message_text, parse_mode='HTML')

    except IndexError:
        bot.reply_to(message, "Невірно введена команда. Приклад: /findclan MANKI", parse_mode='HTML')
    except Exception as e:
        print(f"Помилка в команді findclan: {e}")
        bot.reply_to(message, f"Виникла помилка: {e}", parse_mode='HTML')

@bot.message_handler(commands=['gm_battles'])
def gm_battles(message):
    try:
        clan_tag = message.text.split(' ', 1)[1]
        clan_info_url = f'https://api.worldoftanks.eu/wot/clans/list/?application_id={WG_API_KEY}&search={clan_tag}'
        response = requests.get(clan_info_url)
        clan_data = response.json()

        if clan_data is None or 'data' not in clan_data or not clan_data['data']:
            bot.reply_to(message, f"Клан з тегом <b>{clan_tag}</b> не знайдений.", parse_mode='HTML')
            return

        clan_info = clan_data['data'][0]

        gm_battles_url = f'https://api.worldoftanks.eu/wot/globalmap/clanbattles/?application_id={WG_API_KEY}&clan_id={clan_info["clan_id"]}'
        response = requests.get(gm_battles_url)
        gm_battles_data = response.json()

        if gm_battles_data is None or 'data' not in gm_battles_data or not gm_battles_data['data']:
            bot.reply_to(message, f"На даний момент у клану <b>{clan_tag}</b> бої не виставлені.", parse_mode='HTML')
            return

        battles = gm_battles_data['data']
        response_text = ""
        for battle in battles:
            battle_info = battle['battle']
            response_text += (f"<b>|----------------------------------------------------------------|</b>\n"
                              f"<b>Майбутній бій клану</b> <i>{clan_tag}</i>\n"
                              f"<b>Проти якого клану:</b> {battle_info['opponents'][0]['clan']['tag']}\n"
                              f"<b>На карті:</b> {battle_info['map']['name_i18n']}\n"
                              f"<b>Час бою (UTC):</b> {battle_info['start_at']}\n"
                              f"<b>|----------------------------------------------------------------|</b>\n")
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

    except IndexError:
        bot.reply_to(message, "Невірно введена команда. Приклад: /gm_battles MANKI", parse_mode='HTML')
    except Exception as e:
        print(f"Помилка в команді gm_battles: {e}")
        bot.reply_to(message, f"Виникла помилка: {e}", parse_mode='HTML')

@bot.message_handler(commands=['gm_stat'])
def global_clan(message):
    try:
        clan_tag = message.text.split(' ', 1)[1]
        clan_info_url = f'https://api.worldoftanks.eu/wot/clans/list/?application_id={WG_API_KEY}&search={clan_tag}'
        response = requests.get(clan_info_url)
        clan_data = response.json()

        if clan_data is None or 'data' not in clan_data or not clan_data['data']:
            bot.reply_to(message, f"Клан з тегом <b>{clan_tag}</b> не знайдений.", parse_mode='HTML')
            return

        clan_info = clan_data['data'][0]

        global_clan_url = f'https://api.worldoftanks.eu/wot/globalmap/claninfo/?application_id={WG_API_KEY}&clan_id={clan_info["clan_id"]}'
        response = requests.get(global_clan_url)
        global_clan_data = response.json()

        if global_clan_data is None or 'data' not in global_clan_data or not global_clan_data['data']:
            bot.reply_to(message, f"Статистика клану <b>{clan_tag}</b> на глобальній карті недоступна.", parse_mode='HTML')
            return

        clan_stats = global_clan_data['data'][str(clan_info["clan_id"])]

        message_text = (f"<b>|----------------------------------------------------------------|</b>\n"
                        f"<b>Статистика клану на глобальній карті</b> <i>{clan_tag}</i>\n"
                        f"<b>Кількість боїв:</b> {clan_stats.get('battles', 0)}\n"
                        f"<b>Кількість територій:</b> {clan_stats.get('territories', 0)}\n"
                        f"<b>Кількість перемог:</b> {clan_stats.get('wins', 0)}\n"
                        f"<b>|----------------------------------------------------------------|</b>")
        bot.send_message(message.chat.id, message_text, parse_mode='HTML')

    except IndexError:
        bot.reply_to(message, "Невірно введена команда. Приклад: /gm_stat MANKI", parse_mode='HTML')
    except Exception as e:
        print(f"Помилка в команді gm_stat: {e}")
        bot.reply_to(message, f"Виникла помилка: {e}", parse_mode='HTML')

@bot.message_handler(commands=['clan_members'])
def clan_members(message):
    try:
        clan_tag = message.text.split(' ', 1)[1]
        clan_info_url = f'https://api.worldoftanks.eu/wot/clans/list/?application_id={WG_API_KEY}&search={clan_tag}'
        response = requests.get(clan_info_url)
        clan_data = response.json()

        if clan_data is None or 'data' not in clan_data or not clan_data['data']:
            bot.reply_to(message, f"Клан з тегом <b>{clan_tag}</b> не знайдений.", parse_mode='HTML')
            return

        clan_info = clan_data['data'][0]
        clan_id = clan_info["clan_id"]

        clan_members_url = f'https://api.worldoftanks.eu/wot/clans/info/?application_id={WG_API_KEY}&clan_id={clan_id}&fields=members'
        response = requests.get(clan_members_url)
        clan_members_data = response.json()

        if clan_members_data is None or 'data' not in clan_members_data or str(clan_id) not in clan_members_data['data']:
            bot.reply_to(message, f"Інформація про гравців клану <b>{clan_tag}</b> недоступна.", parse_mode='HTML')
            return

        clan_members = clan_members_data['data'][str(clan_id)]["members"]
        total_members = len(clan_members)

        if not clan_members:
            bot.reply_to(message, f"В клані <b>{clan_tag}</b> немає гравців.", parse_mode='HTML')
            return

        leaderboard_message = f"<b>Клан \"{clan_tag}\"</b>\n\nКількість гравців у клані: {total_members}\n\n<b>╟ Нікнейм, роль, % перемог, середня шкода ╣</b>"

        for index, member_info in enumerate(clan_members[:100], start=1):
            player_name = member_info['account_name']
            member_id = member_info['account_id']

            player_stats_url = f'https://api.worldoftanks.eu/wot/account/info/?application_id={WG_API_KEY}&account_id={member_id}&fields=statistics.all'
            response = requests.get(player_stats_url)
            player_stats_data = response.json()

            if player_stats_data is None or 'data' not in player_stats_data or str(member_id) not in player_stats_data['data']:
                wins_percent = 0.0
                avg_damage = 0.0
            else:
                stats = player_stats_data['data'][str(member_id)]['statistics']['all']
                battles = stats['battles']
                wins_percent = (stats['wins'] / battles * 100) if battles > 0 else 0.0
                avg_damage = (stats['damage_dealt'] / battles) if battles > 0 else 0.0

            leaderboard_message += f"\n<b>{player_name}</b> - <i>{member_info['role']}</i> -  <b>{wins_percent:.2f}%</b> -  <b>{avg_damage:.2f}</b>"

            if index % 10 == 0 or index == len(clan_members):
                bot.send_message(message.chat.id, leaderboard_message, parse_mode='HTML')
                leaderboard_message = ""

    except IndexError:
        bot.reply_to(message, "Невірно введена команда. Приклад: /clan_members MANKI", parse_mode='HTML')
    except Exception as e:
        print(f"Помилка в команді clan_members: {e}")
        bot.reply_to(message, f"Виникла помилка: {e}", parse_mode='HTML')

@bot.message_handler(commands=['feedback'])
def feedback(message):
    bot.reply_to(message, "Будь ласка, напишіть свій відгук:")
    bot.register_next_step_handler(message, process_feedback)

def process_feedback(message):
    try:
        feedback_text = message.text
        user_id = message.from_user.id
        username = message.from_user.username

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (user_id, username, feedback_text) VALUES (?, ?, ?)",
                       (user_id, username, feedback_text))
        conn.commit()
        conn.close()

        bot.reply_to(message, "Дякуємо за ваш відгук! 🙏")

        if ADMIN_USER_ID:
            admin_message = f"Новий відгук від користувача @{username} ({user_id}):\n\n{feedback_text}"
            bot.send_message(ADMIN_USER_ID, admin_message)

    except Exception as e:
        print(f"Помилка при обробці відгуку: {e}")
        bot.reply_to(message, f"Виникла помилка при збереженні відгуку: {e}")

@bot.message_handler(func=lambda message: message.text.lower() in ['привіт', 'hello', 'ку'])
def greet(message):
    bot.reply_to(message, f"Привіт, {message.from_user.first_name}! 👋")

@bot.message_handler(func=lambda message: message.text.lower() in ['дякую', 'спасибо'])
def thank(message):
    bot.reply_to(message, "Будь ласка! 😉")

if __name__ == '__main__':
    print('Бот запущено...')
    bot.polling(none_stop=True)