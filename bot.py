import telebot
import time
import sys
import os
from commands import register_commands

if not os.path.exists(os.path.join(os.path.dirname(__file__),"files/botFiles/config.txt")):
    with open("files/botFiles/config.txt","w") as f:
        f.write("token: YOUR_API_TOKEN\n\n")
        f.write("# это чат-айди, где есть бот(может быть группой), для личный сообщений используйте свое ID\n")
        f.write("admin: YOUR_ADMIN_ID\n")


def read_token_from_config():
    with open('files/botFiles/config.txt', 'r') as f:
        for line in f:
            if line.startswith('token:'):
                return line.split(':')[1].strip()
    raise ValueError("Token not found in config file.")

def read_admin_from_config():
    with open('files/botFiles/config.txt', 'r') as f:
        for line in f:
            if line.startswith('admin:'):
                return line.split(':')[1].strip()
    raise ValueError("Admin not found in config file.")

token = read_token_from_config()
admin = read_admin_from_config()

# Инициализация бота с токеном
bot = telebot.TeleBot(token)

def add_computer(ip):
    with open('files/botFiles/computer-list.txt', 'a') as f:
        f.write(ip + '\n')

online_status = {}

def update_ping(ip):
    online_status[ip] = time.time()  # Запоминаем время последнего пинга
    if ip not in read_computer_list():
        add_computer(ip)

def read_computer_list():
    with open('files/botFiles/computer-list.txt', 'r') as f:
        return [line.strip() for line in f.readlines()]

def check_online_status():
    current_time = time.time()
    online_computers = []
    for ip, last_ping in online_status.items():
        if current_time - last_ping <= 60:
            online_computers.append((ip, '🟢'))  # Онлайн
        else:
            online_computers.append((ip, '🔴'))  # Оффлайн
    return online_computers

@bot.message_handler(commands=['getonline'])
def get_online(message):
    online_computers = check_online_status()
    response = ""
    for ip, status in online_computers:
        response += f"{ip} - {status} - 0% потери пакетов\n"  # Упрощенный вывод
    bot.send_message(message.chat.id, response)

# Регистрация пользовательских команд
register_commands(bot)

# Запуск бота
bot.polling()
bot.send_message(admin,"Bot online!")