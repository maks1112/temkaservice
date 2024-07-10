from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from db_sqlite import take_action_buy


def create_inline_buttons(buttons):
    markup = InlineKeyboardMarkup()
    for row in buttons:
        row_buttons = []
        for text, data in row:
            if 'http' in data:
                print(data)
                row_buttons.append(InlineKeyboardButton(text=text, url=data))
            else:
                row_buttons.append(InlineKeyboardButton(text=text, callback_data=data))
        markup.row(*row_buttons)
    return markup


def update_message(bot, call, count, name):
    action = take_action_buy(name)
    quantity = action['quantity']
    price = action['price']
    photo_path = action['photo_path']
    text_path = action['text_path']

    with open(photo_path, 'rb') as photo_file, open(text_path, 'r', encoding='UTF-8') as text_file:
        photo = photo_file.read()
        text = text_file.read()
        buttons = [
            [('🔺', f'increase_1'), (f'{count} шт', 'count'), ('🔻', f'decrease_1')],
            [('10 🔺', f'increase_10'), ('🔻 10', f'decrease_10')],
            [(f'Купить за {(price * count):.2f}$', f'buy_{(price * count):.2f}') if count > 0 else (
                f'Купить за {price:.2f}$', 'buy_zero')],
            [(f'В наличии {quantity}', 'quantity')],
            [('Все', 'increase_999999')],
            [('На главную каталога', 'catalog')]
        ]
        markup = create_inline_buttons(buttons)
        bot.edit_message_media(
            media=InputMediaPhoto(photo, caption=text),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )


