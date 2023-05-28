import time
import datetime
import telebot
from telebot import types
from environs import Env
import tkinter as tk



from sql_functions import (
    sql_get_user_data,
    sql_register_new_user,
    sql_put_user_phone,
    registration_new_appointment,
    get_masters_name_from_base,
    get_services_from_base
)

import logging

BASE = 'db.sqlite3'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = Env()
env.read_env(override=True)
bot = telebot.TeleBot(env.str("TELEGRAM_CLIENT_BOT_API_TOKEN"))

EMPTY_CACHE = {
    'first_time': True,
    'office': False,
    'master': False,
    'procedure': False,
    'date': False,
    'time': False,
    'phone': False,
    'last_message_id': False
}

TIMES = [
    '10:00', '10:30',
    '11:00', '11:30',
    '12:00', '12:30',
    '13:00', '13:30',
    '14:00', '14:30',
    '15:00', '15:30',
    '16:00', '16:30',
    '17:00', '17:30',
    '18:00', '18:30',
    '19:00', '19:30',
    '20:00', '20:30'
]

MASTERS = get_masters_name_from_base()
SERVICES = get_services_from_base()


def print_booking_text(user_data, not_confirmed=True):
    if not_confirmed:
        dialogue_text = ' ---- Бронирование Записи ----' + '\n\n'
    else:
        dialogue_text = 'Поздравляем с успешной записью!' + '\n'
        dialogue_text += '===============================' + '\n\n'

    if user_data["procedure"]:
        dialogue_text += f'Сервис: {user_data["procedure"]}' + '\n'
    if user_data["master"]:
        dialogue_text += f'Мастер: {user_data["master"]}' + '\n'
        dialogue_text += f'Услуга: {user_data["procedure"]}' + '\n'
    if user_data["date"]:
        dialogue_text += f'Дата: {user_data["date"]}' + '\n'
    if user_data["time"]:
        dialogue_text += f'Время: {user_data["time"]}' + '\n'

    dialogue_text += '\n'

    return dialogue_text


# Приветствие и кнопка START
@bot.message_handler(commands=['start'])
def start_menu(message):
    if 'users' not in bot.__dict__.keys():
        bot.__dict__.update({'users': {}})

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(text='📞 Позвонить нам'))
    bot.send_message(message.chat.id, 'Добро пожаловать в BeautyCity!!!', reply_markup=markup)
    bot.register_next_step_handler(message, call_us)

    bot.__dict__['users'].update({message.chat.id: EMPTY_CACHE})
    user_data = bot.__dict__['users'][message.chat.id]
    user__in_db = sql_get_user_data(message.chat.id)
    if user__in_db:
        user_data['first_time'] = False
        user_data['phone'] = user__in_db['phone']

    dialogue_text = 'Выберите пункт меню:'
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    about_button = types.InlineKeyboardButton("О Нас", callback_data='about')
    choose_master_button = types.InlineKeyboardButton("Выбор мастера", callback_data='choose_master')
    choose_procedure_button = types.InlineKeyboardButton("Выбор процедуры", callback_data='choose_procedure')

    markup_inline.add(about_button, choose_master_button, choose_procedure_button)
    bot.send_message(message.chat.id, dialogue_text, reply_markup=markup_inline)


