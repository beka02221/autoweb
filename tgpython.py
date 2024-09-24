import logging
import requests
import base64
import telebot
import threading

# Токен бота из @BotFather
API_TOKEN = ''

# Токен GitHub
GITHUB_TOKEN = ''
REPO_NAME = 'beka02221/localwebfrombot'  # Например: 'username/repo'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота
bot = telebot.TeleBot(API_TOKEN)

user_data = {}

# Сообщения на разных языках
messages = {
    'English': {
        'welcome': "Hello! Please send me your HTML code, and I will send you the link after a minute.",
        'choose_language': "Choose your language:",
        'send_html': "Please send your HTML code:",
        'wait_message': "Please wait a minute your code is uploading.Then refresh the given page to see the result.",
        'link_sent': "Your page is available at:",
        'error': "An error occurred while uploading the file: {error}",
        'edit_choice': "Would you like to edit your index.html?",
        'edit_html': "To edit index.html, send the new HTML code."
    },
    'Русский': {
        'welcome': "Привет! Пожалуйста, отправь мне свой HTML-код, и я отправлю тебе ссылку через минуту.",
        'choose_language': "Выберите язык:",
        'send_html': "Пожалуйста, отправьте свой HTML-код:",
        'wait_message': "Подождите минуту, ваш код загружается.(чтобы увидеть результат обновите страницу в полученном ссылке).",
        'link_sent': "Ваша страница доступна по адресу:",
        'error': "Произошла ошибка при загрузке файла: {error}",
        'edit_choice': "Хотите изменить свой index.html?",
        'edit_html': "Чтобы изменить index.html, отправьте новый HTML-код."
    }
}

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('English', 'Русский')
    bot.send_message(message.chat.id, messages['Русский']['choose_language'], reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['English', 'Русский'])
def language_choice(message):
    user_data[message.chat.id] = {'language': message.text}
    bot.send_message(message.chat.id, messages[message.text]['send_html'])
    bot.register_next_step_handler(message, handle_html_code)

# Обработчик для получения HTML-кода
def handle_html_code(message):
    html_code = message.text

    # Путь к файлу, который будет создан или обновлен на GitHub
    file_path = 'index.html'
    
    # Проверяем, существует ли файл, чтобы получить его SHA для обновления
    sha = get_github_file_sha(file_path)

    # Делаем запрос к GitHub для создания или обновления файла
    response = create_or_update_github_file(file_path, html_code, sha)
    
    if response.status_code == 201 or response.status_code == 200:
        bot.reply_to(message, messages[user_data[message.chat.id]['language']]['wait_message'])
        
        # Создаем и запускаем таймер для отправки ссылки через минуту
        threading.Timer(60, send_github_link, args=[message]).start()
    else:
        bot.reply_to(message, messages[user_data[message.chat.id]['language']]['error'].format(error=response.json()))

# Функция для отправки ссылки через минуту
def send_github_link(message):
    # Генерируем ссылку на GitHub Pages
    gh_pages_link = f"https://{REPO_NAME.split('/')[0]}.github.io/{REPO_NAME.split('/')[1]}/"
    bot.reply_to(message, f"{messages[user_data[message.chat.id]['language']]['link_sent']} {gh_pages_link}")

    # Запрашиваем, нужно ли изменить index.html
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Yes', 'No')
    bot.send_message(message.chat.id, messages[user_data[message.chat.id]['language']]['edit_choice'], reply_markup=markup)
    bot.register_next_step_handler(message, handle_edit_choice)

# Обработка выбора для изменения index.html
def handle_edit_choice(message):
    if message.text == 'Yes':
        bot.send_message(message.chat.id, messages[user_data[message.chat.id]['language']]['edit_html'])
        bot.register_next_step_handler(message, edit_html_code)
    else:
        bot.send_message(message.chat.id, "Thank you! If you need to change anything, just send /start!")

# Обработка изменения index.html
def edit_html_code(message):
    html_code = message.text
    file_path = 'index.html'
    sha = get_github_file_sha(file_path)
    
    response = create_or_update_github_file(file_path, html_code, sha)
    
    if response.status_code == 200:
        bot.reply_to(message, "index.html has been updated.")
    else:
        bot.reply_to(message, messages[user_data[message.chat.id]['language']]['error'].format(error=response.json()))

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
        "message": "Upload or update file via bot",
        "content": encoded_content
    }

    # Если файл уже существует, добавляем SHA для обновления
    if sha:
        data["sha"] = sha
    
    # Отправляем запрос на создание или обновление файла в репозитории
    response = requests.put(url, json=data, headers=headers)
    
    # Логируем ответ для отладки
    logging.info(f"GitHub response: {response.status_code} - {response.json()}")
    
    return response

if __name__ == '__main__':
    # Запускаем бота
    bot.polling(none_stop=True)
