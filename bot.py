import telebot
import time
import os
import json
from flask import Flask, request, jsonify
from threading import Thread
from telebot import types  # Импортируем типы для кнопок
from commands import register_commands
from ping3 import ping  # Импортируем ping из библиотеки ping3

# Инициализация Flask приложения
app = Flask(__name__)

# Проверка наличия файла конфигурации
config_path = os.path.join(os.path.dirname(__file__), "files/botFiles/config.json")
if not os.path.exists(config_path):
    with open(config_path, "w") as f:
        json.dump({"token": "YOUR_API_TOKEN", "admin": "YOUR_ADMIN_ID"}, f)

def read_config():
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['token'], config['admin']

# Чтение токена и ID администратора из конфигурации
token, admin = read_config()

# Инициализация бота с токеном
bot = telebot.TeleBot(token)

online_status = {}

def add_computer(ip):
    with open('files/botFiles/computer-list.txt', 'a') as f:
        f.write(ip + '\n')

def read_computer_list():
    if not os.path.exists('files/botFiles/computer-list.txt'):
        return []
    with open('files/botFiles/computer-list.txt', 'r') as f:
        return [line.strip() for line in f.readlines()]

def load_online_status():
    computers = read_computer_list()
    for ip in computers:
        online_status[ip] = time.time()  # Устанавливаем текущее время как последнее время пинга

def update_ping(ip):
    online_status[ip] = time.time()  # Запоминаем время последнего пинга
    if ip not in read_computer_list():
        add_computer(ip)

def check_online_status():
    current_time = time.time()
    online_computers = []
    for ip, last_ping in online_status.items():
        if current_time - last_ping <= 60:
            online_computers.append((ip, '🟢', last_ping))  # Сохраняем время последнего пинга
        else:
            online_computers.append((ip, '🔴', last_ping))  # Оффлайн
    return online_computers

@bot.message_handler(commands=['ping'])
def get_online(message):
    online_computers = check_online_status()
    response = "Выберите сервер для пинга:\n"
    markup = types.InlineKeyboardMarkup()  # Создаем клавиатуру

    for ip, status, last_ping in online_computers:
        button = types.InlineKeyboardButton(text=f"{ip} - {status}", callback_data=f"ping_{ip}")
        markup.add(button)

    bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ping_'))
def handle_ping(call):
    ip = call.data.split('_')[1]  # Извлекаем IP из callback_data
    response = f"Пингую сервер {ip}..."
    bot.send_message(call.message.chat.id, response)  # Отправляем сообщение о начале пинга

    # Выполняем пинг
    ping_time = ping(ip)
    if ping_time is not False:
        response = f"Сервер {ip} пингован: {ping_time * 1000:.2f} мс."
        update_ping(ip)  # Обновляем время последнего пинга
    else:
        response = f"Не удалось пинговать сервер {ip}. Возможно, он недоступен."

    bot.answer_callback_query(call.id)  # Подтверждаем нажатие кнопки
    bot.send_message(call.message.chat.id, response)

@bot.message_handler(commands=['pingall'])
def ping_all(message):
    response = "Список всех пингованных серверов:\n\n"
    current_time = time.time()
    for ip in online_status.keys():
        ping_time = ping(ip)  # Пингуем сервер для получения актуального времени
        status = '🟢' if ping_time is not False else '🔴'
        milliseconds = int(ping_time * 1000) if ping_time is not None else 0  # Время в миллисекундах
        response += f"{ip} - {status} - {milliseconds} мс\n"
    bot.send_message(message.chat.id, response)

# Flask маршрут для обработки POST запросов для пинга
@app.route('/', methods=['POST'])
def ping_route():
    data = request.json
    ip = data.get('ip')
    if ip:
        update_ping(ip)  # Обновляем время пинга для данного IP
        return jsonify({"message": f"Ping updated for {ip}"}), 200
    else:
        return jsonify({"error": "IP address is required"}), 400

# Регистрация дополнительных команд и запуск бота
def start_bot():
    register_commands(bot)
    load_online_status()  # Загружаем статус онлайн компьютеров
    bot.polling(none_stop=True)

if __name__ == "__main__":
    Thread(target=start_bot).start()
    app.run(host='0.0.0.0', port=5000)