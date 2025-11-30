import logging
import sys
import colorama  # <-- Import the library

# 1. Initialize Colorama!
# This must be called before any logging output to ensure the terminal is ready.
colorama.init()

# --- 2. Define Color Codes (Unchanged) ---
COLOR_CODES = {
    "RESET": colorama.Style.RESET_ALL,  # Use colorama constants
    "DEBUG": colorama.Fore.CYAN,
    "INFO": colorama.Fore.GREEN,
    "WARNING": colorama.Fore.YELLOW,
    "ERROR": colorama.Fore.RED,
    "CRITICAL": colorama.Style.BRIGHT + colorama.Fore.RED,  # Bold Red
}


# --- 3. Custom Color Formatter (Slightly simplified using colorama constants) ---
class ColorFormatter(logging.Formatter):
    """A custom formatter to add ANSI color codes."""

    def format(self, record):
        level_name = record.levelname
        color_code = COLOR_CODES.get(level_name, COLOR_CODES["RESET"])

        # Apply color only around the core log message, or the entire line.
        # Applying it to the entire line is usually cleaner:
        colored_format = color_code + self._fmt + COLOR_CODES["RESET"]

        # Temporarily set the colored format
        original_formatter = self._style._fmt
        self._style._fmt = colored_format

        output = super().format(record)

        # Reset the logger's format
        self._style._fmt = original_formatter

        return output


# --- 4. Define the Log Format ---
LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d | "  # Timestamp with milliseconds
    "%(levelname)s | "  # Severity Level
    "**%(filename)s:%(lineno)d** | "  # <-- UPDATED: Shows file and line number
    "%(message)s"
)


def get_app_logger(name: str = "__name__"):
    """Returns the configured logger instance."""
    # Using a common name like 'APP_LOGGER' instead of '__name__' can be clearer
    # and prevents the file name from being the logger's name.

    # We'll use the name 'APP_LOGGER' here, but the format prints the call site file.
    logger = logging.getLogger(name)

    # Check if handlers are already added to prevent duplicates on import/reload
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = ColorFormatter(fmt=LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger
