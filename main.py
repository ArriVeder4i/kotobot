import telebot
from telebot import types
import random
from openai import OpenAI
import threading

# Инициализация бота
bot = telebot.TeleBot("")

# Состояния для хранения данных пользователя (в контексте чата)
USER_DATA = {}
STATES = {
    'awaiting_birth_date': 'date',
    'awaiting_birth_time': 'time',
    'awaiting_birth_place': 'place',
    'awaiting_question': 'question'
}

# API-ключ OpenRouter
OPENROUTER_API_KEY = "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"

# Инициализация клиента OpenRouter
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


# Функция для создания клавиатуры
def create_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Спросить колоду♣', callback_data='question')
    btn2 = types.InlineKeyboardButton('Отношения❤', callback_data='relations')
    btn3 = types.InlineKeyboardButton('Совместимость♦', callback_data='compatibility')
    btn4 = types.InlineKeyboardButton('Расклад на сегодня♠', callback_data='today')
    btn5 = types.InlineKeyboardButton('Натальная карта', callback_data='natal_chart')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)

    markup.row(btn5)
    return markup


# Список Старших Арканов (добавь пути к GIF-файлам вручную)
major_arcana = [
    {'name': 'Шут', 'image_path': 'oldark/shut.gif'},  # Замени на реальный путь к GIF
    {'name': 'Маг', 'image_path': 'oldark/mag.gif'},
    {'name': 'Жрица', 'image_path': 'oldark/zhritsa.gif'},
    {'name': 'Императрица', 'image_path': 'oldark/imperatritsa.gif'},
    {'name': 'Император', 'image_path': 'oldark/imperator.gif'},
    {'name': 'Верховный жрец', 'image_path': 'oldark/zhets.gif'},
    {'name': 'Влюбленные', 'image_path': 'oldark/vlulennie.gif'},
    {'name': 'Колесница', 'image_path': 'oldark/kolesnitsa.gif'},
    {'name': 'Сила', 'image_path': 'oldark/sila.gif'},
    {'name': 'Отшельник', 'image_path': 'oldark/otshelnik.gif'},
    {'name': 'Колесо фортуны', 'image_path': 'oldark/koleso fortuni.gif'},
    {'name': 'Справедливость', 'image_path': 'oldark/pravosudie.gif'},
    {'name': 'Повешенный', 'image_path': 'oldark/poveshenniy.gif'},
    {'name': 'Смерть', 'image_path': 'oldark/smert.gif'},
    {'name': 'Умеренность', 'image_path': 'oldark/vozderzhanie.gif'},
    {'name': 'Дьявол', 'image_path': 'oldark/diavol.gif'},
    {'name': 'Башня', 'image_path': 'oldark/bashnia.gif'},
    {'name': 'Звезда', 'image_path': 'oldark/zvezda.gif'},
    {'name': 'Луна', 'image_path': 'oldark/luna.gif'},
    {'name': 'Солнце', 'image_path': 'oldark/solntse.gif'},
    {'name': 'Суд', 'image_path': 'oldark/sud.gif'},
    {'name': 'Мир', 'image_path': 'oldark/mir.gif'},
]


# Функция для разбиения длинного текста на части (максимум 4096 символов)
def split_long_message(text, max_length=4096):
    if len(text) <= max_length:
        return [text]
    parts = []
    while len(text) > max_length:
        split_point = text.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        parts.append(text[:split_point])
        text = text[split_point:].lstrip()
    if text:
        parts.append(text)
    return parts


# Функция для редактирования ответа нейросети
def edit_response(text):
    if text:
        # Заменяем * на ✨
        text = text.replace("*", "✨")
        text = text.replace("#", "🌙")
        text = text.replace("---", "🌕🌖🌗🌘🌑🌒🌓🌔🌙")
    return text


