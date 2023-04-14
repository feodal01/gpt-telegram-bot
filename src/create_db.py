import sqlite3
from pathlib import Path


def sqlite_connect():
    conn = sqlite3.connect("db/database.db", check_same_thread=False)
    conn.execute("pragma journal_mode=wal;")
    return conn


def init_sqlite():
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute('''pragma encoding=utf16;''')
    c.execute(
        '''CREATE TABLE context_table (id integer primary key, user_id integer, user_name text, role text, content text)''')
    c.execute(
        '''CREATE TABLE user_count (id integer primary key, user_id integer, user_name text, cnt_msg integer, subscription boolean)''')
    conn.commit()
    conn.close()
    return


if __name__ == '__main__':
    db = Path("db/database.db")

    try:
        db.resolve(strict=True)
    except FileNotFoundError:
        print("Database not found, trying to create a new one.")
        try:
            init_sqlite()
        except Exception as e:
            print("Error when creating database : ", e.__repr__(), e.args)
            pass
        else:
            print("Success.")
