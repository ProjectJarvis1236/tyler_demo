import json
from datetime import datetime
from memory.chat_func import get_conn

import configs

def add_action(chat_id: str, action_type: str, params: dict, status: str = "success"):
    conn = get_conn()
    cur = conn.cursor()

    # 1. вставка нового действия
    cur.execute("""
        INSERT INTO actions (chat_id, type, data, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        chat_id,
        action_type,
        json.dumps({
            "params": params,
            "status": status
        }, ensure_ascii=False),
        datetime.utcnow().isoformat()
    ))

    # 2. чистка старых действий (оставляем только последние N)
    cur.execute("""
        DELETE FROM actions
        WHERE chat_id = ?
        AND id NOT IN (
            SELECT id FROM actions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
    """, (chat_id, chat_id, 2*configs.ACTIONS_LIMIT))

    conn.commit()
    conn.close()


def get_actions(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT type, data, created_at
    FROM actions
    WHERE chat_id = ?
    ORDER BY id ASC
    """, (chat_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "type": r[0],
            "data": json.loads(r[1]),
            "timestamp": r[2]
        }
        for r in rows
    ]


def get_last_actions(chat_id: str, limit: int = configs.ACTIONS_LIMIT):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT type, data, created_at
    FROM actions
    WHERE chat_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (chat_id, limit))

    rows = cur.fetchall()
    conn.close()

    rows.reverse()

    return [
        {
            "type": r[0],
            "data": json.loads(r[1])
            #"timestamp": r[2]
        }
        for r in rows
    ]