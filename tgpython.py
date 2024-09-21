import logging
import requests
import base64
import telebot
import threading
import time

# Токен бота из @BotFather
API_TOKEN = '7341685493:AAGsKsTZfF6LPql4R6fJJQ9qiUx3Mq1L5eQ'

# Токен GitHub
GITHUB_TOKEN = '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'
REPO_NAME = 'beka02221/localwebfrombot'  # Например: 'username/repo'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота
bot = telebot.TeleBot(API_TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне HTML-код, и я отправлю ссылку через минуту после загрузки.")

# Обработчик для получения HTML-кода
@bot.message_handler(content_types=['text'])
def handle_html_code(message):
    html_code = message.text

    # Путь к файлу, который будет создан или обновлен на GitHub
    file_path = 'index.html'
    
    # Проверяем, существует ли файл, чтобы получить его SHA для обновления
    sha = get_github_file_sha(file_path)

    # Делаем запрос к GitHub для создания или обновления файла
    response = create_or_update_github_file(file_path, html_code, sha)
    
    if response.status_code == 201 or response.status_code == 200:
        bot.reply_to(message, "Подождите минуту, пока ваш код загрузится затем в полученном сайте обнавите страницу что бы ваш код появился.")
        
        # Создаем и запускаем таймер для отправки ссылки через минуту
        threading.Timer(60, send_github_link, args=[message]).start()
    else:
        bot.reply_to(message, f"Произошла ошибка при загрузке файла на GitHub: {response.json()}")

# Функция для отправки ссылки через минуту
def send_github_link(message):
    # Генерируем ссылку на GitHub Pages
    gh_pages_link = f"https://{REPO_NAME.split('/')[0]}.github.io/{REPO_NAME.split('/')[1]}/"
    bot.reply_to(message, gh_pages_link)

# Получаем SHA файла, если он уже существует
def get_github_file_sha(file_path):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('sha')
    return None

# Создаем или обновляем файл на GitHub
def create_or_update_github_file(file_path, content, sha=None):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Кодируем содержимое файла в base64
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    data = {
        "message": "Upload or update HTML via bot",
        "content": encoded_content
    }

    # Если файл уже существует, добавляем SHA для обновления
    if sha:
        data["sha"] = sha
    
    # Отправляем запрос на создание или обновление файла в репозитории
    response = requests.put(url, json=data, headers=headers)
    return response

if __name__ == '__main__':
    # Запускаем бота
    bot.polling(none_stop=True)