# Функция для запроса к OpenRouter с интерпретацией
def get_openrouter_interpretation(query, card_names, context):
    try:
        # Формируем запрос с данными пользователя и контекстом
        if context == "натальной карты":
            prompt = f"Составь натальную карту на основе следующих данных: дата рождения - {query['date']}, время рождения - {query['time']}, место рождения - {query['place']}. Включи основные аспекты личности, любви, карьеры и духовного роста, ограничь ответ 3000 символами. Используй астрологические подходы и добавь творческий подход."
        else:
            # Для карт Таро
            if query:
                cards_string = ", ".join(card_names) if card_names else ""
                prompt = f"Пользовательский вопрос: '{query}'. Дай краткую интерпретацию для {context} на основе таро-карты: {cards_string}. Включи значение карты для любви, карьеры и духовного роста, ограничь ответ 3000 символами. Используй традиционные значения таро и добавь творческий подход."
            else:
                cards_string = ", ".join(card_names)
                prompt = f"Дай краткую интерпретацию для {context} на основе следующих таро-карт: {cards_string}. Включи значение карт для любви, карьеры и духовного роста, ограничь ответ 3000 символами. Используй традиционные значения таро и добавь творческий подход."

        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        # Редактируем ответ перед возвратом
        return edit_response(response.choices[0].message.content if response.choices and response.choices[
            0].message.content else "Не удалось получить интерпретацию.")
    except Exception as e:
        return f"Ошибка при запросе к OpenRouter: {str(e)}"


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_photo(message.chat.id, photo=open('mystical_cat_tarot_reader.jpg', 'rb'))
    except FileNotFoundError:
        bot.send_message(message.chat.id,
                         "Извини, изображение кота-таролога не найдено. Пожалуйста, проверь путь к файлу!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при отправке изображения: {str(e)}")

    # Текст приветствия
    welcome_text = "🐾 Мяу-приветствую тебя, искатель тайн! 🧙‍♂️✨ Я Кот-бот Таролог, и мои мистические лапки готовы разложить карты судьбы. 🔮 Готов ли ты узнать, что шепчет тебе Вселенная? Потяни лапку за первой картой, и тайны откроются! 😺✨\n\nВот твой мистический кот-таролог! 🔮🐱✨ Пусть магия карт приведёт тебя к ответам, которые ты ищешь!"

    # Отправляем текст с клавиатурой
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_markup())


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    # Обработка вопроса к колоде
    if chat_id in USER_DATA and USER_DATA[chat_id].get('state') == 'awaiting_question':
        USER_DATA[chat_id]['question'] = text
        card = random.choice(major_arcana)
        bot.send_message(chat_id, f'Ваша карта: {card["name"]}')
        try:
            bot.send_animation(chat_id, animation=open(card['image_path'], 'rb'))
            bot.send_message(chat_id, "Устанавливаю связь со звёздами💫🪐")
            interpretation = get_openrouter_interpretation(text, [card['name']], "вопроса к колоде")
            for part in split_long_message(interpretation):
                bot.send_message(chat_id, part)
            # Возвращаем кнопки после интерпретации
            bot.send_message(chat_id, 'Выберите следующую опцию:', reply_markup=create_markup())
        except FileNotFoundError:
            bot.send_message(chat_id, "Извини, изображение карты не найдено. Пожалуйста, проверь путь к файлу!")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при отправке карты или интерпретации: {str(e)}")
        del USER_DATA[chat_id]  # Очищаем данные после обработки
        return

    # Обработка данных для натальной карты
    if chat_id in USER_DATA:
        state = USER_DATA[chat_id].get('state')
        if state == 'awaiting_birth_date':
            USER_DATA[chat_id]['date'] = text
            bot.send_message(chat_id, "Укажите время рождения (например, 14:30 или 2:30 PM):")
            USER_DATA[chat_id]['state'] = 'awaiting_birth_time'
        elif state == 'awaiting_birth_time':
            USER_DATA[chat_id]['time'] = text
            bot.send_message(chat_id, "Укажите место рождения (город и страна, например, Москва, Россия):")
            USER_DATA[chat_id]['state'] = 'awaiting_birth_place'
        elif state == 'awaiting_birth_place':
            USER_DATA[chat_id]['place'] = text
            try:
                bot.send_message(chat_id, "Устанавливаю связь со звёздами💫🪐")
                interpretation = get_openrouter_interpretation(USER_DATA[chat_id], [], "натальной карты")
                for part in split_long_message(interpretation):
                    bot.send_message(chat_id, part)
                # Возвращаем кнопки после интерпретации
                bot.send_message(chat_id, 'Выберите следующую опцию:', reply_markup=create_markup())
            except Exception as e:
                bot.send_message(chat_id, f"Ошибка при составлении натальной карты: {str(e)}")
            del USER_DATA[chat_id]  # Очищаем данные после обработки
        return

    # Возвращаем клавиатуру для других текстовых сообщений
    bot.send_message(chat_id, 'Выберите опцию:', reply_markup=create_markup())


