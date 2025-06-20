"""
Telegram message handlers for the Scheduler Bot.
Handles incoming messages and stores them in the database.
"""

import logging
import re
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters
from database import DatabaseManager


class TelegramHandlers:
    """Handles all Telegram bot message processing."""
    
    def __init__(self, database: DatabaseManager, owner_id: int):
        """
        Initialize the handlers.
        
        Args:
            database: Database manager instance
            owner_id: Telegram user ID of the bot owner
        """
        self.database = database
        self.owner_id = owner_id
        self.logger = logging.getLogger(__name__)
        
        # URL detection regex pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
    
    def _is_owner(self, user_id: int) -> bool:
        """
        Check if the user is the bot owner.
        
        Args:
            user_id: Telegram user ID to check
            
        Returns:
            bool: True if user is the owner
        """
        return user_id == self.owner_id
    
    def _log_message_received(self, update: Update, message_type: str) -> None:
        """
        Log that a message was received from the owner.
        
        Args:
            update: Telegram update object
            message_type: Type of message received
        """
        # Safety check for update and user
        if not update or not update.effective_user:
            self.logger.warning("Received update without user information")
            return
            
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        self.logger.info(f"Received {message_type} message from owner (ID: {user_id}, Username: @{username})")
    
    def _extract_urls(self, text: str) -> list:
        """
        Extract URLs from text.
        
        Args:
            text: Text to search for URLs
            
        Returns:
            list: List of found URLs
        """
        return self.url_pattern.findall(text)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized access attempt from user {user_id}")
            await update.message.reply_text("Access denied. This bot is private.")
            return
        
        self.logger.info(f"Start command received from owner (ID: {user_id})")
        
        # Get database statistics
        total_messages, unsent_messages = self.database.get_message_stats()
        
        welcome_message = (
            f"Welcome! Telegram Scheduler Bot is running.\n\n"
            f"Total stored messages: {total_messages}\n"
            f"Unsent messages: {unsent_messages}\n\n"
            "Send me any message and I'll store it for scheduled delivery!"
        )
        
        await update.message.reply_text(welcome_message)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /status command - show bot status.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized status command from user {user_id}")
            await update.message.reply_text("Access denied. This bot is private.")
            return
        
        self.logger.info(f"Status command received from owner (ID: {user_id})")
        
        # Get database statistics
        total_messages, unsent_messages = self.database.get_message_stats()
        db_size = self.database.get_database_size()
        
        status_message = (
            f"Bot Status\n\n"
            f"Total messages: {total_messages}\n"
            f"Unsent messages: {unsent_messages}\n"
            f"Database size: {db_size}\n\n"
            f"Bot is running and ready to receive messages!"
        )
        
        await update.message.reply_text(status_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized help command from user {user_id}")
            await update.message.reply_text("Access denied. This bot is private.")
            return
        
        help_message = (
            "Telegram Scheduler Bot Help\n\n"
            "Commands:\n"
            "/start - Welcome message and status\n"
            "/status - Show bot status\n"
            "/help - Show this help message\n"
            "/stats - Show detailed statistics\n\n"
            "Supported message types:\n"
            "• Text messages (including URLs)\n"
            "• Photos\n"
            "• Voice messages\n"
            "• Audio files\n"
            "• Documents\n\n"
            "The bot will automatically store your messages and send them to the channel at scheduled times."
        )
        
        self.logger.info(f"Help command sent to owner (ID: {user_id})")
        await update.message.reply_text(help_message)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle text messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized text message from user {user_id}")
            return
        
        if not update.message.text:
            self.logger.warning("Received text handler call without text")
            return
        
        self._log_message_received(update, "text")
        
        text = update.message.text
        urls = self._extract_urls(text)
        # Store the text message
        if self.database.store_text_message(text):
            self.logger.info(f"Text message stored successfully: {text[:50]}...")
            if urls:
                self.logger.info(f"Found {len(urls)} URLs in text: {urls}")
            await update.message.reply_text("Message saved successfully!")
        else:
            self.logger.error(f"Failed to store text message: {text[:50]}...")
            await update.message.reply_text("Failed to save message. Please try again.")
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle photo messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized photo message from user {user_id}")
            return
        
        if not update.message.photo:
            self.logger.warning("Received photo handler call without photo")
            return
        
        self._log_message_received(update, "photo")
        
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        if self.database.store_photo_message(file_id):
            self.logger.info(f"Photo message stored successfully: {file_id}")
            await update.message.reply_text("📸 Photo saved successfully!")
        else:
            self.logger.error(f"Failed to store photo message: {file_id}")
            await update.message.reply_text("❌ Failed to save photo. Please try again.")
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle voice messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized voice message from user {user_id}")
            return
        
        if not update.message.voice:
            self.logger.warning("Received voice handler call without voice")
            return
        
        self._log_message_received(update, "voice")
        
        file_id = update.message.voice.file_id
        
        if self.database.store_voice_message(file_id):
            self.logger.info(f"Voice message stored successfully: {file_id}")
            await update.message.reply_text("🎤 Voice message saved successfully!")
        else:
            self.logger.error(f"Failed to store voice message: {file_id}")
            await update.message.reply_text("❌ Failed to save voice message. Please try again.")
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle audio messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized audio message from user {user_id}")
            return
        
        if not update.message.audio:
            self.logger.warning("Received audio handler call without audio")
            return
        
        self._log_message_received(update, "audio")
        
        file_id = update.message.audio.file_id
        
        if self.database.store_audio_message(file_id):
            self.logger.info(f"Audio message stored successfully: {file_id}")
            await update.message.reply_text("🎵 Audio file saved successfully!")
        else:
            self.logger.error(f"Failed to store audio message: {file_id}")
            await update.message.reply_text("❌ Failed to save audio file. Please try again.")
    
    async def handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle document messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized document message from user {user_id}")
            return
        
        if not update.message.document:
            self.logger.warning("Received document handler call without document")
            return
        
        self._log_message_received(update, "document")
        
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "Unknown"
        
        if self.database.store_document_message(file_id, file_name):
            self.logger.info(f"Document message stored successfully: {file_name} ({file_id})")
            await update.message.reply_text(f"📄 Document '{file_name}' saved successfully!")
        else:
            self.logger.error(f"Failed to store document message: {file_name} ({file_id})")
            await update.message.reply_text("❌ Failed to save document. Please try again.")
    
    async def handle_other_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle any other message types not specifically handled.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized message from user {user_id}")
            return
        
        self.logger.info(f"Unsupported message type received from owner (ID: {user_id})")
        await update.message.reply_text("❓ Sorry, this message type is not supported yet.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /stats command - show detailed statistics.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        # Safety check for update and user
        if not update or not update.effective_user or not update.message:
            self.logger.warning("Received update without user or message information")
            return
            
        user_id = update.effective_user.id
        
        if not self._is_owner(user_id):
            self.logger.warning(f"Unauthorized stats command from user {user_id}")
            await update.message.reply_text("Access denied. This bot is private.")
            return
        
        self.logger.info(f"Stats command received from owner (ID: {user_id})")
        
        # Get detailed database statistics
        total_messages, unsent_messages = self.database.get_message_stats()
        db_size = self.database.get_database_size()
        
        # Get message type breakdown if available
        stats_message = (
            f"📊 Detailed Statistics\n\n"
            f"📋 Message Status:\n"
            f"• Total messages: {total_messages}\n"
            f"• Unsent messages: {unsent_messages}\n"
            f"• Sent messages: {total_messages - unsent_messages}\n\n"
            f"💾 Database:\n"
            f"• Size: {db_size}\n\n"
            f"🔄 Bot Status: Active\n"
            f"⏰ Scheduler: Running"
        )
        
        await update.message.reply_text(stats_message)
        self.logger.info(f"Detailed stats sent to owner (ID: {user_id})")

    def get_handlers(self) -> list:
        """
        Get all message handlers for the bot.
        
        Returns:
            list: List of handler objects
        """
        return [
            # Command handlers
            CommandHandler("start", self.start_command),
            CommandHandler("status", self.status_command),
            CommandHandler("help", self.help_command),
            CommandHandler("stats", self.stats_command),
            
            # Message handlers (order matters - more specific first)
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message),
            MessageHandler(filters.PHOTO, self.handle_photo_message),
            MessageHandler(filters.VOICE, self.handle_voice_message),
            MessageHandler(filters.AUDIO, self.handle_audio_message),
            MessageHandler(filters.Document.ALL, self.handle_document_message),
            
            # Catch-all for other message types
            MessageHandler(filters.ALL, self.handle_other_messages),
        ]
