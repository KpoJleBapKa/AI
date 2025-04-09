import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSE_FEED, CHOOSE_QUANTITY, GET_CONTACT, CONFIRM_ORDER = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Корм для папуг 🦜", callback_data='feed_parrot')],
        [InlineKeyboardButton("Корм для канарок 🐤", callback_data='feed_canary')],
        [InlineKeyboardButton("Універсальний корм 🕊️", callback_data='feed_universal')],
        [InlineKeyboardButton("Інший тип (вкажіть)", callback_data='feed_other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привіт! Я допоможу вам замовити корм для птахів. 🐦\n"
        "Будь ласка, оберіть тип корму:",
        reply_markup=reply_markup
    )
    return CHOOSE_FEED

async def choose_feed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    feed_type = query.data
    context.user_data['feed_type'] = feed_type.replace('feed_', '')

    if feed_type == 'feed_other':
        await query.edit_message_text(text="Будь ласка, напишіть, який саме корм вас цікавить:")
        context.user_data['feed_type'] = 'other_specified_later'
        await query.message.reply_text("Добре. Тепер вкажіть бажану кількість (наприклад, в кг або шт):")
    else:
        await query.edit_message_text(text=f"Ви обрали: {context.user_data['feed_type']}. Чудово!")
        await query.message.reply_text("Тепер вкажіть бажану кількість (наприклад, в кг або шт):")

    return CHOOSE_QUANTITY

async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quantity = update.message.text
    context.user_data['quantity'] = quantity

    if not quantity:
        await update.message.reply_text("Будь ласка, введіть кількість.")
        return CHOOSE_QUANTITY

    await update.message.reply_text(
        f"Запам'ятав: {quantity}.\n"
        "Тепер, будь ласка, напишіть ваш контактний номер телефону або адресу для доставки:"
    )
    return GET_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact_info = update.message.text
    context.user_data['contact'] = contact_info

    feed_type = context.user_data.get('feed_type', 'Не вказано')
    quantity = context.user_data.get('quantity', 'Не вказано')
    contact = context.user_data.get('contact', 'Не вказано')

    summary_text = (
        f"**Ваше замовлення:**\n"
        f"Тип корму: {feed_type}\n"
        f"Кількість: {quantity}\n"
        f"Контактна інформація: {contact}\n\n"
        f"Все вірно?"
    )

    keyboard = [
        [
            InlineKeyboardButton("Так, підтвердити 👍", callback_data='confirm_yes'),
            InlineKeyboardButton("Ні, скасувати 👎", callback_data='confirm_no'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(summary_text, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm_yes':
        feed_type = context.user_data.get('feed_type', 'N/A')
        quantity = context.user_data.get('quantity', 'N/A')
        contact = context.user_data.get('contact', 'N/A')

        order_details = f"Нове замовлення!\nТип: {feed_type}\nК-сть: {quantity}\nКонтакт: {contact}"
        logger.info(order_details)

        await query.edit_message_text(text="✅ Дякую! Ваше замовлення прийнято. Ми зв'яжемося з вами найближчим часом.")
        try:
            admin_chat_id = 709307873
            await context.bot.send_message(chat_id=admin_chat_id, text=order_details)
        except Exception as e:
            logger.error(f"Не вдалося відправити сповіщення адміну: {e}")

    elif query.data == 'confirm_no':
        await query.edit_message_text(text="❌ Замовлення скасовано. Якщо бажаєте почати знову, натисніть /start.")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Дію скасовано. Щоб почати знову, натисніть /start.")
    context.user_data.clear()
    return ConversationHandler.END

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Будь ласка, слідуйте інструкціям або використовуйте кнопки.")

def main() -> None:
    application = Application.builder().token("8056922219:AAFbsmHMKGgYV2F2O0gikMhPACvKcA4CZes").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_FEED: [
                CallbackQueryHandler(choose_feed, pattern='^feed_')
            ],
            CHOOSE_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quantity)
            ],
            GET_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern='^confirm_')
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT | filters.COMMAND, fallback_handler)
            ],
        per_user=True,
        per_chat=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel))

    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == "__main__":
    main()