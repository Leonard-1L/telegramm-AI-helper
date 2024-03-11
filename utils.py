import json

users_file = "Users_requests.json"


def load_users_data():
    try:
        with open(users_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def save_data(data):
    with open(users_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=3, ensure_ascii=False)