def main_menu(message):
    user_data = bot.__dict__['users'][message.chat.id]
    dialogue_text = 'Выберите пункт меню:'
    markup = types.InlineKeyboardMarkup(row_width=1)
    about_button = types.InlineKeyboardButton(
        "О Нас", callback_data='about'
    )
    choose_master_button = types.InlineKeyboardButton(
        "Выбор мастера", callback_data='choose_master'
    )
    choose_procedure_button = types.InlineKeyboardButton(
        "Выбор процедуры", callback_data='choose_procedure'
    )
    send_feedback_button = types.InlineKeyboardButton(
        "Оставить отзыв о последнем посещении", callback_data='send_feedback'
    )

    markup.add(about_button, choose_master_button, choose_procedure_button)
    # markup.add(send_feedback_button)
    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if 'users' not in bot.__dict__.keys():  # Если сервер перезапускался, то клиент вернётся на стартовую страницу
        bot.__dict__.update({'users': {}})
        bot.__dict__['users'].update({call.message.chat.id: EMPTY_CACHE})
        bot.delete_message(call.message.chat.id, call.message.id)
        start_menu(call.message)
        call.data = ''

    user_data = bot.__dict__.get('users', {}).get(call.message.chat.id, EMPTY_CACHE)
    args = call.data.split('#')
    if len(args) > 1:
        if args[1] == 'cut_date':
            user_data['date'] = False
        if args[1] == 'cut_time':
            user_data['time'] = False
        if args[1] == 'cut_phone':
            user_data['phone'] = False
            user_data['time'] = False

    if call.data == 'main_menu':
        main_menu(call.message)
    elif call.data == 'about':
        about(call.message)
    elif call.data == 'choose_master':
        choose_master(call.message)
    elif call.data.startswith('master'):
        choose_date(call.message, master=args[1])  # Pass the master as a string
    elif call.data.startswith('re_choose_date'):
        choose_date(call.message)
    elif call.data.startswith('choose_time'):
        choose_time(call.message, date=args[1])  # Pass the date as a string
    elif call.data.startswith('re_choose_time'):
        choose_time(call.message)
    elif call.data.startswith('confirmation'):
        confirmation(call.message, args[1])

    elif call.data.startswith('successful_booking'):
        lines = call.message.text.split('\n')
        meet_date = lines[2].split(':')[1].strip()
        meet_time = call.message.text.split('\n')[2].split(':')[1].strip()
        tg_id = call.message.chat.id
        master_id = call.message.text.split('\n')[3].split(':')[1].strip()
        service_id = call.message.text.split('\n')[4].split(':')[1].strip()
        successful_booking(call.message, meet_date, meet_time, tg_id, master_id, service_id)
        print(successful_booking(call.message, meet_date, meet_time, tg_id, master_id, service_id))

    elif call.data == 'choose_procedure':
        choose_procedure(call.message)
    elif call.data.startswith('procedure'):
        choose_date(call.message, procedure=args[1])


def about(message):
    dialogue_text = 'Студия BeautyCity' + '\n'
    dialogue_text += 'Instagram: @BeautyCity' + '\n'
    dialogue_text += 'Vkontakte: vk.com/BeautyCity' + '\n'

    markup = types.InlineKeyboardMarkup(row_width=1)
    button_1 = types.InlineKeyboardButton("Посетить сайт - beautycity.ru", url='https://www.beautycity.ru')
    button_back = types.InlineKeyboardButton('<< Назад', callback_data='main_menu')

    markup.add(button_1, button_back)
    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


def choose_master(message):
    dialogue_text = 'Выберите мастера:'
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for master in MASTERS:
        button = types.InlineKeyboardButton(master, callback_data=f'master#{master}')
        buttons.append(button)
    button_back = types.InlineKeyboardButton('<< Назад', callback_data='main_menu')
    markup.add(*buttons, button_back)
    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


def choose_procedure(message):
    dialogue_text = 'Выберите процедуру:'
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = []
    for service in SERVICES:
        button = types.InlineKeyboardButton(service, callback_data=f'procedure#{service}')
        buttons.append(button)

    button_back = types.InlineKeyboardButton('<< Назад', callback_data='main_menu')
    markup.add(*buttons, button_back)

    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


def choose_date(message, master=None, procedure=None):
    user_data = bot.__dict__['users'][message.chat.id]
    if master:
        user_data.update({'master': master})
    else:
        master = user_data.get('master')

    if procedure:
        user_data.update({'procedure': procedure})
    else:
        procedure = user_data.get('procedure')

    buttons = []
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    today = datetime.datetime.now().date()
    days_to_end_of_next_week = 14 - today.weekday()

    for i in range(days_to_end_of_next_week):
        new_date = today + datetime.timedelta(days=i)
        formatted_date = f"{new_date.day:02d}.{new_date.month:02d} ({days[new_date.weekday()]})"
        buttons.append(types.InlineKeyboardButton(formatted_date, callback_data=f'choose_time#{formatted_date}'))

    dialogue_text = print_booking_text(user_data)
    dialogue_text += 'Выберите удобный Вам день:'

    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i + 3])
    markup.row(types.InlineKeyboardButton('<< Назад', callback_data='choose_master'))
    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


def choose_time(message, date=None):
    user_data = bot.__dict__['users'][message.chat.id]
    if date:
        user_data.update({'date': date})
    else:
        date = user_data['date']
    dialogue_text = print_booking_text(user_data)
    dialogue_text += 'Выберите доступное время:'
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = []
    for item in TIMES:
        buttons.append(types.InlineKeyboardButton(item, callback_data=f'confirmation#{item}'))
    for i in range(0, len(buttons), 4):
        markup.add(*buttons[i:i + 4])
    markup.row(types.InlineKeyboardButton('<< Назад', callback_data='re_choose_date#cut_date'))
    bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)


