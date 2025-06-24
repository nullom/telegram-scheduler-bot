"""
Configuration module for Telegram Scheduler Bot.
Handles environment variables and application settings.
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the Telegram bot."""

    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration by loading environment variables.

        Args:
            env_file: Path to the environment file (default: .env)
        """
        self.logger = logging.getLogger(__name__)

        # Load environment variables from .env file
        if os.path.exists(env_file):
            load_dotenv(env_file)
            self.logger.info(f"Loaded configuration from {env_file}")
        else:
            self.logger.warning(
                (
                    f"Environment file {env_file} not found, "
                    "using system environment variables only"
                )
            )

        # Validate and load all configuration
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """Load all configuration values from environment variables."""

        # Telegram Bot Configuration
        self.bot_token = os.getenv("BOT_TOKEN")
        self.owner_id = self._get_int_env("OWNER_ID")
        self.channel_id = self._get_int_env("CHANNEL_ID")

        # Scheduling Configuration
        scheduled_times_str = os.getenv(
            "SCHEDULED_TIMES", "07:07,09:15,13:13,15:15,17:17,19:19,21:21"
        )
        self.scheduled_times = self._parse_scheduled_times(scheduled_times_str)

        # Database Configuration
        self.db_cleanup_days = self._get_int_env("DB_CLEANUP_DAYS", default=30)
        self.db_path = os.getenv("DB_PATH", "bot_storage.db")

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "bot.log")

        # Optional Configuration
        self.timezone = os.getenv("TIMEZONE", "UTC")
        self.max_retries = self._get_int_env("MAX_RETRIES", default=3)
        self.retry_delay = self._get_int_env("RETRY_DELAY", default=5)

    def _get_int_env(
        self, key: str, default: Optional[int] = None
    ) -> Optional[int]:
        """
        Get integer value from environment variable.

        Args:
            key: Environment variable key
            default: Default value if not found or invalid

        Returns:
            int: Parsed integer value or default
        """
        value = os.getenv(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            self.logger.warning(
                (
                    f"Invalid integer value for {key}: {value}, "
                    f"using default: {default}"
                )
            )
            return default

    def _parse_scheduled_times(self, times_str: str) -> List[str]:
        """
        Parse scheduled times from comma-separated string.

        Args:
            times_str: Comma-separated time strings in HH:MM format

        Returns:
            list: List of valid time strings
        """
        times = []
        for time_str in times_str.split(","):
            time_str = time_str.strip()
            if self._validate_time_format(time_str):
                times.append(time_str)
            else:
                self.logger.warning(
                    f"Invalid time format: {time_str}, skipping"
                )

        if not times:
            # Fallback to default times if none are valid
            default_times = [
                "07:07",
                "09:15",
                "13:13",
                "15:15",
                "17:17",
                "19:19",
                "21:21",
            ]
            self.logger.warning(
                (
                    "No valid scheduled times found, "
                    f"using defaults: {default_times}"
                )
            )
            return default_times

        return sorted(times)  # Sort times for better scheduling

    def _validate_time_format(self, time_str: str) -> bool:
        """
        Validate time format (HH:MM).

        Args:
            time_str: Time string to validate

        Returns:
            bool: True if valid, False otherwise"""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False

            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, IndexError):
            return False

    def _validate_config(self) -> None:
        """Validate critical configuration values."""
        errors = []

        # Validate required Telegram configuration
        if not self.bot_token:
            errors.append("BOT_TOKEN is required")
        elif not (
            self.bot_token
            and ":" in self.bot_token
            and len(self.bot_token.split(":")) == 2
        ):
            errors.append(
                (
                    "BOT_TOKEN appears to be invalid (should be in format: "
                    "XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)"
                )
            )

        if self.owner_id is None:
            errors.append("OWNER_ID is required")
        elif self.owner_id <= 0:
            errors.append("OWNER_ID must be a positive integer")

        if self.channel_id is None:
            errors.append("CHANNEL_ID is required")
        elif self.channel_id >= 0:
            errors.append(
                (
                    "CHANNEL_ID must be negative for channels "
                    "(should start with -100)"
                )
            )

        # Validate scheduling configuration
        if not self.scheduled_times:
            errors.append("At least one valid scheduled time is required")

        # Validate database configuration
        if self.db_cleanup_days <= 0:
            errors.append("DB_CLEANUP_DAYS must be positive")

        # Validate logging configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {valid_log_levels}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("Configuration validation successful")

    def get_log_level_numeric(self) -> int:
        """
        Get numeric log level for logging configuration.

        Returns:
            int: Numeric log level
        """
        return getattr(logging, self.log_level, logging.INFO)

    def is_development_mode(self) -> bool:
        """
        Check if running in development mode.

        Returns:
            bool: True if in development mode
        """
        return os.getenv("DEVELOPMENT", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    def get_summary(self) -> dict:
        """
        Get a summary of current configuration (sensitive data masked).

        Returns:
            dict: Configuration summary
        """
        return {
            "bot_token": (
                f"***{self.bot_token[-10:]}" if self.bot_token else None
            ),
            "owner_id": self.owner_id,
            "channel_id": self.channel_id,
            "scheduled_times": self.scheduled_times,
            "db_cleanup_days": self.db_cleanup_days,
            "db_path": self.db_path,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "timezone": self.timezone,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "development_mode": self.is_development_mode(),
        }

    def log_configuration(self) -> None:
        """Log current configuration summary."""
        summary = self.get_summary()
        self.logger.info("Current configuration:")
        for key, value in summary.items():
            self.logger.info(f"  {key}: {value}")

    @classmethod
    def create_default_env_file(cls, filepath: str = ".env") -> bool:
        """
        Create a default .env file with placeholder values.

        Args:
            filepath: Path where to create the .env file

        Returns:
            bool: True if file was created successfully
        """
        default_content = """# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_user_id_here
CHANNEL_ID=your_channel_id_here

# Scheduling Configuration (comma-separated HH:MM format)
SCHEDULED_TIMES=07:07,09:15,13:13,15:15,17:17,19:19,21:21

# Database Configuration
DB_CLEANUP_DAYS=30
DB_PATH=bot_storage.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Optional Configuration
TIMEZONE=UTC
MAX_RETRIES=3
RETRY_DELAY=5
DEVELOPMENT=false
"""

        try:
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(default_content)
                return True
            return False  # File already exists
        except Exception:
            return False
