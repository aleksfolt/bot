import requests
import telebot
from telebot import types
import phonenumbers
from phonenumbers import carrier, geocoder
import socket

# Замените этот токен на свой токен бота
BOT_TOKEN = '7149009411:AAEUtU2eq1oiVl4DBEbUjEr5RFQOg0oB6KE'

# Замените этот API-ключ на свой ключ от opencagedata.com
API_KEY = 'bdf74038f14a42e8a2a38ec23a05842e'


bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    item_ip = types.InlineKeyboardButton("💻 Айпи", callback_data='ip')
    item_phone = types.InlineKeyboardButton("📱 Номер", callback_data='phone')
    markup.add(item_ip, item_phone)

    bot.send_message(message.chat.id, 
                    f"👋 Здравствуй! Ты в боте от @fightlor. \n\n"
                    f"> Это бот для пробития осинт информации", 
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'ip':
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text="Введите IP-адрес:")
        bot.register_next_step_handler(call.message, handle_ip) 
    elif call.data == 'phone':
        bot.edit_message_text(chat_id=call.message.chat.id, 
                              message_id=call.message.message_id,
                              text="Введите номер телефона:")
        bot.register_next_step_handler(call.message, handle_phone) 

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # В главном меню не обрабатываем сообщения
    if message.text.startswith('https://') or message.text.startswith('http://'):
        pass
    elif message.text.startswith('+'):
        pass
    else:
        bot.reply_to(message, "Некорректный ввод. Используйте кнопки.")

def handle_ip(message):
    ip = message.text
    try:
        # Проверка, является ли IP-адрес действительным
        try:
            socket.inet_aton(ip)
        except socket.error:
            bot.reply_to(message, "Некорректный IP-адрес.")
            return

        # Получение информации об IP-адресе
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        response.raise_for_status()
        data = response.json()

        city = data.get('city')
        region = data.get('region')
        country = data.get('country')
        org = data.get('org')
        loc = data.get('loc')
        hostname = data.get('hostname')
        postal = data.get('postal')
        timezone = data.get('timezone')

        # Получение данных о местоположении с помощью opencagedata.com
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city},{region},{country}&key={API_KEY}&language=ru"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])
        if results:
            result = results[0]
            latitude = result.get('geometry', {}).get('lat')
            longitude = result.get('geometry', {}).get('lng')

            # Получение данных WHOIS
            try:
                response = requests.get(f'https://api.hackertarget.com/whois/?q={ip}')
                response.raise_for_status()
                whois_data = response.text
                whois_lines = whois_data.splitlines()
                whois_dict = {}
                for line in whois_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        whois_dict[key.strip()] = value.strip()
            except requests.exceptions.RequestException as e:
                whois_data = f"Ошибка при получении данных WHOIS: {e}"
                whois_dict = {}

            # Ссылка на карту
            map_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

            # Форматирование ответа
            info = f"""
Информация об IP-адресе {ip}:
Город: {city}
Регион: {region}
Страна: {country}
Почтовый индекс: {postal}
Часовой пояс: {timezone}
Организация: {org}
Хост: {hostname}
Местоположение на карте: {map_link}

**WHOIS:**
role:           {whois_dict.get('role', 'N/A')}
address:        {whois_dict.get('address', 'N/A')}
admin-c:        {whois_dict.get('admin-c', 'N/A')}
tech-c:         {whois_dict.get('tech-c', 'N/A')}
nic-hdl:        {whois_dict.get('nic-hdl', 'N/A')}
mnt-by:         {whois_dict.get('mnt-by', 'N/A')}
created:        {whois_dict.get('created', 'N/A')}
last-modified:  {whois_dict.get('last-modified', 'N/A')}
source:         {whois_dict.get('source', 'N/A')}

            """

            bot.reply_to(message, info)
        else:
            bot.reply_to(message, "Не удалось получить информацию о местоположении.")
        send_welcome(message)

    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Ошибка: {e}")

def handle_phone(message):
    phone_number = message.text
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if phonenumbers.is_valid_number(parsed_number):
            # Получение информации о номере
            carrier_name = carrier.name_for_number(parsed_number, "ru")
            region = geocoder.description_for_number(parsed_number, "ru")

            # Получение данных из API opencagedata.com
            url = f"https://api.opencagedata.com/geocode/v1/json?q={phone_number}&key={API_KEY}&language=ru"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Извлечение информации
            results = data.get('results', [])
            if results:
                result = results[0]
                country_code = result.get('components', {}).get('country_code')
                city = result.get('components', {}).get('city', '')
                region = result.get('components', {}).get('state', '')

                info = f"""
Информация о номере {phone_number}:
Оператор: {carrier_name}
Регион: {region}
Страна: {country_code}
Город: {city}
                """

                bot.reply_to(message, info)
            else:
                bot.reply_to(message, "Не удалось получить информацию о номере.")
        else:
            bot.reply_to(message, "Некорректный номер телефона.")
    except phonenumbers.phonenumberutil.NumberParseException:
        bot.reply_to(message, "Некорректный номер телефона.")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Ошибка при запросе к API: {e}")

if __name__ == '__main__':
    bot.infinity_polling()
