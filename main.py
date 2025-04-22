# pip install python-telegram-bot --upgrade

import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_PASSWORD = "ADMIN_PASSWORD"
ADMIN_WAIT = range(1)


def load_users():
    try:
        with open('users.json', encoding="utf8") as file:
            return json.load(file)
    except:
        return []

def save_users(users):
    with open('users.json', 'w', encoding="utf8") as file:
        json.dump(users, file)


def load_admins():
    try:
        with open('admins.json', encoding="utf8") as file:
            return json.load(file)
    except:
        return []

def save_admins(admins):
    with open('admins.json', 'w', encoding="utf8") as file:
        json.dump(admins, file)


def get_keyboard(user_id):
    users = load_users()
    admins = load_admins()

    inline = [
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]

    if str(user_id) in admins:
        inline.insert(0, [InlineKeyboardButton("▶️ Запустить таймер", callback_data='start_timer')])
    else:
        if str(user_id) in users:
            inline.insert(0, [InlineKeyboardButton("🛡 Стать админом", callback_data='become_admin')])
            inline.insert(1, [InlineKeyboardButton("🚪 Выйти из списка", callback_data='leave')])
        else:
            inline.insert(0, [InlineKeyboardButton("🛡 Стать админом", callback_data='become_admin')])
            inline.insert(1, [InlineKeyboardButton("🔙 Вернуться в список", callback_data='return')])

    return InlineKeyboardMarkup(inline)

def get_reply_keyboard(user_id):
    users = load_users()
    admins = load_admins()

    if str(user_id) in admins:
        return ReplyKeyboardMarkup([
            [KeyboardButton("▶️ Запустить таймер")],
            [KeyboardButton("❓ Помощь")]
        ], resize_keyboard=True)
    elif str(user_id) in users:
        return ReplyKeyboardMarkup([
            [KeyboardButton("🛡 Стать админом"), KeyboardButton("🚪 Выйти из списка")],
            [KeyboardButton("❓ Помощь")]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            [KeyboardButton("🛡 Стать админом"), KeyboardButton("🔙 Вернуться в список")],
            [KeyboardButton("❓ Помощь")]
        ], resize_keyboard=True)


def start(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    users = load_users()
    if str(user_id) not in users:
        users.append(str(user_id))
        save_users(users)

    update.message.reply_text(
        "Добро пожаловать! Используйте кнопки ниже для взаимодействия.",
        reply_markup=get_reply_keyboard(user_id)
    )
    # context.bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=get_keyboard(user_id))

def become_admin(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    admins = load_admins()
    if str(user_id) not in admins:
        if update.callback_query:
            update.callback_query.message.reply_text("Введите пароль для получения прав администратора:")
        else:
            update.message.reply_text("Введите пароль для получения прав администратора:")
        return ADMIN_WAIT
    update.message.reply_text("У вас есть права администратора.")

def confirm_password(update: Update, context: CallbackContext):
    if update.message.text == ADMIN_PASSWORD:
        admins = load_admins()
        user_id = str(update.effective_chat.id)
        if user_id not in admins:
            admins.append(user_id)
            save_admins(admins)
        update.message.reply_text("Теперь вы администратор!", reply_markup=get_reply_keyboard(user_id))
        # context.bot.send_message(chat_id=user_id, text="Кнопки обновлены", reply_markup=get_keyboard(user_id))
    else:
        update.message.reply_text("Неверный пароль.")
    return ConversationHandler.END

def cancel_password(update: Update, context: CallbackContext):
    update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def start_timer_callback(update: Update, context: CallbackContext):
    admins = load_admins()
    user_id = str(update.effective_chat.id)
    if user_id in admins:
        context.job_queue.run_once(warning_timer, 480, context=user_id)
        context.job_queue.run_once(end_timer, 600, context=user_id)
        if update.callback_query:
            update.callback_query.message.reply_text("Таймер запущен.")
        else:
            update.message.reply_text("Таймер запущен.")
    else:
        update.message.reply_text("Обратитесь к администратору.")

def warning_timer(context: CallbackContext):
    users = load_users()
    for user in users:
        context.bot.send_message(chat_id=user, text="Осталось две минуты.")

def end_timer(context: CallbackContext):
    users = load_users()
    for user in users:
        context.bot.send_message(chat_id=user, text="Ваше время истекло!")

def help_command(update: Update, context: CallbackContext):
    message = "Команды бота:\n/start — начало\n/become_admin — стать админом\n/leave — выйти из списка\n/return — вернуться в список\n/help — помощь"
    if update.callback_query:
        update.callback_query.message.reply_text(message)
    else:
        update.message.reply_text(message)

def leave(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    users = load_users()
    if user_id in users:
        users.remove(user_id)
        save_users(users)
    if update.callback_query:
        update.callback_query.message.reply_text("Вы покинули список участников.", reply_markup=get_keyboard(user_id))
    else:
        update.message.reply_text("Вы покинули список участников.", reply_markup=get_reply_keyboard(user_id))

def return_to_list(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
    if update.callback_query:
        update.callback_query.message.reply_text("Вы снова в списке участников.") 
    else:
        update.message.reply_text("Вы снова в списке участников.")

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'start_timer':
        return start_timer_callback(update, context)
    elif data == 'help':
        return help_command(update, context)
    elif data == 'become_admin':
        return become_admin(update, context)
    elif data == 'leave':
        return leave(update, context)
    elif data == 'return':
        return return_to_list(update, context)

def main():
    updater = Updater(":", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(become_admin, pattern='^become_admin$'), CommandHandler("become_admin", become_admin), MessageHandler(Filters.text("🛡 Стать админом"), become_admin)],
        states={
            ADMIN_WAIT: [MessageHandler(Filters.text & ~Filters.command, confirm_password)]
        },
        fallbacks=[CommandHandler('cancel', cancel_password)]
    )

    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("leave", leave))
    dp.add_handler(CommandHandler("return", return_to_list))

    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text("▶️ Запустить таймер"), start_timer_callback))
    dp.add_handler(MessageHandler(Filters.text("❓ Помощь"), help_command))
    dp.add_handler(MessageHandler(Filters.text("🚪 Выйти из списка"), leave))
    dp.add_handler(MessageHandler(Filters.text("🔙 Вернуться в список"), return_to_list))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
