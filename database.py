import sqlite3

DATABASE_NAME = "telegram_bot.db"

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats
        (chat_id INTEGER PRIMARY KEY)
    ''')
    conn.commit()
    conn.close()

def add_chat_id(chat_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO chats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Chat ID already exists
        pass
    finally:
        conn.close()

def get_all_chat_ids():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM chats")
    chat_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return chat_ids
