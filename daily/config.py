"""Configuration for daily."""

import os
import tomllib
from pathlib import Path

# Base configuration directory
CONFIG_DIR = Path.home() / ".daily"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Defaults
DEFAULT_DAILIES_DIR = CONFIG_DIR / "dailies"

# Daily file name format
DAILY_FILE_FORMAT = "%Y-%m-%d-daily.md"

# Command to Markdown section mapping
SECTIONS = {
    "did": "## ✅ Done",
    "plan": "## ▶️ To Do",
    "block": "## 🚧 Blockers",
    "meeting": "## 🗓 Meetings",
    "notes": "## 🧠 Quick Notes",
}

# Inline tags format
TAG_FORMAT = "#tags: {tags}"


def load_config_file() -> dict:
    """Load configuration from TOML file.

    Returns:
        Dictionary with configuration, or empty if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def get_dailies_dir() -> Path:
    """Get dailies directory with priority:

    1. DAILY_DIR environment variable
    2. Config file ~/.daily/config.toml
    3. Default ~/.daily/dailies

    Returns:
        Path to dailies directory (created if it doesn't exist).
    """
    # 1. Environment variable (highest priority)
    env_dir = os.environ.get("DAILY_DIR")
    if env_dir:
        dailies_dir = Path(env_dir)
    else:
        # 2. Config file
        config = load_config_file()
        config_dir = config.get("dailies_dir")
        if config_dir:
            dailies_dir = Path(config_dir).expanduser()
        else:
            # 3. Default
            dailies_dir = DEFAULT_DAILIES_DIR

    dailies_dir.mkdir(parents=True, exist_ok=True)
    return dailies_dir


def create_default_config() -> None:
    """Create config file with default values."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        default_config = f'''# daily configuration
# https://github.com/user/daily-cli

# Directory where daily notes are stored
# You can use ~ for user's home directory
dailies_dir = "{DEFAULT_DAILIES_DIR}"
'''
        CONFIG_FILE.write_text(default_config)
