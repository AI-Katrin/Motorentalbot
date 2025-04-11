import asyncio
from openai import AsyncOpenAI
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, MenuButtonCommands, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ContentType
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN, MINIAPP_URL, EMPLOYEE_CHAT_ID, OPENAI_PROXY, OPENAI_API_KEY
from dotenv import load_dotenv
import aiohttp
from aiohttp_socks import ProxyConnector
import httpx
import logging
logging.basicConfig(level=logging.INFO)



bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

http_client = None
aclient = None

#if OPENAI_PROXY:
#    logging.info(f"🟢 Используем прокси: {OPENAI_PROXY}")
#    transport = httpx.AsyncHTTPTransport(proxy=OPENAI_PROXY)
#    http_client = httpx.AsyncClient(transport=transport)
#else:
#    logging.info("🟢 Без прокси")
#    http_client = httpx.AsyncClient()

logging.info("🟢 Тестируем без прокси")
http_client = httpx.AsyncClient()

aclient = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=http_client
)

# Определяем состояния для процесса заявки
class UrgentRequestFSM(StatesGroup):
    waiting_for_contact = State()
    waiting_for_motorcycle = State()
    waiting_for_pickup = State()
    waiting_for_delivery = State()

# Раздел "Заявка на обратный звонок"
class CallbackRequestFSM(StatesGroup):
    waiting_for_contact = State()
    waiting_for_comment = State()

# Раздел "Маршрут для путешествия"
class RouteFSM(StatesGroup):
    in_dialog = State()  # состояние активного диалога с ChatGPT


