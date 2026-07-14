import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ai_chatbot"
        )

        if conn.is_connected():
            return conn

    except Error as e:
        print("Database Error:", e)

    return None


def _require_connection(conn):
    # FIX: almost every function below used to call conn.cursor()
    # without checking if get_connection() returned None (e.g. MySQL
    # not running, wrong credentials). That crashed with a confusing
    # "NoneType object has no attribute 'cursor'" instead of a clear
    # error - which is exactly what happens when a photo/video/document
    # upload tries to save_message() while the DB is unreachable.
    if conn is None:
        raise Exception("Database connection failed. Is MySQL running?")


# ------------user function---------------
def create_user(full_name, email, password_hash):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    query = """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (%s, %s, %s)
    """

    cursor.execute(query, (full_name, email, password_hash))
    conn.commit()

    cursor.close()
    conn.close()


def get_user_by_email(email):
    conn = get_connection()
    _require_connection(conn)

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

# ----------------conversation-------------
def create_conversation(user_id, title="New Chat"):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations(user_id, title)
        VALUES(%s,%s)
        """,
        (user_id, title)
    )

    conn.commit()

    conversation_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return conversation_id


def get_conversations(user_id):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=%s
        ORDER BY pinned DESC, created_at DESC
        """,
        (user_id,)
    )

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def rename_conversation(conversation_id, new_title):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET title=%s
        WHERE id=%s
        """,
        (new_title, conversation_id)
    )

    conn.commit()

    cursor.close()
    conn.close()


def delete_conversation(conversation_id):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    # Delete all messages first
    cursor.execute(
        "DELETE FROM messages WHERE conversation_id = %s",
        (conversation_id,)
    )

    # Delete the conversation
    cursor.execute(
        "DELETE FROM conversations WHERE id = %s",
        (conversation_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()


def search_conversations(user_id, keyword):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=%s
        AND title LIKE %s
        ORDER BY updated_at DESC
        """,
        (user_id, f"%{keyword}%")
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

# ----------------message--------------
def save_message(conversation_id, role, message):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (conversation_id, role, message)
        VALUES(%s,%s,%s)
        """,
        (conversation_id, role, message)
    )

    cursor.execute(
        """
        UPDATE conversations
        SET updated_at=NOW()
        WHERE id=%s
        """,
        (conversation_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()


def get_messages(conversation_id):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, role, message, created_at
        FROM messages
        WHERE conversation_id=%s
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return messages

# -----------dashboard--------------
def dashboard_stats(user_id):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor(dictionary=True)

    # Total Conversations
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM conversations
        WHERE user_id=%s
    """, (user_id,))
    total_conversations = cursor.fetchone()["total"]

    # Total Messages
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM messages
        WHERE conversation_id IN (
            SELECT id
            FROM conversations
            WHERE user_id=%s
        )
    """, (user_id,))
    total_messages = cursor.fetchone()["total"]

    # User Messages
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM messages
        WHERE role='user'
        AND conversation_id IN (
            SELECT id
            FROM conversations
            WHERE user_id=%s
        )
    """, (user_id,))
    user_messages = cursor.fetchone()["total"]

    # AI Messages
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM messages
        WHERE role='assistant'
        AND conversation_id IN (
            SELECT id
            FROM conversations
            WHERE user_id=%s
        )
    """, (user_id,))
    ai_messages = cursor.fetchone()["total"]

    # Total Words
    cursor.execute("""
        SELECT message
        FROM messages
        WHERE conversation_id IN (
            SELECT id
            FROM conversations
            WHERE user_id=%s
        )
    """, (user_id,))

    rows = cursor.fetchall()

    total_words = sum(
        len(row["message"].split())
        for row in rows
        if row["message"]
    )

    cursor.execute("""
        SELECT
            MIN(m.created_at) AS first_message,
            MAX(m.created_at) AS last_message
        FROM messages m
        JOIN conversations c
        ON m.conversation_id = c.id
        WHERE c.user_id = %s
    """, (user_id,))

    duration_row = cursor.fetchone()

    if (
        duration_row["first_message"] is not None
        and duration_row["last_message"] is not None
    ):
        duration = duration_row["last_message"] - duration_row["first_message"]

        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        conversation_duration = f"{hours}h {minutes}m {seconds}s"
    else:
        conversation_duration = "0h 0m 0s"

    cursor.close()
    conn.close()

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "user_messages": user_messages,
        "ai_messages": ai_messages,
        "total_words": total_words,
        "conversation_duration": conversation_duration
    }


def delete_all_conversations(user_id):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    # Delete all messages belonging to the user's conversations
    cursor.execute("""
        DELETE m
        FROM messages m
        JOIN conversations c
        ON m.conversation_id = c.id
        WHERE c.user_id = %s
    """, (user_id,))

    # Delete all conversations of the user
    cursor.execute("""
        DELETE FROM conversations
        WHERE user_id = %s
    """, (user_id,))

    conn.commit()

    cursor.close()
    conn.close()


def pin_conversation(conversation_id, pinned):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET pinned=%s
        WHERE id=%s
        """,
        (pinned, conversation_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def update_message(message_id, new_message):
    conn = get_connection()
    _require_connection(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE messages
        SET message = %s
        WHERE id = %s
        """,
        (new_message, message_id),
    )

    conn.commit()

    # FIX: cursor was never closed here (only conn.close() was called).
    cursor.close()
    conn.close()