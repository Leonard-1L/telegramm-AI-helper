import sqlite3
from config import DB_NAME, DB_TABLE_USERS_NAME


def create_db():
    connection = sqlite3.connect(DB_NAME)
    connection.close()


def execute_query(query: str, data: tuple | None = None, db_name: str = DB_NAME):
    connection = None
    try:
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        if data:
            cursor.execute(query, data)
            connection.commit()
        else:
            cursor.execute(query)
        result = cursor.fetchall() if data else None
    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса: ", e)
        result = None
    finally:
        if connection:
            connection.close()
    return result


def create_table():
    sql_query = (
        f"CREATE TABLE IF NOT EXISTS {DB_TABLE_USERS_NAME} "
        f"(id INTEGER PRIMARY KEY, "
        f"user_id INTEGER, "
        f"subject TEXT, "
        f"level TEXT, "
        f"task TEXT, "
        f"answer TEXT);"
    )
    execute_query(sql_query)
    print("Таблица успешно создана")


def add_new_user(user_data: tuple):
    if not is_user_in_db(user_data[0]):
        colums = "(user_id, subject, level, task, answer)"
        sql_query = (
            f"INSERT INTO {DB_TABLE_USERS_NAME} "
            f"{colums} "
            f"VALUES (?, ?, ?, ?, ?);"
        )
        execute_query(sql_query, user_data)
        print("Польователь успешно добавлен")
    else:
        print("Пользователь уже существует!")


def is_user_in_db(user_id) -> bool:
    sql_query = (
        f"SELECT user_id "
        f"FROM {DB_TABLE_USERS_NAME} "
        f"WHERE user_id = ?;"
    )
    return bool(execute_query(sql_query, (user_id,)))


def update_row(user_id, coloumn_name, new_value):
    if is_user_in_db(user_id):
        sql_query = (
            f"UPDATE {DB_TABLE_USERS_NAME}"
            f"SET {coloumn_name} = ? "
            f"WHERE user_id = ?;"
        )
        execute_query(sql_query, (new_value, user_id))
    else:
        print("Пользователь не найден в базе")


def get_user_data(user_id):
    if is_user_in_db(user_id):
        sql_query = (
            f"SELECT * "
            f"FROM {DB_TABLE_USERS_NAME} "
            f"WHERE user_id = {user_id}"
        )
        row = execute_query(sql_query)[0]
        result = {
            "subject": row[2],
            "level": row[3],
            "task": row[4],
            "answer": row[5]
        }
        return result


def delete_user(user_id):
    if is_user_in_db(user_id):
        sql_query = (
            f"DELETE "
            f"FROM {DB_TABLE_USERS_NAME} "
            f"WHERE user_id = ?;"
        )
        execute_query(sql_query, (user_id,))

delete_user(2)