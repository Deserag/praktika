import random
import telebot
from db import connect_to_db
from datetime import datetime

TOKEN = "6524657285:AAH6cfR-cZ30GBwAZg_ExiKCZOPWbiD1H-w"
bot = telebot.TeleBot(TOKEN)
user_state = {}
user_cart = {}
user_data = {}


def get_user_orders(user_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT Наименование, Количество, Сумма FROM Заказы WHERE Телеграм_Id = %s;", (user_id,))
    orders = [{'name': row[0], 'quantity': row[1], 'price': row[2]} for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return orders

def show_product_options(message, product_name):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    add_to_cart_button = telebot.types.KeyboardButton(f"Добавить в корзину: {product_name}")
    back_button = telebot.types.KeyboardButton("Назад")
    keyboard.add(add_to_cart_button, back_button)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text.startswith("Добавить в корзину: "))
def handle_add_to_cart(message):
    product_name = message.text[len("Добавить в корзину: "):].strip()
    # Получаем информацию о товаре
    product_info = get_product_info(product_name)
    if product_info:
        product_id = product_info[0]
        product_price = product_info[3]
        quantity = 1
        total_price = product_price * quantity

        # Получаем уникальный номер заказа, например, используя случайные числа
        order_number = random.randint(100000, 999999)
        user_id = message.chat.id

        # Добавляем заказ в базу данных
        add_order_to_db(order_number, user_id, product_id, quantity, product_price, total_price, product_name)

        bot.send_message(user_id,f"Товар '{product_name}' добавлен в корзину, количество: {quantity}, на сумму: {total_price:.2f} руб.")
        show_main_menu(message)
    else:
        bot.send_message(message.chat.id, f"Товар '{product_name}' не найден.")
def add_order_to_db(order_number, user_id, product_id, quantity, product_price, total_price, product_name):
    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Код_товара FROM Товары WHERE Наименование = %s;", (product_name,))
            product_id = cursor.fetchone()
            cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
            user_id = cursor.fetchone()
            # Форматируем цену без конвертации, если в базе данных уже используется тип numeric
            cursor.execute("INSERT INTO Заказы (Номер_заказа, ФИО_клиента, Код_товара, Количество, Цена, Общая_цена) VALUES (%s, %s, %s, %s, %s, %s)",
                (order_number, user_id, product_id, quantity, "%.2f" % product_price, "%.2f" % total_price))
            connection.commit()
    finally:
        connection.close()
def clear_user_state(user_id):
    user_state.pop(user_id, None)
# Создайте функцию для добавления заказа в базу данных:


def is_user_registered(user_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT EXISTS(SELECT 1 FROM Клиенты WHERE Телеграм_Id=%s)", (user_id,))
    result = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return result

def send_verification_or_registration_menu(message):
    user_id = message.chat.id
    if is_user_registered(user_id):
        msg = bot.send_message(user_id, "Подтвердите ФИО:")
        bot.register_next_step_handler(msg, process_fio_verification)
    else:
        msg = bot.send_message(user_id, "Регистрация.\nВведите ФИО:")
        bot.register_next_step_handler(msg, process_registration)

def get_product_info(product_name):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT Категория, Наименование, Описание, Цена, Изображение FROM Товары WHERE Наименование = %s;",
                   (product_name,))
    # Данные извлекаются в кортеже, так что мы можем их распаковать.
    product_info = cursor.fetchone()
    cursor.close()
    connection.close()

    if product_info:
        # Распаковываем данные и конвертируем цену в float для дальнейших расчетов.
        category, name, description, price, image = product_info
        price = float(price)  # Конвертируем Decimal в float
        return category, name, description, price, image
    else:
        return None  # или raise Exception("Товар не найден") - по вашему усмотрению
def process_fio_verification(message):
    user_id = message.chat.id
    user_state[message.chat.id] = "registered"
    user_fio = message.text.strip()

    if check_fio(user_id, user_fio):
        user_state[message.chat.id] = "registered"
        show_main_menu(message)
    else:
        bot.send_message(user_id, "Неверное ФИО. Пожалуйста, попробуйте еще раз.")
        bot.register_next_step_handler(message, process_fio_verification)

def check_fio(user_id, user_fio):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_Id = %s", (user_id,))
    result = cursor.fetchone()
    if result and user_fio.lower() == result[0].lower():
        return True
    else:
        return False

def process_registration(message):
    # Регистрируем пользователя в системе, сохраняем его ФИО в базе данных
    user_id = message.chat.id
    user_fio = message.text.strip()
    connection = connect_to_db()
    cursor = connection.cursor()
    user_state[message.chat.id] = "registered"
    cursor.execute("INSERT INTO Клиенты (Телеграм_Id, ФИО) VALUES (%s, %s)", (user_id, user_fio))
    connection.commit()
    cursor.close()
    connection.close()

    # Показываем главное меню после регистрации
    show_main_menu(message)


@bot.message_handler(func=lambda message: message.text == "Назад" )
def handle_back_to_main_menu(message):
    show_main_menu(message)

@bot.message_handler(func=lambda message: message.text == "Нaзад" )
def handle_back_to_main_menu(message):
    handle_bue(message)

@bot.message_handler(func=lambda message: message.text == "Изменение заказа")
def handle_payment(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button_plus= telebot.types.KeyboardButton(text="+")
    button_minus = telebot.types.KeyboardButton(text="-")
    button_clear = telebot.types.KeyboardButton(text="Очистка корзины")
    button_back = telebot.types.KeyboardButton(text="Нaзад")
    button_main = telebot.types.KeyboardButton(text="Главное меню")
    keyboard.add(button_plus, button_minus, button_clear, button_back, button_main)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    handle_cart(message)

@bot.message_handler(func=lambda message: message.text == "Оплата")
def handle_payment(message):
    connection = connect_to_db()
    user_id = message.from_user.id
    current_time = datetime.now().date()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
            user_fio = cursor.fetchone()
            cursor.execute("SELECT Код_заказа, Номер_заказа,  Код_товара, Количество, Цена, Общая_цена FROM Заказы WHERE ФИО_клиента = %s;", (user_fio))
            product_info = cursor.fetchone()
            if product_info:
                code_order = random.randint(0, 1000000)
                number_order = product_info[1]
                code_tovar = product_info[2]
                kolichestvo = product_info[3]
                price = product_info[4]
                sym_price = product_info[5]
                status = "Оплачено"
                cursor.execute("INSERT INTO История_заказов (Код_заказа, Номер_заказа, ФИО_клиента,Дата,Код_товара, Количество, Цена, Общая_цена,Статус ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (code_order, code_tovar, user_fio, current_time,code_tovar, kolichestvo, price, sym_price, status))
                cursor.execute("DELETE FROM Заказы WHERE ФИО_клиента = %s;", (user_fio,))
                connection.commit()
                bot.send_message(message.chat.id, "Спасибо за покупку")
            else:
                bot.send_message(message.chat.id,"Корзина пуста")
    finally:
        connection.close()

def clear_user_cart(user_id):
    user_cart.pop(user_id, None)


# Функция отображения меню каталога
def handle_catalog(message):
    categories = get_categories()
    keyboard = telebot.types.InlineKeyboardMarkup()
    for category in categories:
        callback_data = 'category_{}'.format(category)
        keyboard.add(telebot.types.InlineKeyboardButton(text=category, callback_data=callback_data))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=keyboard)


# Функция для получения списка категорий из базы данных
def get_categories():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT Категория FROM Товары;")
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return categories

# Функция для получения списка товаров по выбранной категории из базы данных
def get_products_by_category(category):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT Наименование FROM Товары WHERE Категория = %s;", (category,))
    products = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return products


# Функция для обработки команды /catalog или кнопки "Каталог"
@bot.message_handler(func=lambda message: message.text == "Каталог")
def handle_catalog(message):
    # Получаем список категорий из базы данных
    categories = get_categories()

    # Отправляем кнопки с названиями категорий
    keyboard = telebot.types.InlineKeyboardMarkup()
    for category in categories:
        callback_data = 'category_{}'.format(category)
        keyboard.add(telebot.types.InlineKeyboardButton(text=category, callback_data=callback_data))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category_callback_query(call):
    # Извлекаем название категории
    category = call.data[len("category_"):]

    # Получение списка товаров для данной категории
    products = get_products_by_category(category)

    # Подготовка клавиатуры с товарами
    keyboard = telebot.types.InlineKeyboardMarkup()
    for product in products:
        callback_data = f'product_{product}'
        keyboard.add(telebot.types.InlineKeyboardButton(text=product, callback_data=callback_data))

    # Отправляем сообщение с клавиатурой товаров
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Товары в категории '{category}':", reply_markup=keyboard)


# Добавьте обработчик вызовов для выбора товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def handle_product_callback_query(call):
    # Извлекаем название товара
    product_name = call.data[len("product_"):]
    show_product_options(call.message, product_name)


    product_info = get_product_info(product_name)

    # Отправляем информацию о товаре
    if product_info:
        # Если у товара есть изображение, отправляем его вместе с описанием
        if product_info[-1]:  # Предпоследний элемент - это предположительно изображение
            bot.send_photo(call.message.chat.id, product_info[-1],
                           caption=f'{product_info[1]} - {product_info[3]}\n{product_info[2]}')
        else:
            bot.send_message(call.message.chat.id, f'{product_info[1]} - {product_info[3]}\n{product_info[2]}')
    else:
        bot.send_message(call.message.chat.id, 'Информация о данном товаре отсутствует.')

@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category_callback_query(call):
    bot.answer_callback_query(call.id)

def show_main_menu(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)  # Установите row_width равным 3
    button_catalog = telebot.types.KeyboardButton(text="Каталог")
    button_cart = telebot.types.KeyboardButton(text="Корзина")
    button_about = telebot.types.KeyboardButton(text="О магазине")
    keyboard.add(button_catalog, button_cart, button_about)  # Добавляем все кнопки сразу
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "О магазине")
def about_the_shop(message):
    bot.send_message(message.chat.id, "Наш магазин предлагает широкий ассортимент компьютерной техники и аксессуаров. "
                                      "Мы гарантируем качество и надежность наших товаров. "
                                      "Следите за новинками на нашем сайте!")
def handle_cart(message):
    user_id = message.chat.id
    user_cart[user_id] = {}
    connection = connect_to_db()
    cursor = connection.cursor()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
            user_fio = cursor.fetchone()
            if user_fio:
                cursor.execute("""
                               SELECT Заказы.Номер_заказа, Заказы.Код_товара, Товары.Наименование, Заказы.Количество, Заказы.Цена
                               FROM Заказы
                               JOIN Товары ON Заказы.Код_товара = Товары.Код_товара
                               WHERE Заказы.ФИО_клиента = %s;
                               """, (user_fio[0],))
                cart_contents = cursor.fetchall()
                if cart_contents:
                    for order_number, product_id, product_name, quantity, price in cart_contents:
                        markup = telebot.types.InlineKeyboardMarkup()  # Создаем новую клавиатуру для каждого товара
                        markup.add(telebot.types.InlineKeyboardButton("Выбрать", callback_data=f'select_{product_id}'))
                        product_text = f"Товар: {product_name}\nКоличество: {quantity}шт.\nЦена: {price}руб. за ед."
                        user_cart[user_id][product_id] = {'name': product_name, 'quantity': quantity}
                        bot.send_message(user_id, product_text, reply_markup=markup)
                    bot.send_message(user_id, "Выберите товар для изменения или удаления из корзины.")
                else:
                    bot.send_message(user_id, "Ваша корзина пуста.")
    finally:
        connection.close()


def add_product_to_cart(user_id, product_info, quantity):
    # Реализация добавления товара в корзину пользователя с учетом количества
    # Предполагается, что в user_cart[user_id] мы храним информацию о корзине пользователя
    if user_id not in user_cart:
        user_cart[user_id] = []
    user_cart[user_id].append({'product_info': product_info, 'quantity': quantity})

# Обработчик для кнопки "Корзина"
@bot.message_handler(func=lambda message: message.text == "Корзина")
def handle_bue(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button_catalog = telebot.types.KeyboardButton(text="Оплата")
    button_cart = telebot.types.KeyboardButton(text="Изменение заказа")
    button_about = telebot.types.KeyboardButton(text="Назад")
    keyboard.add(button_catalog, button_cart, button_about)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def callback_query_handler(call):
    product_id = call.data[len('select_'):]

    # Здесь мы должны убедиться, что user_state существует и инициализировать его при необходимости.
    if call.message.chat.id not in user_state:
        user_state[call.message.chat.id] = {}

    # Установка выбранного product_id
    user_state[call.message.chat.id]['selected_product_id'] = product_id

    # Сообщаем пользователю, что товар выбран
    bot.answer_callback_query(call.id, "Товар выбран.")  # Отправляем уведомление пользователю



def show_catalog_menu(message):
    categories = get_categories()

    # Отправляем кнопки с названиями категорий
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in categories:
        keyboard.add(telebot.types.KeyboardButton(text=category))
    # Добавляем кнопку "Назад"
    keyboard.add(telebot.types.KeyboardButton(text="Главное меню"))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=keyboard)


# Обработчик для кнопки "Каталог"
@bot.message_handler(func=lambda message: message.text == "Каталог" and user_state.get(message.chat.id) == "registered")
def handle_catalog_button(message):
    show_catalog_menu(message)


# Обработчик для выбора товара из категории
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "registered" and message.text in get_products_by_category(user_state[message.chat.id]))
def handle_category_choice(message):
    category = message.text
    # Остальная реализация остается прежней

