import time
import requests
import telebot
from telebot import types
import phonenumbers
from phonenumbers import carrier, geocoder
import socket
import json
import os
from crypto_pay_sync import cryptopay
from fake_useragent import UserAgent
from time import sleep
from random import randint

BOT_TOKEN = '7149009411:AAEUtU2eq1oiVl4DBEbUjEr5RFQOg0oB6KE'
API_KEY = 'bdf74038f14a42e8a2a38ec23a05842e'

crypto_client = cryptopay.Crypto("235743:AA84QeqOlCzUf6mpxbYwiuHtFOfOkN716j2", testnet=False)
bot = telebot.TeleBot(BOT_TOKEN)

ua = UserAgent()

output_format = 'usual'
users_data = {}
group_id = -1002166461586

def check_subscription(chat_id, user_id):
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def read_users_data():
    try:
        with open('users_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def write_user_data(user_id):
    users = read_users_data()
    if str(user_id) not in users:
        users[str(user_id)] = True
        with open('users_data.json', 'w') as file:
            json.dump(users, file)

def check_user_in_data(user_id):
    users = read_users_data()
    return str(user_id) in users

def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    item_ip = types.InlineKeyboardButton("💻 Айпи", callback_data='ip')
    item_phone = types.InlineKeyboardButton("📱 Номер", callback_data='phone')
    item_settings = types.InlineKeyboardButton("⚙️ Настройки", callback_data='settings')
    item_spoof = types.InlineKeyboardButton("🕵️‍♂️ Спуфинг User-Agent", callback_data='spoof')
    markup.add(item_ip, item_phone, item_settings, item_spoof)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Функция для отправки сообщений
def send_message(chat_id, text, reply_markup=None):
    bot.send_message(chat_id, text, reply_markup=reply_markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if check_user_in_data(message.from_user.id):
        chat_member = bot.get_chat_member('@FightSearch', message.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            button_1 = types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/FightSearch")
            markup.add(button_1)
            bot.send_message(message.chat.id, "⚠️ Пожалуйста подпишитесь на канал для использования бота.", reply_markup=markup)
            return

        if message.chat.id not in users_data:
            users_data[message.chat.id] = {
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name
            }
            # bot.send_message(group_id, f"Новый пользователь в боте: {message.from_user.username} ({message.from_user.first_name} {message.from_user.last_name})")

        markup = types.InlineKeyboardMarkup()
        item_ip = types.InlineKeyboardButton("💻 Айпи", callback_data='ip')
        item_phone = types.InlineKeyboardButton("📱 Номер", callback_data='phone')
        item_settings = types.InlineKeyboardButton("⚙️ Настройки", callback_data='settings')
        item_spoof = types.InlineKeyboardButton("🕵️‍♂️ Спуфинг User-Agent", callback_data='spoof')
        markup.add(item_ip, item_phone, item_settings, item_spoof)

        bot.send_message(message.chat.id,
                         f"👋 Здравствуй! Ты в боте от @fightlor. \n\n"
                         f"> Это бот для пробития осинт информации",
                         reply_markup=markup)
    else:
        invoice = crypto_client.createInvoice("USDT", "1", params={"description": "Покупка использования бота."})
        result = invoice.get('result', {})
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_1 = types.InlineKeyboardButton("💰Купить", url=result['pay_url'])
        button_2 = types.InlineKeyboardButton("💵 Я оплатил", callback_data=f"confirm_{result['invoice_id']}")
        markup.add(button_1, button_2)
        bot.send_message(message.chat.id, "⚠️ Приобретите пожалуйста подписку чтобы использовать бота.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_pay(call):
    invoice_id = call.data.split("_")[1]
    invoices = crypto_client.get_invoices(invoice_ids=[invoice_id]).get('result', {}).get('items', [])
    if invoices and invoices[0]['status'] == 'paid':
        user_id = call.from_user.id
        bot.send_message(call.message.chat.id, "🎉")
        time.sleep(1)
        bot.send_message(call.message.chat.id, "Оплата успешна! Можете использовать бота.")
        write_user_data(user_id)
    else:
        bot.send_message(call.message.chat.id, "❌")
        bot.send_message(call.message.chat.id, "Оплата не прошла, попробуйте еще раз!")

# Меню настроек
@bot.callback_query_handler(func=lambda call: call.data == 'settings')
def handle_settings(call):
    markup = types.InlineKeyboardMarkup()
    item_json = types.InlineKeyboardButton("JSON", callback_data='json')
    item_txt = types.InlineKeyboardButton("TXT", callback_data='txt')
    item_usual = types.InlineKeyboardButton("Обычный", callback_data='usual')
    markup.add(item_json, item_txt, item_usual)

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Выберите формат вывода:",
                          reply_markup=markup)
    # Обработчик настроек

@bot.callback_query_handler(func=lambda call: call.data in ['json', 'txt', 'usual'])
def handle_output_format(call):
    global output_format
    output_format = call.data

    # Возвращаем в главное меню
    send_welcome(call.message)

@bot.message_handler(commands=['online'])
def handle_online(message):
    online_count = len(users_data)
    bot.send_message(message.chat.id, f"Сейчас онлайн {online_count} человек.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
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
    elif call.data == 'spoof':
        send_message(chat_id, "Введите URL (логера для спуфинга например grabify):")
        bot.register_next_step_handler(call.message, handle_spoof_url)
    else:
        send_message(chat_id, "Обработка других кнопок не реализована.")

def handle_spoof_url(message):
    chat_id = message.chat.id
    url_to_fetch = message.text
    for _ in range(3):  # Делаем 3 запроса
        try:
            headers = {'User-Agent': ua.random}
            response = requests.get(url_to_fetch, headers=headers)
            send_message(chat_id, f"Спуфинг User-Agent: {headers['User-Agent']}\nСтатус-код ответа: {response.status_code}")
            sleep(randint(1, 3))  # Пауза между запросами
        except requests.RequestException as e:
            send_message(chat_id, f"Произошла ошибка: {e}")
            break  # Прерываем цикл при возникновении ошибки
    
    # Возвращаемся к главному меню после выполнения запросов
    main_menu(chat_id)

# Обработка IP-адреса
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

            # Получение данных из API ip-api.com
            try:
                response = requests.get(f'http://ip-api.com/json/{ip}')
                response.raise_for_status()
                ip_api_data = response.json()
            except requests.exceptions.RequestException as e:
                ip_api_data = f"Ошибка при получении данных с ip-api.com: {e}"

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

*WHOIS:*
role:           {whois_dict.get('role', 'N/A')}
address:        {whois_dict.get('address', 'N/A')}
admin-c:        {whois_dict.get('admin-c', 'N/A')}
tech-c:         {whois_dict.get('tech-c', 'N/A')}
nic-hdl:        {whois_dict.get('nic-hdl', 'N/A')}
mnt-by:         {whois_dict.get('mnt-by', 'N/A')}
created:        {whois_dict.get('created', 'N/A')}
last-modified:  {whois_dict.get('last-modified', 'N/A')}
source:         {whois_dict.get('source', 'N/A')}

*ip-api.com:*
ISP:           {ip_api_data.get('isp', 'N/A')}
AS:            {ip_api_data.get('as', 'N/A')}
Mobile:        {ip_api_data.get('mobile', 'N/A')}
Proxy:         {ip_api_data.get('proxy', 'N/A')}
Hosting:      {ip_api_data.get('hosting', 'N/A')}
Type:          {ip_api_data.get('type', 'N/A')}
Continent:     {ip_api_data.get('continent', 'N/A')}
Country:       {ip_api_data.get('country', 'N/A')}
RegionName:    {ip_api_data.get('regionName', 'N/A')}
City:          {ip_api_data.get('city', 'N/A')}
Zip:           {ip_api_data.get('zip', 'N/A')}
Lat:           {ip_api_data.get('lat', 'N/A')}
Lon:           {ip_api_data.get('lon', 'N/A')}
Timezone:      {ip_api_data.get('timezone', 'N/A')}
Currency:      {ip_api_data.get('currency', 'N/A')}
            """

            if output_format == 'json':
                with open('ip_info.json', 'w') as f:
                    json.dump(data, f)
                bot.send_document(message.chat.id, open('ip_info.json', 'rb'),
                                  caption="Информация сохранена в файл ip_info.json.")
            elif output_format == 'txt':
                with open('ip_info.txt', 'w') as f:
                    f.write(info)
                bot.send_document(message.chat.id, open('ip_info.txt', 'rb'),
                                  caption="Информация сохранена в файл ip_info.txt.")
            else:
                bot.reply_to(message, info)
        else:
            bot.reply_to(message, "Не удалось получить информацию о местоположении.")
        send_welcome(message)

    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Ошибка: {e}")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

# Обработка номера телефона
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

                if output_format == 'json':
                    with open('phone_info.json', 'w') as f:
                        json.dump(data, f)
                    bot.send_document(message.chat.id, open('phone_info.json', 'rb'),
                                      caption="Информация сохранена в файл phone_info.json.")
                elif output_format == 'txt':
                    with open('phone_info.txt', 'w') as f:
                        f.write(info)
                    bot.send_document(message.chat.id, open('phone_info.txt', 'rb'),
                                      caption="Информация сохранена в файл phone_info.txt.")
                else:
                    bot.reply_to(message, info)
            else:
                bot.reply_to(message, "Не удалось получить информацию о номере.")
        else:
            bot.reply_to(message, "Некорректный номер телефона.")
    except phonenumbers.phonenumberutil.NumberParseException:
        bot.reply_to(message, "Некорректный номер телефона.")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Ошибка при запросе к API: {e}")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

# Запускаем бота
if __name__ == '__main__':
    bot.infinity_polling()
