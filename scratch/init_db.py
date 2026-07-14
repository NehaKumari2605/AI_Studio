import mysql.connector
from mysql.connector import Error

def init_db():
    try:
        # Connect to MySQL server without selecting a database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        if conn.is_connected():
            cursor = conn.cursor()
            print("Connected to MySQL server.")

            # Create Database
            cursor.execute("CREATE DATABASE IF NOT EXISTS ai_chatbot")
            print("Database 'ai_chatbot' ensured.")

            cursor.execute("USE ai_chatbot")

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) DEFAULT 'New Chat',
                    pinned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    conversation_id INT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
            """)

            print("Tables 'users', 'conversations', and 'messages' ensured.")
            cursor.close()
            conn.close()
            print("Database initialization complete.")
    except Error as e:
        print(f"Error while connecting or initializing MySQL: {e}")

if __name__ == "__main__":
    init_db()
