import requests
import json

import telebot

from utils import create_inline_buttons
from db_sqlite import add_data_payment

CRYPTO_BOT_API_TOKEN = '193888:AA2HH2t1uAFfYfT20h6VHhZIo6tP0vGEsLH'


def check_auth():
    CHECK_AUTH_URL = 'https://pay.crypt.bot/api/getMe'

    headers = {
        'Content-Type': 'application/json',
        'Crypto-Pay-API-Token': CRYPTO_BOT_API_TOKEN
    }
    response = requests.post(CHECK_AUTH_URL, headers=headers)
    return response.json()


def create_invoice(amount, description):
    CREATE_INVOICE_URL = 'https://pay.crypt.bot/api/createInvoice'

    headers = {
        'Content-Type': 'application/json',
        'Crypto-Pay-API-Token': CRYPTO_BOT_API_TOKEN
    }
    data = {
        'asset': 'USDT',
        'amount': str(amount),
        'description': description,
        'hidden_message': 'Thank you for your payment!',
        'paid_btn_name': 'callback',
        'paid_btn_url': 'https://t.me/GrassBuild_bot'
    }
    response = requests.post(CREATE_INVOICE_URL, headers=headers, data=json.dumps(data))
    return response.json()


def check_invoice(invoice_id):
    CHECK_INVOICE_URL = 'https://pay.crypt.bot/api/getInvoices'

    headers = {
        'Content-Type': 'application/json',
        'Crypto-Pay-API-Token': CRYPTO_BOT_API_TOKEN
    }
    data = {
        'invoice_id': invoice_id
    }
    response = requests.post(CHECK_INVOICE_URL, headers=headers, data=json.dumps(data))
    return response.json()


def send_invoice(bot, message, amount):
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(message.chat.id, message.message_id-1)
    description = 'Payment for Temka Service'
    invoice = create_invoice(amount, description)
    if invoice.get('ok'):
        invoice_id = invoice['result']['invoice_id']
        pay_url = invoice['result']['pay_url']

        add_data_payment(message.chat.id, invoice_id, pay_url)
        markup = telebot.types.InlineKeyboardMarkup()
        buttons = [
            [("Проверить оплату", f'check_payment_{invoice_id}')],
            [("Оплатить", f'{pay_url}')]
        ]
        markup = create_inline_buttons(buttons)
        with open('../tg_market/texts/send_invoice.txt', 'r', encoding='UTF-8') as file:
            text = file.read()
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Ошибка при создании инвойса. Попробуйте еще раз.")