def confirmation(message, time=None):
    user_data = bot.__dict__['users'][message.chat.id]
    if time:
        user_data.update({'time': time})
        user_data.update({'last_message_id': message.id})
    else:
        time = user_data.get('time')
    dialogue_text = print_booking_text(user_data)
    if user_data.get('first_time'):
        dialogue_text += 'Отправьте в чат, свой контактный номер.\n\n'
        dialogue_text += 'Отправляя нам свой телефон, Вы подтверждаете своё согласие на обработку Ваших данных.\n'
        dialogue_text += 'Более подробно с текстом соглашения можно ознакомиться по ссылке: www.confirmation.ru'
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(types.InlineKeyboardButton('<< Назад', callback_data='re_choose_time#cut_time'))
        bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)
        user_data['waiting_for_phone'] = True
        bot.register_next_step_handler(message, get_phone)
    else:
        dialogue_text += f'Ваш номер для связи: {user_data["phone"]}' + '\n\n'
        dialogue_text += 'Подтвердите Ваши контактные данные,\n'
        dialogue_text += 'или отправьте в чат, другой номер для связи.\n\n'
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.row(types.InlineKeyboardButton('Подтвердить Запись', callback_data='successful_booking'))
        markup.row(types.InlineKeyboardButton('<< Назад', callback_data='re_choose_time#cut_time'))
        bot.edit_message_text(dialogue_text, message.chat.id, message.id, reply_markup=markup)
        user_data['waiting_for_phone'] = True
        bot.register_next_step_handler(message, get_phone)


def successful_booking(call, meet_date, meet_time, tg_id, master_id, service_id):
    user_data = bot.__dict__['users'][call.chat.id]
    user_data['waiting_for_phone'] = False
    if user_data['first_time']:
        username = f'{call.chat.first_name} {call.chat.last_name}({call.chat.username})'
        username = username.replace(' None', '')
        username = username.replace('None', '')
        sql_register_new_user(call.chat.id, username, user_data['phone'])
    else:
        sql_put_user_phone(call.chat.id, user_data['phone'])

    dialogue_text = print_booking_text(user_data, not_confirmed=False)
    dialogue_text += f'Ваш номер для связи: {user_data["phone"]}' + '\n\n'
    message = bot.send_message(call.chat.id, dialogue_text)
    bot.delete_message(call.chat.id, user_data['last_message_id'])
    user_data['last_message_id'] = message.message_id
    registration_new_appointment(meet_date, meet_time, tg_id, master_id, service_id)
    start_menu(call)



# Добавление кнопки "позвонить нам" в ReplyKeyboardMarkup
@bot.message_handler(content_types=['text'])
def call_us(message):
    user_data = bot.__dict__['users'][message.chat.id]
    if user_data.get('waiting_for_phone', False):
        get_phone(message)
    elif "позвонить нам" in message.text.lower():
        bot.send_message(
            message.chat.id, "Рады звонку в любое время – 8 800 555 35 35"
        )
    else:
        bot.send_message(
            message.chat.id, "Выберите действие из меню"
                             " или введите 'позвонить нам',"
                             " чтобы связаться с нами."
        )


def get_phone(message):
    user_data = bot.__dict__['users'][message.chat.id]
    user_data.update({'phone': message.text})
    user_data['waiting_for_phone'] = False

    dialogue_text = print_booking_text(user_data)
    dialogue_text += f'Ваш номер для связи: {user_data["phone"]}' + '\n\n'
    dialogue_text += f'Подтвердите запись, или введите другой телефон для связи'

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton('Подтвердить Запись', callback_data='successful_booking'))
    markup.row(types.InlineKeyboardButton('<< Назад', callback_data='re_choose_time#cut_phone'))
    try:
        bot.edit_message_text(dialogue_text, message.chat.id, user_data['last_message_id'], reply_markup=markup)
        bot.register_next_step_handler(message, get_phone)
        time.sleep(2)
        bot.delete_message(message.chat.id, user_data['last_message_id'])
        user_data['last_message_id'] = message.message_id
    except Exception as error:
        print(error)


if __name__ == '__main__':
    print('\n\n\n')
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f'Infinity polling exception: {e}', exc_info=True)
        time.sleep(5)  # Ожидание перед повторным запуском опроса