# Обработчик callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    # Сразу отвечаем на callback-запрос, чтобы избежать таймаута
    bot.answer_callback_query(call.id)

    if call.data == 'question':
        bot.send_message(chat_id, "Что вы хотите спросить у колоды?")
        USER_DATA[chat_id] = {'state': 'awaiting_question'}
    elif call.data == 'relations':
        cards = random.sample(major_arcana, 3)
        card_names = [card['name'] for card in cards]
        bot.send_message(chat_id, f'Карты для расклада на отношения: {", ".join(card_names)}')
        try:
            for card in cards:
                bot.send_animation(chat_id, animation=open(card['image_path'], 'rb'))
            bot.send_message(chat_id, "Устанавливаю связь со звёздами💫🪐")
            interpretation = get_openrouter_interpretation(None, card_names, "расклада на отношения")
            for part in split_long_message(interpretation):
                bot.send_message(chat_id, part)
            # Возвращаем кнопки после интерпретации
            bot.send_message(chat_id, 'Выберите следующую опцию:', reply_markup=create_markup())
        except FileNotFoundError:
            bot.send_message(chat_id, "Извини, изображение карты не найдено. Пожалуйста, проверь путь к файлу!")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при отправке карт или интерпретации: {str(e)}")
    elif call.data == 'compatibility':
        cards = random.sample(major_arcana, 3)
        card_names = [card['name'] for card in cards]
        bot.send_message(chat_id, f'Карты для расклада на совместимость: {", ".join(card_names)}')
        try:
            for card in cards:
                bot.send_animation(chat_id, animation=open(card['image_path'], 'rb'))
            bot.send_message(chat_id, "Устанавливаю связь со звёздами💫🪐")
            interpretation = get_openrouter_interpretation(None, card_names, "расклада на совместимость")
            for part in split_long_message(interpretation):
                bot.send_message(chat_id, part)
            # Возвращаем кнопки после интерпретации
            bot.send_message(chat_id, 'Выберите следующую опцию:', reply_markup=create_markup())
        except FileNotFoundError:
            bot.send_message(chat_id, "Извини, изображение карты не найдено. Пожалуйста, проверь путь к файлу!")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при отправке карт или интерпретации: {str(e)}")
    elif call.data == 'today':
        card = random.choice(major_arcana)
        bot.send_message(chat_id, f'Карта дня: {card["name"]}')
        try:
            bot.send_animation(chat_id, animation=open(card['image_path'], 'rb'))
            bot.send_message(chat_id, "Устанавливаю связь со звёздами💫🪐")
            interpretation = get_openrouter_interpretation(None, [card['name']], "расклада на сегодня")
            for part in split_long_message(interpretation):
                bot.send_message(chat_id, part)
            # Возвращаем кнопки после интерпретации
            bot.send_message(chat_id, 'Выберите следующую опцию:', reply_markup=create_markup())
        except FileNotFoundError:
            bot.send_message(chat_id, "Извини, изображение карты не найдено. Пожалуйста, проверь путь к файлу!")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при отправке карты или интерпретации: {str(e)}")
    elif call.data == 'natal_chart':
        bot.send_message(chat_id, "Укажите дату рождения (например, 15.03.1990):")
        USER_DATA[chat_id] = {'state': 'awaiting_birth_date'}


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
