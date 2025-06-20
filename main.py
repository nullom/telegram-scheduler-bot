"""
Main entry point for Telegram Scheduler Bot.
Combines all modules and starts the bot with scheduling functionality.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from telegram.ext import Application
from telegram import Bot
from telegram.error import TelegramError

from config import Config
from database import DatabaseManager
from handlers import TelegramHandlers
from scheduler import MessageScheduler


class TelegramSchedulerBot:
    """Main bot class that coordinates all components."""
    
    def __init__(self):
        """Initialize the bot with all components."""
        self.config = None
        self.database = None
        self.application = None
        self.bot = None
        self.handlers = None
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
          # File handler
        file_handler = logging.FileHandler(
            log_dir / (self.config.log_file if self.config else "bot.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(
            self.config.get_log_level_numeric() if self.config else logging.INFO
        )
        
        # Clear existing handlers and add new ones
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Reduce noise from external libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        
        self.logger.info("Logging configured successfully")
    
    async def initialize_components(self) -> None:
        """Initialize all bot components."""
        try:            # Load configuration
            self.config = Config()
            self.logger.info("Configuration loaded successfully")
            
            # Reconfigure logging with config values
            self.setup_logging()
              # Log configuration summary
            self.config.log_configuration()
            
            # Initialize database
            self.database = DatabaseManager(self.config.db_path)
            total_messages, unsent_messages = self.database.get_message_stats()
            self.logger.info(f"Database initialized: {total_messages} total messages, {unsent_messages} unsent")
            
            # Initialize Telegram application
            self.application = Application.builder().token(self.config.bot_token).build()
            self.bot = self.application.bot
            
            # Initialize bot and get info
            await self.application.initialize()
            await self.bot.initialize()
            
            bot_info = await self.bot.get_me()
            self.logger.info(f"Bot connected: @{bot_info.username} (ID: {bot_info.id})")
            
            # Initialize handlers
            self.handlers = TelegramHandlers(self.database, self.config.owner_id)
            
            # Add all handlers to application
            for handler in self.handlers.get_handlers():
                self.application.add_handler(handler)
            
            self.logger.info(f"Added {len(self.handlers.get_handlers())} message handlers")
            
            # Initialize scheduler
            self.scheduler = MessageScheduler(
                bot=self.bot,
                database=self.database,
                channel_id=self.config.channel_id,
                scheduled_times=self.config.scheduled_times,
                cleanup_days=self.config.db_cleanup_days
            )
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def start_bot(self) -> None:
        """Start the bot and scheduler."""
        try:
            # Start the scheduler
            self.scheduler.start()
            
            # Get scheduler info
            job_info = self.scheduler.get_job_info()
            self.logger.info(f"Scheduler started with {job_info['total_jobs']} jobs")
            self.logger.info(f"Next message send: {job_info['next_message_send']}")
            self.logger.info(f"Next cleanup: {job_info['next_cleanup']}")
            
            # Start the Telegram application
            await self.application.start()
            
            # Start polling for updates
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                bootstrap_retries=-1,  # Retry indefinitely
                drop_pending_updates=True
            )
            
            self.is_running = True
            self.logger.info("Bot started successfully and is polling for updates")
              # Send startup notification to owner
            try:
                startup_message = (
                    "🤖 Telegram Scheduler Bot Started!\n\n"
                    f"📊 Status:\n"
                    f"• Database: {self.database.get_message_stats()[1]} unsent messages\n"
                    f"• Scheduler: {job_info['sending_jobs']} sending jobs active\n"
                    f"• Next send: {job_info['next_message_send'].strftime('%H:%M') if job_info['next_message_send'] else 'No messages'}\n\n"
                    f"Ready to receive and schedule your messages!"
                )
                
                await self.bot.send_message(
                    chat_id=self.config.owner_id,
                    text=startup_message
                )
                self.logger.info("Startup notification sent to owner")
                
            except TelegramError as e:
                self.logger.warning(f"Could not send startup notification: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop_bot(self) -> None:
        """Stop the bot and scheduler gracefully."""
        self.logger.info("Stopping bot...")
        
        try:
            # Send shutdown notification to owner
            if self.bot and self.config:
                try:
                    shutdown_message = (
                        "🛑 Telegram Scheduler Bot Stopping...\n\n"
                        "The bot will be offline until restarted."
                    )
                    
                    await self.bot.send_message(
                        chat_id=self.config.owner_id,
                        text=shutdown_message
                    )
                    self.logger.info("Shutdown notification sent to owner")
                    
                except TelegramError as e:
                    self.logger.warning(f"Could not send shutdown notification: {e}")
            
            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop()
                self.logger.info("Scheduler stopped")
            
            # Stop Telegram application
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info("Telegram application stopped")
            
            # Stop bot
            if self.bot:
                await self.bot.shutdown()
                self.logger.info("Bot shutdown completed")
            
            self.is_running = False
            self.logger.info("Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            if self.is_running:
                # Create a new event loop for shutdown if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self.stop_bot())
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        self.logger.info("Signal handlers registered")
    
    async def run_forever(self) -> None:
        """Keep the bot running until stopped."""
        try:
            while self.is_running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("Bot execution cancelled")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            raise
    
    async def main(self) -> None:
        """Main bot execution method."""
        try:            # Setup basic logging first
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Setup initial logging configuration
            self.setup_logging()
            
            self.logger.info("=== Telegram Scheduler Bot Starting ===")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Initialize all components
            await self.initialize_components()
            
            # Start the bot
            await self.start_bot()
            
            # Run forever
            await self.run_forever()
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            # Ensure cleanup
            await self.stop_bot()


def main():
    """Entry point for the application."""
    bot = TelegramSchedulerBot()
    
    try:
        # Run the bot
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
