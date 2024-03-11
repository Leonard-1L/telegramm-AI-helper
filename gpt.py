import requests
import logging
from transformers import AutoTokenizer
from config import MODEL_NAME, MAX_PROMT_TOKENS, GPT_LOCAL_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w"
)


def correct_len_tokens(text: str) -> bool:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return len(tokenizer.encode(text)) <= MAX_PROMT_TOKENS


def ask_gpt(user: dict) -> str:
    assistant_content = "Решим задачу: " + user['current_answer']
    temperature = 0.9
    max_tokens = 512

    response = requests.post(
        GPT_LOCAL_URL,
        headers={"Content-Type": "application/json"},
        json={
            "messages": [
                {"role": "user", "content": user["current_task"]},
                {"role": "system", "content": system_role(user) + system_level(user)},
                {"role": "assistant", "content": assistant_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )
    if response.status_code == 200:
        result = response.json()["choices"][0]["message"]["content"]
        logging.debug(f"Отправлено: {user['current_task']}\nПолучен результат: {result}")
        return result
    else:
        print("Не удалось получить ответ.")
        logging.error(f"Отправлено: {user['current_task']}\nПолучена ошибка: {response.json()}")


def system_role(user: dict) -> str:
    if user['current_subject'] == 'Программирование':
        role = "Ты лучший помощник по программированию. Твоя цель - помочь твоему собеседнику со всеми вопросами связанные с програмированием. Если тема разговора перестает быть про програмирование, то скажи, что тема уходит в другое русло, и ты не можешь продолжать из-за этого разговор. Отвечай на каждый вопрос понятно и без ошибок."
    else:
        role = "Ты лучший помощник по физике. Твоя цель - помочь твоему собеседнику со всеми вопросами связанные с физикой. Если тема разговора перестает быть про физику, то скажи, что тема уходит в другое русло, и ты не можешь продолжать из-за этого разговор. Отвечай на каждый вопрос понятно и без ошибок."
    return role


def system_level(user: dict) -> str:
    if user['current_level'] == 'Слабый':
        level = "Отвечай как для маленького ребенка, то-есть легко и понятно. Нельзя употреблять никаких терминов, лишь общепонятные слова. Если ответить не сможешь, то попроси повысить сложность ответа."
    elif user['current_level'] == 'Средний':
        level = "Отвечай как для школьника старших классов. Каждый сложный термин обьясняй. Задачу решай поэтапно."
    else:
        level = "Отвечай как для студента. Краткие, но понятные ответы должны быть в приоритете. Задау решай быстро и качественно."
    return level
