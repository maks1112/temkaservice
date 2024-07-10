from datetime import datetime

from telebot.types import ReplyKeyboardMarkup
from utils import create_inline_buttons
from db_sqlite import add_to_db, get_data_purchase, delete_data_purchase, get_data_my_profile, update_balance, \
    update_quantity, update_my_purchase
from payment import check_auth, send_invoice
from telebot import TeleBot


def setup_handlers(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def start(message):
        add_to_db(message.from_user.id)
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row('Каталог', 'Профиль')
        markup.row('Пополнить', 'Связаться')

        welcome_photo = open(r'photographies/welcome.jpeg', 'rb')
        with open(r'../tg_market/texts/welcome.txt', 'r', encoding='UTF-8') as file:
            welcome_text = file.read()
            bot.send_photo(message.from_user.id, photo=welcome_photo, caption=welcome_text, reply_markup=markup,
                           parse_mode='HTML')

    @bot.message_handler(func=lambda message: message.text in ['Каталог', 'Профиль', 'Пополнить', 'Связаться'])
    def handle_reply_markup(message):
        from_user_id = message.from_user.id
        if get_data_purchase(from_user_id):
            delete_data_purchase(from_user_id)

        try:
            bot.delete_message(from_user_id, message.message_id - 1)
        except:
            bot.delete_message(from_user_id, message.message_id)

        if message.text == 'Каталог':
            bot.send_message(from_user_id, "🛒")
            buttons = [
                [('Магазин аккаунтов', 'shop_accounts')],
                [('Схемы', 'schemes'), ('Скрипты ', 'scripts')]
            ]
            markup = create_inline_buttons(buttons)

            catalog_photo = open('photographies/catalog.jpeg', 'rb')
            bot.send_photo(from_user_id, catalog_photo, reply_markup=markup)

        elif message.text == 'Профиль':
            bot.send_message(from_user_id, "🪪")
            buttons = [
                [('Настройки', 'settings')],
                [('История покупок', 'purchase_history')]
            ]
            markup = create_inline_buttons(buttons)

            data = get_data_my_profile(from_user_id)
            balance = data['balance']
            quantity = data['my_purchase'].count(',')
            registrate = data['registrate']
            with open('../tg_market/texts/my_prfile.txt', 'r', encoding='UTF-8') as file:
                text = file.read()
            formatted_text = text.format(user_id=from_user_id, balance=balance, registrate=registrate,
                                         quantity=quantity)
            bot.send_message(from_user_id, formatted_text, reply_markup=markup)

        elif message.text == 'Пополнить':
            handle_deposit(bot, from_user_id)

        elif message.text == 'Связаться':
            bot.send_message(from_user_id, "👀")
            with open('../tg_market/texts/contact.txt', 'r', encoding='UTF-8') as file:
                contact_text = file.read()
            bot.send_message(from_user_id, contact_text)

    @bot.message_handler(content_types=['text'])
    def text(message):
        bot.send_message(message.chat.id, 'Команда не найдена.')


def handle_amount(bot, message):
    chat_id = message.chat.id
    text = message.text

    try:
        amount = float(text)
        if amount >= 0.05 and check_auth():
            send_invoice(bot, message, amount)
        else:
            msg = bot.send_message(chat_id, 'Введите сумму больше 0.05$')
            bot.register_next_step_handler(msg, lambda message: handle_amount(bot, message))

    except ValueError:
        bot.send_message(chat_id, "Вы перенаправлены на главную.")


def handle_deposit(bot, user_id):
    bot.send_message(user_id, '💸')
    photo = open('photographies/profile.jpeg', 'rb')
    buttons = [
        [('Crypto bot', 'crypto_bot')]
    ]
    markup = create_inline_buttons(buttons)
    bot.send_photo(user_id, photo, caption="Выберите способ пополнения:", reply_markup=markup)


def handle_no_stock(bot, chat_id):
    buttons = [[('Каталог', 'catalog')]]
    markup = create_inline_buttons(buttons)
    bot.send_message(chat_id, 'Нету в наличии', reply_markup=markup)


def handle_free_item(bot, chat_id, download_link):
    with open('../tg_market/texts/result_buy.txt', 'r', encoding='UTF-8') as file:
        text = file.read()
    bot.send_message(chat_id, text + download_link)
    bot.send_message(chat_id, '💸')


def handle_purchase(bot, chat_id, price, download_link):
    profile_data = get_data_my_profile(chat_id)
    balance = profile_data['balance']
    data = get_data_purchase(chat_id)
    if balance >= price:
        update_balance(chat_id, price*data['quantity'])
        if download_link:
            with open('../tg_market/texts/result_buy.txt', 'r', encoding='UTF-8') as file:
                text = file.read()
            bot.send_message(chat_id, text + download_link)
            bot.send_message(chat_id, '💸')
            update_quantity(data['name'], data['quantity'])
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('../tg_market/texts/purchase_info.txt', 'r') as file:
                text = file.read()
                print(text)
                purchase_info = text.format(_time=current_time, download_link=download_link)
            update_my_purchase(chat_id, purchase_info)

    else:
        buttons = [[('Пополнить', 'deposit')],
                   [('Каталог', 'catalog')]]
        markup = create_inline_buttons(buttons)
        with open('../tg_market/texts/not_enough_money.txt', 'r', encoding='UTF-8') as file:
            text = file.read()
        text_format = text.format(balance=balance)
        bot.send_message(chat_id, text_format, reply_markup=markup)