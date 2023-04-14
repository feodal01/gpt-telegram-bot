import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
import sqlite3
import yaml

from db_utils import count_user_msg, check_subscription, select_context, store_user_requests
from gpt_utils import get_answer, make_message_list, validate_user_message_lenght


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=settings['WELCOME_MESSAGE'])


async def _send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def show_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('pragma encoding=UTF8')
    cursor.execute('SELECT * FROM context_table WHERE user_id=? AND user_name=?;', (user['id'], user['username']))
    rows = ['{}: {}'.format(list(row)[-2], list(row)[-1]) for row in cursor.fetchall()]
    [await _send_message(update, context, text) for text in rows]


async def ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    user_message = update.message.text

    # Трекаем что пользователь написал сообщение
    count_user_msg(username=user['username'], user_id=user['id'])

    # Проверяем есть ли подписка у пользователя или что количество сообщений не превышает бесплатный лимит
    if not check_subscription(username=user['username'], user_id=user['id']):
        pass # пока что

    # FixMe Вставить логирование и сделать проверку на длину
    if not validate_user_message_lenght(user_message):
        await _send_message(update, context, 'Message is too long, please make it shorter!')

    # Выбираем пользовательский контекст из того, что там написал пользователь
    selected_context = select_context(username=user['username'], user_id=user['id'])
    # Укорачиваем, чтобы вписать в контекст модели
    messages = make_message_list(selected_context, user_message=user_message)

    # Заправшиваем у openai ответ
    try:
        result = get_answer(messages=messages)
    except ValueError as e:
        result = 'Что то пошло не так с запросом, попробуйте еще раз'

    # сохраним что там нам написал юзер и ответила сетка
    store_user_requests(user['username'], user['id'], 'user', user_message)
    store_user_requests(user['username'], user['id'], 'assistant', result)

    await _send_message(update, context, result)


if __name__ == '__main__':

    with open('api_settings.yaml', 'r') as f:
        settings = yaml.safe_load(f)

    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    application = ApplicationBuilder().token(os.environ.get('TELEGRAM_TOKEN')).build()

    start_handler = CommandHandler('start', start)
    show_context_handler = CommandHandler('show_context', show_context)
    ask_gpt_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), ask_gpt)

    application.add_handler(start_handler)
    application.add_handler(ask_gpt_handler)
    application.add_handler(show_context_handler)

    application.run_polling()
