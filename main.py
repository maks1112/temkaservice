import telebot
from handlers import setup_handlers
from callbacks import setup_callbacks

bot = telebot.TeleBot('7006500687:AAHSmeddSmofp8u4omRB4EhTkt16FJgT1_o')

setup_handlers(bot)
setup_callbacks(bot)

bot.polling(none_stop=True)