async def get_chatgpt_response(prompt: str, state: FSMContext) -> str:
    try:
        # Получаем текущую историю
        data = await state.get_data()
        history = data.get("chat_history", [])

        # Добавляем текущее сообщение пользователя
        history.append({"role": "user", "content": prompt})

        # Добавляем system prompt только один раз в самом начале
        messages = [{"role": "system", "content": ('''
                Ты - опытный гид по мотопутешествиям. На основе данных из запроса ты составляешь маршрут для мотопутешествия. Анализируй маршруты, опубликованные в интернете, опыт других путешественников, твои знания об особенностях мототуров. 
                Для составления маршрута важно учесть: 
                1. Тайминг поездки (важно, чтобы люди не ехали ночью). Учитывай время восхода и время захода солнца в указанную даты
                2. Погодные условия (помни, что мы едем на мотоцикле, нам неприятен дождь, снег и все подобное). Данные о погоде бери с gismeteo.ru, учитывай даты поездки
                3. Заправки по маршруту (учитывай модель мотоцикла и средний расход топлива этого мотоцикла). Данные о заправках бери с Яндекс.карт, учитывай их рейтинг и отзывы
                4. Места, где можно поесть. Учитывай примерное время между приемами пищи, заведения выбирай с высоким рейтингом на Яндекс.картах или Google.maps.
                5. Отели. Выбирай 3-4*. Если будет запрос на другой уровень (например, другая зведность или стоимость проживания), то учитывай то, что хочет клиент. Всегда смотри на рейтинг этих отелей на Яндекс.картах, Google.maps, booking
                6. Достопримечательности, которые можно посетить по маршруту
                7. Дорожные условия. Всегда предупреждай клиента, если могут возникнуть какие-то сложности (например, грунтовая дорога, манера вождения местных жителей, дождь, отсутствие сотовой связи, недостаток заправок)
                
                Ответ выдавай в формате (например, маршрут из Санкт-Петербурга в Карелию):
                "Карелия – субъект Российской Федерации расположенный на Северо-Западе страны с населением около 500 000 человек. Карелия – это край лесов, озер и рек. На территории Карелии проживают малочисленные народы России – карелы, ижора и вепсы. Исторически территория Карелии неоднократна переходила от Финляндии к России, что безусловно оставило свой след в культуре этого края.
                Главная идея данного тура – это, во-первых, показать настоящую Карелию, которая находится вдали от столицы региона г. Петрозаводска; погрузиться в карельскую глубинку, покататься по грунтовым дорогам и побывать в старинных деревнях. А во-вторых, познакомиться с культурой финно-угорских племен, которая сохранилась и дошла до наших дней.
                
                Маршрут можно условно разделить на две составляющих:
                Дикая, малонаселенная часть, где маршрут проходит в основном по грунтовым дорогам. Здесь не везде есть гостиницы высокого уровня, не везде есть связь и привычный уровень комфорта.
                Наиболее туристическая часть, в которой находится столица, главные достопримечательности и привычные атрибуты цивилизации.
                
                Главные особенности тура:
                Бывшие финские города Выборг и Сортавала
                Карельские деревни Суднозеро, Вокнаволок и др., которые находятся под охраной государства
                Нетронутая карельская природа
                Грунтовые дороги
                Чистейшие реки и озера
                о. Кижи и образцы древнерусского деревянного зодчества
                Тур начинается и заканчивается в дружественном нам городе Санкт-Петербурге. 
                
                Даты поездки: 18-29 июня
                Продолжительность: 12 дней
                Общий километраж: 2750 км
                Уровень сложности: средне-сложный. Будет около 30% грунтовых дорог, уверенные навыки езды по грунту обязательны!!!
                Дороги: 70% асфальт, 30% грунт
                
                Маршрут:
                Санкт-Петербург – Сортавала – Суоярви – Гимолы – Костомукша – Калевала – Медвежьегорск – Петрозаводск – Лодейное поле – Санкт-Петербург
                
                Программа по дням:
                День 1.  Санкт-Петербург – Сортавала, 430 км. Рассвет в 06:12, закат в 17:00
                09:00 - Направляемся в сторону Выборга. В городе небольшая прогулка по центру и обед в кафе "Х". 
                12:00 - Далее осмотр кирхы Ряйсяля в поселке Мельниково.
                16:00 Едем в Сортавалу. Заселяемся в отель "Х". Живем в городе, ужинаем в ресторане "Кружево", куда добираемся на морском трансфере. Информация о трансфере:
                
                Маршрут на карте: (ты присылаешь координаты каждой точки для того, чтобы пользователь мог составить себе маршрут на Яндекс.картах)
                Заправки по маршруту с учетом среднего расхода топлива Х л/км для вашего мотоцикла Х:  (здесь ты указываешь информацию о заправках по маршруту и координаты для добавления на карту)
                Информация о достопримечательностях: (здесь ты указываешь ссылки на информацию о достопримечательностях из дня маршрута и координаты для добавления на карту)
                Отель: (ссылка на отель и координаты для добавления на карту)
                Кафе: (ссылка на информацию о кафе и координаты для добавления на карту)
                
                День 2. Сортавала – Суоярви, 215 км. Рассвет в 06:13, закат в 16:58
                Сегодня будет день грунтовых дорог, большая часть которых проходит по территории заказника Толвоярви. По пути будут встречаться деревянные бревенчатые мосты, гати и участки с большим количеством луж, включая знаменитую «царь-лужу». Длина последней составляет 150 метров, а уровень воды может достигать 50 см.
                Путешествие по Карелии предполагает перемещение по диким местам, поэтому не рассчитываем на обед в местах с привычным уровнем сервиса. Вместо этого будем устраивать пикники на природе.
                
                09:00 - Направляемся в сторону заказника Толвоярви. 
                12:00- 15:00 посещаем какую-то достопримечательность, затем обедаем
                17:00 - Отправляемся в Суоярви
                
                Маршрут на карте: (ты присылаешь координаты каждой точки для того, чтобы пользователь мог составить себе маршрут на Яндекс.картах)
                Заправки по маршруту с учетом среднего расхода топлива Х л/км для вашего мотоцикла Х:  (здесь ты указываешь информацию о заправках по маршруту и координаты для добавления на карту)
                Информация о достопримечательностях: (здесь ты указываешь ссылки на информацию о достопримечательностях из дня маршрута и координаты для добавления на карту)
                Отель: (ссылка на отель и координаты для добавления на карту)
                Кафе: (ссылка на информацию о кафе и координаты для добавления на карту)''')}] + history

        # Отправляем запрос в ChatGPT
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        # Сохраняем ответ в истории
        answer = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": answer})

        # Обновляем историю в состоянии
        await state.update_data(chat_history=history)

        return answer
    except Exception as e:
        return f"Ошибка при обращении к ChatGPT: {e}"