# Обработчик для выбора товара из категории
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "registered" and message.text in get_products_by_category(user_state[message.chat.id]['category']))
def handle_product_choice(message):
    product_name = message.text
    product_info = get_product_info(product_name)
    if product_info:
        category, name, description, price, image = product_info
        # Убираем лишние нули из цены и добавляем единицу измерения
        price = "{:.2f}".format(price) if price is not None else "Не указана"
        price_str = f"{price} Руб."
        product_message = f"Категория: {category}\nНаименование: {name}\nОписание: {description}\nЦена: {price_str}"
        if image:
            bot.send_photo(message.chat.id, image, caption=product_message)
        else:
            bot.send_message(message.chat.id, product_message)
    else:
        bot.send_message(message.chat.id, "Товар не найден.")


@bot.message_handler(func=lambda message: message.text == "+")
def increase_in_number_goods(message):
    user_id = message.chat.id
    if user_id in user_state and 'selected_product_id' in user_state[user_id]:
        product_id = int(user_state[user_id]['selected_product_id'])
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
        user_fio = cursor.fetchone()
        user_cart[user_id][product_id]['quantity'] += 1
        new_quantity = user_cart[user_id][product_id]['quantity']
        cursor.execute("""UPDATE Заказы SET Количество = %s WHERE Код_товара = %s AND ФИО_клиента = %s;""", (new_quantity, product_id, user_fio))
        connection.commit()
        bot.send_message(message.chat.id, f"Количество товара увеличено. Теперь его количество: {new_quantity}")
        connection.close()

