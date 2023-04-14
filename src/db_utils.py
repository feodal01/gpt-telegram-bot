import sqlite3

from gpt_utils import settings


def check_subscription(username, user_id):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_count WHERE user_id=? AND user_name=?;', (user_id, username))
    result = cursor.fetchall()

    if len(result) == 0:
        conn = sqlite3.connect('db/database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_count (user_id, user_name, cnt_msg, subscription) VALUES (?, ?, ?, ?)',
                       (user_id, username, 0, False))
        conn.commit()
        return True

    else:
        subscription = result[0][-1]
        cnt_msg = result[0][-2]
        if subscription or (cnt_msg <= settings['FREE_MESSAGES']):
            return True
        else:
            return False


def select_context(username, user_id):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('pragma encoding=UTF8')
    cursor.execute('SELECT * FROM context_table WHERE user_id=? AND user_name=?;', (user_id, username))
    return cursor.fetchall()


def count_user_msg(username, user_id):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_count WHERE user_id=? AND user_name=?;', (user_id, username))
    result = cursor.fetchall()
    if len(result) == 0:
        cnt_msg = 0
    else:
        cnt_msg = result[0][-2]

    cursor.execute('UPDATE user_count set cnt_msg = ?, subscription = ? WHERE user_id = ? AND user_name = ?',
                   (cnt_msg + 1, False, user_id, username, ))
    conn.commit()


def store_user_requests(username, user_id, role, content):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO context_table (user_id, user_name, role, content) VALUES (?, ?, ?, ?)',
                   (user_id, username, role, content))
    conn.commit()