# Расширяем функцию отправки главного меню, добавляя новую кнопку
async def send_main_menu(chat_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Аренда мотоциклов",
        callback_data="rent_motorcycle"  # Теперь кнопка вызывает запрос номера
    ))
    builder.row(types.InlineKeyboardButton(
        text="Вызвать мотоэвакуатор",
        callback_data="mototow"
    ))
    builder.row(types.InlineKeyboardButton(
        text="Заявка на обратный звонок",
        callback_data="callback_request"
    ))
    builder.row(types.InlineKeyboardButton(
        text="Маршрут для путешествия",
        callback_data="route"
    ))
    keyboard = builder.as_markup()
    await bot.send_message(chat_id, "Добро пожаловать в MotoRentalBot. Выберите действие:", reply_markup=keyboard)

# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()  # Сбросить текущее состояние
    await bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonCommands())
    await send_main_menu(message.chat.id)

@dp.callback_query(F.data == "rent_motorcycle")
async def request_contact_before_rent(callback_query: types.CallbackQuery, state: FSMContext):
    #Запрашиваем номер телефона перед открытием WebApp
    await bot.answer_callback_query(callback_query.id)
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await bot.send_message(
        callback_query.from_user.id,
        "Для авторизации и просмотра доступных мотоциклов отправьте ваш контакт.",
        reply_markup=contact_keyboard
    )
    await state.set_state("waiting_for_contact")  # Устанавливаем состояние ожидания контакта

## Обработчик для кнопки "Аренда мотоциклов"
@dp.message(F.content_type == ContentType.CONTACT, StateFilter("waiting_for_contact"))
async def process_contact_and_open_webapp(message: types.Message, state: FSMContext):
    """Обрабатываем контакт и открываем Mini App"""
    phone_number = message.contact.phone_number
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    await state.update_data(phone_number=phone_number)
    # Уведомляем менеджера о входе нового пользователя
    await bot.send_message(EMPLOYEE_CHAT_ID, f"{user_name} (ID: {user_id}) вошел в Mini App\nТелефон: {phone_number}")
    await state.clear()
    # Отправляем inline-кнопку для запуска Mini App
    miniapp_url = f"{MINIAPP_URL}?user_id={user_id}&phone={phone_number}"  # Добавляем параметры
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=miniapp_url))]
        ]
    )
    await bot.send_message(
        message.chat.id,
        "Контакт получен. Теперь можете перейти в Mini App для оформления аренды.",
        reply_markup=keyboard
    )