@bot.message_handler(func=lambda message: message.text == "-")
def decrease_in_number_goods(message):
    user_id = message.chat.id
    if user_id in user_state and 'selected_product_id' in user_state[user_id]:
        product_id = int(user_state[user_id]['selected_product_id'])
        connection = connect_to_db()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
            user_fio_tuple = cursor.fetchone()

            if user_fio_tuple:
                user_fio = user_fio_tuple[0]

                if product_id in user_cart[user_id]:
                    user_cart[user_id][product_id]['quantity'] -= 1
                    new_quantity = user_cart[user_id][product_id]['quantity']

                    if new_quantity > 0:
                        cursor.execute("""UPDATE Заказы SET Количество = %s WHERE Код_товара = %s AND ФИО_клиента = %s;""", (new_quantity, product_id, user_fio))
                        bot.send_message(message.chat.id, f"Количество товара уменьшено. Теперь его количество: {new_quantity}")
                    else:
                        cursor.execute("""DELETE FROM Заказы WHERE Код_товара = %s AND ФИО_клиента = %s;""", (product_id, user_fio))
                        bot.send_message(message.chat.id, "Товар удален из корзины.")
                        del user_cart[user_id][product_id]

                else:
                    bot.send_message(message.chat.id, "Товар отсутствует в корзине.")

            else:
                bot.send_message(message.chat.id, "Информация о пользователе не найдена.")

            connection.commit()
        except Exception as e:
            print(e)  # Логируем ошибку
            bot.send_message(message.chat.id, "Произошла ошибка при обновлении корзины.")
        finally:
            cursor.close()
            connection.close()


