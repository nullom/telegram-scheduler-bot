"""
Scheduler module for Telegram Scheduler Bot.
Handles scheduled message sending and cleanup operations using APScheduler.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.error import TelegramError
from database import DatabaseManager


class MessageScheduler:
    """Handles scheduled message sending and cleanup operations."""
    
    def __init__(self, bot: Bot, database: DatabaseManager, channel_id: int, 
                 scheduled_times: list, cleanup_days: int = 30):
        """
        Initialize the scheduler.
        
        Args:
            bot: Telegram Bot instance
            database: Database manager instance
            channel_id: Telegram channel ID for sending messages
            scheduled_times: List of times in HH:MM format for sending messages
            cleanup_days: Number of days to keep old messages
        """
        self.bot = bot
        self.database = database
        self.channel_id = channel_id
        self.scheduled_times = scheduled_times
        self.cleanup_days = cleanup_days
        self.logger = logging.getLogger(__name__)
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self) -> None:
        """Setup all scheduled jobs."""
        # Add message sending jobs for each scheduled time
        for time_str in self.scheduled_times:
            try:
                hour, minute = map(int, time_str.split(':'))
                job_id = f"send_message_{time_str.replace(':', '')}"
                
                self.scheduler.add_job(
                    self._send_scheduled_message,
                    CronTrigger(hour=hour, minute=minute),
                    id=job_id,
                    name=f"Send scheduled message at {time_str}",
                    replace_existing=True
                )
                
                self.logger.info(f"Added scheduled job for {time_str}")
                
            except ValueError as e:
                self.logger.error(f"Invalid time format '{time_str}': {e}")
        
        # Add daily cleanup job (run at 00:30)
        self.scheduler.add_job(
            self._cleanup_old_messages,
            CronTrigger(hour=0, minute=30),
            id="cleanup_old_messages",
            name="Daily cleanup of old messages",
            replace_existing=True
        )
        
        self.logger.info("Added daily cleanup job for 00:30")
    
    async def _send_scheduled_message(self) -> None:
        """Send one scheduled message to the channel."""
        try:
            # Get the next message to send
            message = self.database.get_next_message()
            
            if not message:
                self.logger.info("No messages available for scheduled sending")
                return
            
            message_id = message['id']
            message_type = message['message_type']
            
            # Send message based on type
            success = False
            
            if message_type == 'text':
                success = await self._send_text_message(message)
            elif message_type == 'url':
                success = await self._send_url_message(message)
            elif message_type == 'photo':
                success = await self._send_photo_message(message)
            elif message_type == 'voice':
                success = await self._send_voice_message(message)
            elif message_type == 'audio':
                success = await self._send_audio_message(message)
            elif message_type == 'document':
                success = await self._send_document_message(message)
            else:
                self.logger.error(f"Unknown message type: {message_type}")
                return
            
            if success:
                # Mark message as sent and then delete it
                self.database.mark_message_sent(message_id)
                self.database.delete_sent_message(message_id)
                self.logger.info(f"Successfully sent and removed {message_type} message (ID: {message_id})")
            else:
                self.logger.error(f"Failed to send {message_type} message (ID: {message_id})")
                
        except Exception as e:
            self.logger.error(f"Error in scheduled message sending: {e}")
    
    async def _send_text_message(self, message: dict) -> bool:
        """Send a text message to the channel."""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message['content']
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send text message: {e}")
            return False
    
    async def _send_url_message(self, message: dict) -> bool:
        """Send a URL message to the channel."""
        try:
            # Send the URL with original context if available
            text = message['content'] if message['content'] else message['url']
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=text,
                disable_web_page_preview=False  # Allow link previews
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send URL message: {e}")
            return False
    
    async def _send_photo_message(self, message: dict) -> bool:
        """Send a photo message to the channel."""
        try:
            await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=message['file_id']
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send photo message: {e}")
            return False
    
    async def _send_voice_message(self, message: dict) -> bool:
        """Send a voice message to the channel."""
        try:
            await self.bot.send_voice(
                chat_id=self.channel_id,
                voice=message['file_id']
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send voice message: {e}")
            return False
    
    async def _send_audio_message(self, message: dict) -> bool:
        """Send an audio message to the channel."""
        try:
            await self.bot.send_audio(
                chat_id=self.channel_id,
                audio=message['file_id']
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send audio message: {e}")
            return False
    
    async def _send_document_message(self, message: dict) -> bool:
        """Send a document message to the channel."""
        try:
            await self.bot.send_document(
                chat_id=self.channel_id,
                document=message['file_id']
            )
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send document message: {e}")
            return False
    
    async def _cleanup_old_messages(self) -> None:
        """Clean up old messages from the database."""
        try:
            deleted_count = self.database.cleanup_old_messages(self.cleanup_days)
            
            if deleted_count > 0:
                self.logger.info(f"Cleanup completed: removed {deleted_count} old messages")
            else:
                self.logger.info("Cleanup completed: no old messages to remove")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def start(self) -> None:
        """Start the scheduler."""
        try:
            self.scheduler.start()
            self.logger.info("Scheduler started successfully")
            
            # Log scheduled jobs
            jobs = self.scheduler.get_jobs()
            self.logger.info(f"Active jobs: {len(jobs)}")
            for job in jobs:
                # Get next run time safely
                try:
                    next_run = self.scheduler.get_job(job.id).next_run_time
                    self.logger.info(f"  - {job.name}: next run at {next_run}")
                except:
                    self.logger.info(f"  - {job.name}: scheduled")
                
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown(wait=False)
            self.logger.info("Scheduler stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self.scheduler.running
    
    def get_job_info(self) -> dict:
        """Get detailed information about all scheduled jobs."""
        job_info = {
            "scheduler_running": self.is_running(),
            "total_jobs": 0,
            "sending_jobs": 0,
            "cleanup_jobs": 0,
            "next_message_send": None,
            "next_cleanup": None,
            "scheduled_times": self.scheduled_times,
            "cleanup_days": self.cleanup_days
        }
        
        try:
            jobs = self.scheduler.get_jobs()
            job_info["total_jobs"] = len(jobs)
            
            for job in jobs:
                if job.id.startswith("send_message_"):
                    job_info["sending_jobs"] += 1
                elif job.id == "cleanup_old_messages":
                    job_info["cleanup_jobs"] += 1
            
            # Calculate next run times manually
            if self.is_running():
                now = datetime.now()
                
                # Find next message send time
                earliest_send = None
                for time_str in self.scheduled_times:
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        today_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        if today_time <= now:
                            # Move to tomorrow
                            today_time = today_time + timedelta(days=1)
                        
                        if earliest_send is None or today_time < earliest_send:
                            earliest_send = today_time
                    except:
                        pass
                
                job_info["next_message_send"] = earliest_send
                
                # Next cleanup is always tomorrow at 00:30
                tomorrow_cleanup = now.replace(hour=0, minute=30, second=0, microsecond=0)
                if tomorrow_cleanup <= now:
                    tomorrow_cleanup = tomorrow_cleanup + timedelta(days=1)
                job_info["next_cleanup"] = tomorrow_cleanup
                
        except Exception as e:
            self.logger.error(f"Error getting job info: {e}")
        
        return job_info
    
    async def send_immediate_test(self) -> bool:
        """Send a test message immediately (for testing purposes)."""
        try:
            test_message = "🤖 Test message from Telegram Scheduler Bot"
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=test_message
            )
            
            self.logger.info("Test message sent successfully")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send test message: {e}")
            return False
    
    def reschedule_jobs(self, new_times: list) -> bool:
        """Reschedule message sending jobs with new times."""
        try:
            # Remove existing sending jobs
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                if job.id.startswith("send_message_"):
                    self.scheduler.remove_job(job.id)
            
            # Update scheduled times
            self.scheduled_times = new_times
            
            # Add new jobs
            for time_str in self.scheduled_times:
                hour, minute = map(int, time_str.split(':'))
                job_id = f"send_message_{time_str.replace(':', '')}"
                
                self.scheduler.add_job(
                    self._send_scheduled_message,
                    CronTrigger(hour=hour, minute=minute),
                    id=job_id,
                    name=f"Send scheduled message at {time_str}",
                    replace_existing=True
                )
            
            self.logger.info(f"Rescheduled jobs for times: {new_times}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reschedule jobs: {e}")
            return False