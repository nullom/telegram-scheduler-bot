"""
Database module for Telegram Scheduler Bot.
Handles all SQLite operations for storing and retrieving messages.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os


class DatabaseManager:
    """Manages SQLite database operations for the Telegram bot."""

    def __init__(self, db_path: str):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create messages table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_type TEXT NOT NULL,
                        content TEXT,
                        file_id TEXT,
                        url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent_at TIMESTAMP NULL
                    )
                """
                )

                # Create index for faster queries
                cursor.execute(
                    (
                        "CREATE INDEX IF NOT EXISTS idx_created_at "
                        "ON messages(created_at)"
                    )
                )

                cursor.execute(
                    (
                        "CREATE INDEX IF NOT EXISTS idx_sent_at "
                        "ON messages(sent_at)"
                    )
                )

                conn.commit()
                self.logger.info("Database initialized successfully")

        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise

    def store_text_message(self, content: str) -> bool:
        """
        Store a text message in the database.

        Args:
            content: The text content to store

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, content) "
                        "VALUES (?, ?)"
                    ),
                    ("text", content),
                )
                conn.commit()
                self.logger.info(
                    (
                        "Text message stored successfully "
                        f"(ID: {cursor.lastrowid})"
                    )
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store text message: {e}")
            return False

    def store_url_message(self, url: str, original_text: str = None) -> bool:
        """
        Store a URL message in the database.

        Args:
            url: The URL to store
            original_text: Original text containing the URL (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, content, url) "
                        "VALUES (?, ?, ?)"
                    ),
                    ("url", original_text, url),
                )
                conn.commit()
                self.logger.info(
                    f"URL message stored successfully (ID: {cursor.lastrowid})"
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store URL message: {e}")
            return False

    def store_photo_message(self, file_id: str) -> bool:
        """
        Store a photo message in the database.

        Args:
            file_id: Telegram file ID for the photo

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, file_id) "
                        "VALUES (?, ?)"
                    ),
                    ("photo", file_id),
                )
                conn.commit()
                self.logger.info(
                    (
                        "Photo message stored successfully "
                        f"(ID: {cursor.lastrowid})"
                    )
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store photo message: {e}")
            return False

    def store_voice_message(self, file_id: str) -> bool:
        """
        Store a voice message in the database.

        Args:
            file_id: Telegram file ID for the voice message

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, file_id) "
                        "VALUES (?, ?)"
                    ),
                    ("voice", file_id),
                )
                conn.commit()
                self.logger.info(
                    (
                        "Voice message stored successfully "
                        f"(ID: {cursor.lastrowid})"
                    )
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store voice message: {e}")
            return False

    def store_audio_message(self, file_id: str) -> bool:
        """
        Store an audio message in the database.

        Args:
            file_id: Telegram file ID for the audio file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, file_id) "
                        "VALUES (?, ?)"
                    ),
                    ("audio", file_id),
                )
                conn.commit()
                self.logger.info(
                    (
                        "Audio message stored successfully "
                        f"(ID: {cursor.lastrowid})"
                    )
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store audio message: {e}")
            return False

    def store_document_message(
        self, file_id: str, file_name: str = None
    ) -> bool:
        """
        Store a document message in the database.

        Args:
            file_id: Telegram file ID for the document
            file_name: Original file name (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "INSERT INTO messages (message_type, file_id, "
                        "content) VALUES (?, ?, ?)"
                    ),
                    ("document", file_id, file_name),
                )
                conn.commit()
                self.logger.info(
                    (
                        "Document message stored successfully "
                        f"(ID: {cursor.lastrowid})"
                    )
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to store document message: {e}")
            return False

    def get_next_message(self) -> Optional[Dict]:
        """
        Get the next unsent message from the database (oldest first).

        Returns:
            dict: Message data or None if no messages available
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, message_type, content, file_id, url, created_at
                    FROM messages
                    WHERE sent_at IS NULL
                    ORDER BY created_at ASC
                    LIMIT 1
                """
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "message_type": row[1],
                        "content": row[2],
                        "file_id": row[3],
                        "url": row[4],
                        "created_at": row[5],
                    }

                return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get next message: {e}")
            return None

    def mark_message_sent(self, message_id: int) -> bool:
        """
        Mark a message as sent by updating its sent_at timestamp.

        Args:
            message_id: ID of the message to mark as sent

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "UPDATE messages SET sent_at = CURRENT_TIMESTAMP "
                        "WHERE id = ?"
                    ),
                    (message_id,),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Message {message_id} marked as sent")
                    return True
                else:
                    self.logger.warning(
                        f"Message {message_id} not found for marking as sent"
                    )
                    return False

        except sqlite3.Error as e:
            self.logger.error(
                f"Failed to mark message {message_id} as sent: {e}"
            )
            return False

    def delete_sent_message(self, message_id: int) -> bool:
        """
        Delete a sent message from the database.

        Args:
            message_id: ID of the message to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    (
                        "DELETE FROM messages WHERE id = ? "
                        "AND sent_at IS NOT NULL"
                    ),
                    (message_id,),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(
                        f"Message {message_id} deleted from database"
                    )
                    return True
                else:
                    self.logger.warning(
                        f"Message {message_id} not found or not sent yet"
                    )
                    return False

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete message {message_id}: {e}")
            return False

    def cleanup_old_messages(self, days: int) -> int:
        """
        Delete messages older than specified number of days.

        Args:
            days: Number of days to keep messages

        Returns:
            int: Number of messages deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM messages WHERE created_at < ?",
                    (cutoff_date.isoformat(),),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self.logger.info(
                        (
                            f"Cleaned up {deleted_count} old messages (older "
                            f"than {days} days)"
                        )
                    )
                else:
                    self.logger.info("No old messages found for cleanup")

                return deleted_count

        except sqlite3.Error as e:
            self.logger.error(f"Failed to cleanup old messages: {e}")
            return 0

    def get_message_stats(self) -> Tuple[int, int]:
        """
        Get count of total and unsent messages.

        Returns:
            tuple: (total_messages, unsent_messages)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get total count
                cursor.execute("SELECT COUNT(*) FROM messages")
                total_count = cursor.fetchone()[0]

                # Get unsent count
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE sent_at IS NULL"
                )
                unsent_count = cursor.fetchone()[0]

                return total_count, unsent_count

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get message counts: {e}")
            return 0, 0

    def get_database_size(self) -> str:
        """
        Get the size of the database file.

        Returns:
            str: Database size in human-readable format
        """
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)

                # Convert to human readable format
                for unit in ["B", "KB", "MB", "GB"]:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0

                return f"{size_bytes:.1f} TB"
            else:
                return "0 B"

        except Exception as e:
            self.logger.error(f"Failed to get database size: {e}")
            return "Unknown"
