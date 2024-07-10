from telebot import TeleBot
from telebot.types import InputMediaPhoto

from db_sqlite import (get_data_purchase, take_action_buy, update_purchase_quantity,
                       update_balance, delete_data_purchase, get_data_my_profile,
                       take_action_catalog, enqueue_purchase, get_data_payment, take_my_purchase)
from handlers import handle_deposit, handle_no_stock, handle_free_item, handle_purchase, handle_amount
from payment import check_invoice
from utils import create_inline_buttons, update_message


def setup_callbacks(bot: TeleBot):
    @bot.callback_query_handler(func=lambda call: call.data == 'deposit')
    def callback_deposit(call):
        handle_deposit(bot, call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_buy')
    def callback_back_to_buy(call):
        data = get_data_purchase(call.message.chat.id)
        update_message(bot, call, data['quantity'], data['name'])

    @bot.callback_query_handler(func=lambda call: call.data == 'promo')
    def callback_promo(call):
        photo_path = '../tg_market/photographies/promocode.jpeg'
        text = 'Введите промокод:'
        buttons = [[('Назад к покупке', 'back_to_buy')]]
        markup = create_inline_buttons(buttons)
        with open(photo_path, 'rb') as photo_file:
            promo_photo = photo_file.read()
        bot.edit_message_media(
            media=InputMediaPhoto(promo_photo, caption=text),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('increase_'))
    def callback_increase(call):
        add_quantily = int(call.data.split('_')[1])
        data = get_data_purchase(call.message.chat.id)
        if data:
            name = data['name']
            new_quantity = data['quantity'] + add_quantily
            quantity = take_action_buy(name)['quantity']
            if quantity < new_quantity:
                new_quantity = quantity
            update_purchase_quantity(call.message.chat.id, new_quantity)
            update_message(bot, call, new_quantity, name)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('decrease_'))
    def callback_decrease(call):
        add_quantily = int(call.data.split('_')[1])
        data = get_data_purchase(call.message.chat.id)
        if data and data['quantity'] > 1:
            name = data['name']
            new_quantity = data['quantity'] - add_quantily
            if new_quantity < 1:
                new_quantity = 1
            update_purchase_quantity(call.message.chat.id, new_quantity)
            update_message(bot, call, new_quantity, name)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def buy(call):
        chat_id = call.message.chat.id
        purchase_data = get_data_purchase(chat_id)
        name = purchase_data['name']
        buy_action = take_action_buy(name)
        price = buy_action.get('price')
        download_link = buy_action.get('download_link')

        if call.data.endswith('zero') and price:
            handle_no_stock(bot, chat_id)
        elif not price:
            handle_free_item(bot, chat_id, download_link)
        else:
            handle_purchase(bot, chat_id, price, download_link)

        bot.delete_message(chat_id, call.message.message_id)
        delete_data_purchase(chat_id)

    @bot.callback_query_handler(func=lambda call: call.data in ('crypto_bot',))
    def process_payment(call):
        chat_id = call.message.chat.id
        bot.delete_message(chat_id, call.message.message_id)
        balance = get_data_my_profile(chat_id)['balance']
        with open('../tg_market/texts/process_payment.txt', 'r', encoding='UTF-8') as file:
            text = file.read()
            text_formated = text.format(balance=balance)
        msg = bot.send_message(chat_id, text_formated)
        bot.register_next_step_handler(msg, lambda message: handle_amount(bot, message))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('check_payment_'))
    def callback_check_payment(call):
        chat_id = call.message.chat.id
        invoice_id = call.data.split('_')[-1]
        invoice_status = check_invoice(invoice_id)
        print(invoice_status)
        if invoice_status.get('ok'):
            invoice = None
            for item in invoice_status['result']['items']:
                if item['invoice_id'] == int(invoice_id):
                    invoice = item
                    break
            status = invoice['status']
            if status == 'paid':
                bot.send_message(chat_id, f"Инвойс с ID {invoice_id} был оплачен.")
                amount = invoice['amount']
                update_balance(chat_id, amount)
            else:
                pay_url = get_data_payment(chat_id)['pay_url']
                print(pay_url)
                buttons = [
                    [("Проверить оплату", f'check_payment_{invoice_id}')],
                    [("Оплатить", pay_url)]
                ]
                markup = create_inline_buttons(buttons)

                with open('../tg_market/texts/send_invoice.txt', 'r', encoding='UTF-8') as file:
                    text = file.read()
                bot.edit_message_text(f"{text}\n\nИнвойс с ID {invoice_id} еще не оплачен. Статус: {status}.",
                                      chat_id, call.message.message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, f"Ошибка при получении чеков: {invoice_status.json()}")

    @bot.callback_query_handler(func=lambda call: call.data == 'purchase_history')
    def purchase_history(call):
        chat_id = call.message.chat.id
        my_purchases = take_my_purchase(chat_id)

        if my_purchases:
            text = ''
            for count in range(len(my_purchases)):
                text += my_purchases[-count] + '\n' + '-' * 40 + '\n'
            bot.send_message(chat_id, text)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        chat_id = call.message.chat.id

        action = take_action_catalog(call.data)
        if action:
            if get_data_purchase(chat_id):
                delete_data_purchase(chat_id)

            if action['photo_path'] and action['text_path']:
                photo_path = action['photo_path']
                text_path = action['text_path']
                with open(photo_path, 'rb') as photo_file, open(text_path, 'r', encoding='UTF-8') as text_file:
                    photo = photo_file.read()
                    buttons = []
                    if isinstance(action['next_action'], tuple):
                        for i, caption in enumerate(action['text_caption']):
                            buttons.append([(f"{caption} - {action['price'][i]}$", action['next_action'][i])])
                    buttons.append([('На главную каталога', 'catalog')])
                    markup = create_inline_buttons(buttons)
                    bot.send_photo(call.message.chat.id, photo, caption=text_file.read(), reply_markup=markup)
                return
            elif 'button_text' in action:
                buttons = action['button_text']
                markup = create_inline_buttons(buttons)
                with open(action['photo_path'], 'rb') as photo:
                    if action.get('text_caption', ''):
                        bot.delete_message(chat_id, call.message.message_id - 1)
                        bot.send_photo(call.message.chat.id, photo, caption=action.get('text_caption', ''),
                                       reply_markup=markup)
                    else:
                        bot.send_photo(call.message.chat.id, photo, reply_markup=markup)
                return
            else:
                bot.send_message(call.message.chat.id, action.get('text_caption', ''))
                return
        action = take_action_buy(call.data)
        if action:
            quantity = action.get('quantity', None)
            if quantity:
                count = 1
            else:
                count = 0
            enqueue_purchase(chat_id, action['price'], call.data, quantity=count)
            update_message(bot, call, count, call.data)