@bot.message_handler(func=lambda message: message.text == "Очистка корзины")
def delete(message):
    user_id = message.chat.id
    connection = connect_to_db()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT ФИО FROM Клиенты WHERE Телеграм_id = %s;", (user_id,))
        user_fio_tuple = cursor.fetchone()
        if user_fio_tuple:
            user_fio = user_fio_tuple[0]
            cursor.execute("DELETE FROM Заказы WHERE ФИО_клиента = %s;", (user_fio,))
            connection.commit()
            bot.send_message(message.chat.id, "Корзина очищена.")
        else:
            bot.send_message(message.chat.id, "Не найден пользователь для очистки.")
    except Exception as e:
        print(e)  # Логируем ошибку
        bot.send_message(message.chat.id, "Произошла ошибка при очистке корзины.")
    finally:
        cursor.close()
        connection.close()



@bot.message_handler(func=lambda message: message.text == "Главное меню" )
def handle_back_to_category_menu(message):
    show_main_menu(message)
# Обработчик для выбора категории товаров
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "registered" and message.text in get_categories())
def handle_category_choice(message):
    category = message.text
    products = get_products_by_category(category)

    # Сохраняем выбранную категорию в состояние пользователя
    user_state[message.chat.id]['category'] = category

    # Отправляем кнопки с названиями товаров
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for product in products:
        keyboard.add(telebot.types.KeyboardButton(text=product))
    keyboard.add(telebot.types.KeyboardButton(text="Назад"), telebot.types.KeyboardButton(text="Главное меню"))
    bot.send_message(message.chat.id, f"Товары в категории '{category}':", reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_verification_or_registration_menu(message)

bot.polling(none_stop=True)