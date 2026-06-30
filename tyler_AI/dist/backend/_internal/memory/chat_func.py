

# chats = {} # после добавления БД не используется

# def create_chat(chat_id: str):
#     if chat_id not in chats:        #элемент безопасности
#         chats[chat_id] = {
#             "messages":[],
#             "summary":"",
#         }

# def add_message(chat_id: str, sender: str, text: str):
#     create_chat(chat_id)
#     chats[chat_id]["messages"].append({"sender": sender, "text": text})
   

# def get_messages(chat_id: str):
#     create_chat(chat_id)
#     return chats[chat_id]["messages"]
    

# def get_last_messages(chat_id: str, limit: int):
#     chat = chats.get(chat_id)
#     if not chat: return []
#     return chat["messages"][-limit:]
    

# def add_summary(chat_id: str, summary: str):
#     create_chat(chat_id)
#     chats[chat_id]["summary"] = summary
    

# def get_summary(chat_id: str):
#     create_chat(chat_id)
#     return chats[chat_id]["summary"]
    

# def get_col(chat_id: str)->int:
#     count = 0
#     for m in get_messages(chat_id): count+=1
#     return count
    
import sqlite3
from datetime import datetime

DB_NAME = "chat_memory.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        sender TEXT,
        text TEXT,
        created_at TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        chat_id TEXT PRIMARY KEY,
        summary TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        type TEXT,
        data TEXT,
        created_at TEXT,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_actions_chat_id
    ON actions(chat_id)
    """)

    conn.commit()
    conn.close()


def create_chat(chat_id: str, title: str = "New Chat"):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO chats (id, title, created_at)
    VALUES (?, ?, ?)
    """, (chat_id, title, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def get_chats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, title, created_at
    FROM chats
    ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]


def rename_chat(chat_id: str, title: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE chats SET title = ?
    WHERE id = ?
    """, (title, chat_id))

    conn.commit()
    conn.close()


def delete_chat(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cur.execute("DELETE FROM summaries WHERE chat_id = ?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id = ?", (chat_id,))

    conn.commit()
    conn.close()


def add_message(chat_id: str, sender: str, text: str):
    create_chat(chat_id)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO messages (chat_id, sender, text, created_at)
    VALUES (?, ?, ?, ?)
    """, (chat_id, sender, text, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def get_messages(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT sender, text
    FROM messages
    WHERE chat_id = ?
    ORDER BY id ASC
    """, (chat_id,))

    rows = cur.fetchall()
    conn.close()

    return [{"sender": s, "text": t} for s, t in rows]


def get_last_messages(chat_id: str, limit: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT sender, text
    FROM messages
    WHERE chat_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (chat_id, limit))

    rows = cur.fetchall()
    conn.close()

    rows.reverse()
    return [{"sender": s, "text": t} for s, t in rows]


def add_summary(chat_id: str, summary: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO summaries (chat_id, summary)
    VALUES (?, ?)
    ON CONFLICT(chat_id) DO UPDATE SET summary=excluded.summary
    """, (chat_id, summary))

    conn.commit()
    conn.close()


def get_summary(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT summary FROM summaries WHERE chat_id = ?
    """, (chat_id,))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else ""


def get_col(chat_id: str) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) FROM messages WHERE chat_id = ?
    """, (chat_id,))

    count = cur.fetchone()[0]
    conn.close()

    return count