## Обработчик для кнопки "Вызвать Мотоэвакуатор"
@dp.callback_query(F.data == "mototow")
async def process_mototow(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Оставить заявку на мотоэвакуацию", callback_data="urgent_request"))
    builder.row(types.InlineKeyboardButton(text="Позвонить менеджеру", callback_data="call_manager"))
    builder.row(types.InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    keyboard = builder.as_markup()
    await bot.send_message(callback_query.from_user.id, "Как вам удобнее вызвать эвакуатор?", reply_markup=keyboard)

# Обработчик для варианта "Оставить заявку на мотоэвакуацию"
@dp.callback_query(F.data == "urgent_request")
async def process_urgent_request(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Отправляем reply-клавиатуру для запроса контакта
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await bot.send_message(
        callback_query.from_user.id,
        "Пожалуйста, отправьте ваш контакт вызова эвакуатора.",
        reply_markup=contact_keyboard
    )
    await state.set_state(UrgentRequestFSM.waiting_for_contact)

# Обработчик для получения контакта в заявке на мотоэвакуацию
@dp.message(UrgentRequestFSM.waiting_for_contact, F.content_type == ContentType.CONTACT)
async def process_urgent_contact(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number
    await state.update_data(contact=contact)
    await message.answer(
        "Принято. Какой мотоцикл везем?\nВведите марку и модель мотоцикла:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(UrgentRequestFSM.waiting_for_motorcycle)

# Обработчик для получения марки и модели мотоцикла
@dp.message(UrgentRequestFSM.waiting_for_motorcycle)
async def process_motorcycle(message: types.Message, state: FSMContext):
    motorcycle = message.text
    await state.update_data(motorcycle=motorcycle)
    await message.answer(f"Вы указали: {motorcycle}.\nОткуда забрать мотоцикл? Введите адрес отправки:")
    await state.set_state(UrgentRequestFSM.waiting_for_pickup)

# Обработчик для получения адреса отправки
@dp.message(UrgentRequestFSM.waiting_for_pickup)
async def process_pickup(message: types.Message, state: FSMContext):
    pickup_address = message.text
    await state.update_data(pickup_address=pickup_address)
    data = await state.get_data()
    motorcycle = data.get("motorcycle")
    await message.answer(
        f"\nАдрес отправки: {pickup_address}.\nКуда везем мотоцикл? Введите адрес доставки:"
    )
    await state.set_state(UrgentRequestFSM.waiting_for_delivery)

# Обработчик для получения адреса доставки
@dp.message(UrgentRequestFSM.waiting_for_delivery)
async def process_delivery(message: types.Message, state: FSMContext):
    delivery_address = message.text
    await state.update_data(delivery_address=delivery_address)
    data = await state.get_data()
    motorcycle = data.get("motorcycle")
    pickup_address = data.get("pickup_address")
    # Финальное сообщение пользователю
    await message.answer(
        f"Спасибо! Ваша заявка получена. Водитель свяжется с вами в ближайшее время.\n\n"
        f"Информация о доставке:\nМотоцикл: {motorcycle}\nАдрес отправки: {pickup_address}\nАдрес доставки: {delivery_address}"
    )
    # Отправляем уведомление сотруднику
    user_name = message.from_user.full_name
    contact = data.get("contact")
    notify_text = (
        f"Получена новая заявка на эвакуацию.\nПользователь: {user_name}\nТелефон: {contact}\n"
        f"Мотоцикл: {motorcycle}\nАдрес отправки: {pickup_address}\nАдрес доставки: {delivery_address}"
    )
    await bot.send_message(EMPLOYEE_CHAT_ID, notify_text)
    await state.clear()

# Обработчик для кнопки "Позвонить менеджеру"
@dp.callback_query(F.data == "call_manager")
async def call_manager(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    # Отправляем сообщение с HTML-ссылкой для звонка
    await bot.send_message(
        callback_query.from_user.id,
        'Номер телефона для вызова эвакуатора: <a href="tel:+79299585988">+79299585988</a>',
        parse_mode="HTML"
    )

# Обработчик для inline кнопки "Назад" (callback "back_to_main")
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.clear()
    await send_main_menu(callback_query.from_user.id)

# Объединённый обработчик для кнопки "Назад" (как для reply-клавиатуры, так и для текстовых сообщений)
@dp.message(F.text == "Назад")
async def back_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await message.answer("Возвращаем вас в главное меню.", reply_markup=ReplyKeyboardRemove())
    await send_main_menu(message.chat.id)

# Обработчик для кнопки "Заявка на обратный звонок"
@dp.callback_query(F.data == "callback_request")
async def process_callback_request(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Отправляем reply-клавиатуру для запроса контакта
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await bot.send_message(
        callback_query.from_user.id,
        "Оставьте ваш контакт для связи.",
        reply_markup=contact_keyboard
    )
    await state.set_state(CallbackRequestFSM.waiting_for_contact)

# Обработчик для получения контакта (для заявки на обратный звонок)
@dp.message(CallbackRequestFSM.waiting_for_contact, F.content_type == ContentType.CONTACT)
async def process_callback_contact(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number
    await state.update_data(contact=contact)
    await message.answer(
        "Что вас интересует? Напишите комментарий для менеджера, чтобы мы быстрее разобрались в вашем вопросе:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CallbackRequestFSM.waiting_for_comment)

# Обработчик для получения комментария (текстовое сообщение)
@dp.message(CallbackRequestFSM.waiting_for_comment)
async def process_callback_comment(message: types.Message, state: FSMContext):
    comment = message.text
    await state.update_data(comment=comment)
    data = await state.get_data()
    contact = data.get("contact")
    # Отправляем финальное сообщение пользователю
    await message.answer(
        f"Спасибо! Ваша заявка на обратный звонок принята!\nИнформация о заявке: {comment}",
        reply_markup=ReplyKeyboardRemove()
    )
    # Отправляем уведомление сотруднику в Телеграм
    user_name = message.from_user.full_name
    notify_text = (
        f"Новая заявка на обратный звонок.\n"
        f"Пользователь: {user_name}\n"
        f"Телефон: {contact}\n"
        f"Комментарий к заявке: {comment}"
    )
    await bot.send_message(EMPLOYEE_CHAT_ID, notify_text)
    await state.clear()

# Обработчик для кнопки "Маршрут для путешествия"
@dp.callback_query(F.data == "route")
async def process_route(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Устанавливаем состояние диалога с маршрутом
    await state.set_state(RouteFSM.in_dialog)
    # Исходное сообщение-промпт
    initial_prompt = (
        "Расскажите максимально подробно о своем маршруте: откуда и куда планируете поехать, даты поездки, модель мотоцикла. "
        "Укажите все детали, которые могут показаться вам важными при составлении маршрута."
    )
    response = await get_chatgpt_response(initial_prompt, state)
    # Inline-клавиатура для продолжения или завершения диалога
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Хочу уточнить детали", callback_data="continue_route"))
    builder.row(types.InlineKeyboardButton(text="Завершить составление маршрута", callback_data="finish_route"))
    keyboard = builder.as_markup()
    await bot.send_message(callback_query.from_user.id, response, reply_markup=keyboard)

# Обработчик для кнопки "Хочу уточнить детали"
@dp.callback_query(F.data == "continue_route")
async def continue_route(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, уточните детали вашего маршрута:")

# Обработчик для диалога с пользователем (в состоянии RouteFSM.in_dialog)
@dp.message(RouteFSM.in_dialog)
async def route_dialog(message: types.Message, state: FSMContext):
    user_input = message.text
    response = await get_chatgpt_response(user_input, state)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Хочу уточнить детали", callback_data="continue_route"))
    builder.row(types.InlineKeyboardButton(text="Завершить составление маршрута", callback_data="finish_route"))
    keyboard = builder.as_markup()
    await message.answer(response, reply_markup=keyboard)

# Обработчик для кнопки "Завершить составление маршрута"
@dp.callback_query(F.data == "finish_route")
async def finish_route(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Спасибо! Ваш маршрут составлен. Если понадобятся изменения, вы всегда можете уточнить детали.")
    await state.clear()

@dp.message(Command(commands=["commands"]))
async def get_commands(message: types.Message):
    cmds = await bot.get_my_commands()
    await message.answer(str(cmds))

@dp.message(F.content_type == ContentType.CONTACT)
async def process_contact(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == UrgentRequestFSM.waiting_for_contact.state:
        # Здесь можно реализовать дополнительную логику, если контакт получен в нужном состоянии
        pass
    else:
        await message.reply("Контакт не ожидается сейчас.")

# Обработчик неизвестных текстовых сообщений
@dp.message(F.content_type == ContentType.TEXT)
async def fallback_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
    await send_main_menu(message.chat.id)

async def main():
    global http_client, aclient

    try:
        logging.info("Запускаем бота")
        await dp.start_polling(bot)
    finally:
        await http_client.aclose()

if __name__ == '__main__':
    asyncio.run(main())