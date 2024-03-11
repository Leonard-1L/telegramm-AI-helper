import gpt
import logging
import telebot
from telebot.types import Message
from config import BOT_TOKEN, LOGS_PATH
from utils import *

bot = telebot.TeleBot(token=BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS_PATH,
    filemode="w"
)

help_message = (
    "Я бот-помощник. Сперва тебе надо выбрать тему и сложность общения. Всё выбирается с помощью команды /settings и изменить можно в любое время.\n"
    "Перед каждым вопросом нужно писать 'Задать вопрос ИИ'. Учитывайте, что памяти у нейросети нет, и все что вы напишите в следующем вопросе она забудет.\n"
    "Если нейросеть не смогла до конца написать ответ, то попроси её продолжить объснение.")

user_data = load_users_data()


def create_keyboard(buttons: list):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=["help"])
def help_func(message: Message):
    bot.send_message(message.from_user.id,
                     text=help_message,
                     reply_markup=create_keyboard([""]))


@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.username
    user_id = str(message.chat.id)

    if user_id not in user_data:
        user_data[user_id] = {
            "user_name": user_name,
            "current_subject": None,
            "current_level": None,
            "current_question": None,
            "current_answer": ''
        }
        save_data(user_data)

    bot.send_message(
        user_id,
        f"Привет, {user_name}! Я бот-помощник, попытаюсь ответить на все твои вопросы по теме физики или программирования.\n"
        "Мои ответы могут быть прописаны не полностью - в этом случае ты можешь написать 'продолжить'.\n"
        "Если у вас трудности - напишите команду /help.",
        reply_markup=create_keyboard(["Выбрать сложность/тему", "Задать вопрос ИИ"]),
    )


@bot.message_handler(func=lambda message: message.text in ["/settings", 'Выбрать сложность/тему'])
def open_settings(message: Message):
    bot.send_message(message.from_user.id,
                     "Выберите, что хотите изменить:",
                     reply_markup=create_keyboard(["Тема общения", "Сложность ответа"]))
    bot.register_next_step_handler(message, chouse_settings)


def chouse_settings(message: Message):
    if message.text == "Тема общения":
        bot.send_message(message.from_user.id,
                         "Выберите тему диалога из представленных ниже вариантов:",
                         reply_markup=create_keyboard(["Программирование", "Физика"]))
        bot.register_next_step_handler(message, change_settings)
    elif message.text == "Сложность ответа":
        bot.send_message(message.from_user.id,
                         "Выберите вид ответа от нейросети:",
                         reply_markup=create_keyboard(["Слабый", "Средний", "Сложный"]))
        bot.register_next_step_handler(message, change_settings)


def change_settings(message: Message):
    if message.text in ["Программирование", "Физика"]:
        user_data[str(message.from_user.id)]['current_subject'] = message.text
    elif message.text in ["Слабый", "Средний", "Сложный"]:
        user_data[str(message.from_user.id)]['current_level'] = message.text
    user_data[str(message.from_user.id)]['current_answer'] = ""
    save_data(user_data)
    bot.send_message(message.from_user.id,
                     text="Настройки успешно сохранены.",
                     reply_markup=create_keyboard(['Задать вопрос ИИ', "Выбрать сложность/тему"])
                     )


# Пользователь пока вводит только один вид из настроек. Сделай проверку на то, все ли виды настроек были скоректированы. Ну а дальше все как по маслу должно быть, сделать чтобы в system коректировался одновременно как и тема, так и сложность, в самом конце сделай реализацию бд. Так же настрой чтобы пользователь мог сразу выбрать настройки, а то начало забаганное.
@bot.message_handler(func=lambda message: message.text == "Задать вопрос ИИ")
def solve_task(message):
    if not user_data[str(message.chat.id)]['current_subject']:
        bot.send_message(message.chat.id,
                         "у вас не выбрана тема для общения. Перейдите в настройки и выберите её.",
                         reply_markup=create_keyboard(['Выбрать сложность/тему']))
        return
    if not user_data[str(message.from_user.id)]['current_level']:
        bot.send_message(message.chat.id,
                         "у вас не выбрана сложность ответа. Перейдите в настройки и выберите её.",
                         reply_markup=create_keyboard(['Выбрать сложность/тему']))
        return

    bot.send_message(message.chat.id, f"Выбрана тема: {user_data[str(message.chat.id)]['current_subject']}\n"
                                      f"Выбрана сложность: {user_data[str(message.from_user.id)]['current_level']}\n"
                                      "Напиши условие задачи:")
    bot.register_next_step_handler(message, give_answer)


def give_answer(message: Message):
    user_id = str(message.chat.id)
    if gpt.correct_len_tokens(message.text):
        bot.send_message(user_id, "Решаю...")
        user_data[user_id]['current_task'] = message.text
        logging.info(f"Получен запрос '{message.text}' от {message.from_user.username}")
        try:
            answer = gpt.ask_gpt(user_data[user_id])
        except Exception as E:
            bot.send_message(message.from_user.id,
                             "К сожалению у нас техническая неполадка. Просим повторить запрос или обраться к разработчику @Leoprofi",
                             reply_markup=create_keyboard(['Задать вопрос ИИ']))
            logging.error(f"Получена ошибка: {E}")
            return
        user_data[user_id]["current_answer"] = answer
        save_data(user_data)

        if answer is None:
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT. Попытайтесь отправить запрос заного.",
                reply_markup=create_keyboard(["Задать вопрос ИИ"]),
            )
            logging.error("ИИ не отвечает")

        elif answer == "":
            bot.send_message(
                user_id,
                "Обьяснение полностью закончено.",
                reply_markup=create_keyboard(["Задать вопрос ИИ"]),
            )
            logging.info(
                f"Отправлено: {message.text}\nПолучена ошибка: нейросеть вернула пустую строку"
            )

        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать вопрос ИИ", "Продолжить объяснение", "Выбрать сложность/тему"]
                ),
            )

    else:
        user_data[user_id]["current_task"] = None
        user_data[user_id]["current_answer"] = None
        save_data(user_data)

        bot.send_message(
            message.chat.id,
            "Запрос слишком длинный. Напишите более короткую задачу.",
        )
        logging.info(
            f"Отправлено: {message.text}\nТекст задачи слишком длинный, ответа нет."
        )


@bot.message_handler(
    func=lambda message: message.text.lower() in ["продолжить объяснение", "продолжи", "продолжить", "дальше",
                                                  "продолжай", "больше"])
def continue_explaining(message: Message):
    user_id = str(message.chat.id)

    if not user_data[user_id]["current_task"]:
        bot.send_message(
            user_id,
            "Для начала напиши условие задачи:",
            reply_markup=create_keyboard(["Задать вопрос ИИ"]),
        )

    else:
        bot.send_message(user_id, "Формулирую продолжение...")
        answer = gpt.ask_gpt(user_data[user_id])
        user_data[user_id]["current_answer"] += answer
        save_data(user_data)

        if answer is None:
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT.",
                reply_markup=create_keyboard(["Задать вопрос ИИ"]),
            )
        elif answer == "":
            bot.send_message(
                user_id,
                "Ответ полностью получен.",
                reply_markup=create_keyboard(["Задать вопрос ИИ"]),
            )
        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать вопрос ИИ", "Продолжить объяснение"]
                ),
            )


@bot.message_handler(commands=["debug"])
def debug(message):
    user_id = str(message.from_user.id)
    logging.info(f"{message.from_user.username} запросил логи")
    with open("log_file.txt", "rb") as f:
        bot.send_document(user_id, f)


@bot.message_handler()
def other_message(message: Message):
    bot.send_message(message.chat.id, "Выберите вариант предложенный на клавиатуре ниже")


if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling()
