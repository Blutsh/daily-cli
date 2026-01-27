"""Tests for the config module."""

from pathlib import Path

from daily.config import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_DAILIES_DIR,
    DAILY_FILE_FORMAT,
    SECTIONS,
    TAG_FORMAT,
    create_default_config,
    get_dailies_dir,
    load_config_file,
)


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_default_dailies_dir_is_path(self):
        """DEFAULT_DAILIES_DIR is a Path."""
        assert isinstance(DEFAULT_DAILIES_DIR, Path)

    def test_default_dailies_dir_location(self):
        """DEFAULT_DAILIES_DIR is in user's home."""
        assert ".daily" in str(DEFAULT_DAILIES_DIR)
        assert "dailies" in str(DEFAULT_DAILIES_DIR)

    def test_config_dir_location(self):
        """CONFIG_DIR is in ~/.daily."""
        assert str(CONFIG_DIR).endswith(".daily")

    def test_config_file_is_toml(self):
        """CONFIG_FILE is a TOML file."""
        assert str(CONFIG_FILE).endswith("config.toml")

    def test_daily_file_format(self):
        """File format includes date and md extension."""
        assert "%Y" in DAILY_FILE_FORMAT
        assert "%m" in DAILY_FILE_FORMAT
        assert "%d" in DAILY_FILE_FORMAT
        assert DAILY_FILE_FORMAT.endswith(".md")

    def test_sections_mapping(self):
        """SECTIONS has required commands."""
        assert "did" in SECTIONS
        assert "plan" in SECTIONS
        assert "block" in SECTIONS
        assert "meeting" in SECTIONS

    def test_sections_have_emoji_headers(self):
        """Sections have emoji headers."""
        assert "✅" in SECTIONS["did"]
        assert "▶️" in SECTIONS["plan"]
        assert "🚧" in SECTIONS["block"]
        assert "🗓" in SECTIONS["meeting"]

    def test_tag_format(self):
        """TAG_FORMAT has correct placeholder."""
        assert "{tags}" in TAG_FORMAT
        assert "#tags:" in TAG_FORMAT


class TestLoadConfigFile:
    """Tests for load_config_file."""

    def test_load_config_file_not_exists(self, tmp_path, monkeypatch):
        """Returns empty dict if file doesn't exist."""
        monkeypatch.setattr("daily.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        result = load_config_file()
        assert result == {}

    def test_load_config_file_valid(self, tmp_path, monkeypatch):
        """Loads valid TOML file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('dailies_dir = "/custom/path"')
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)

        result = load_config_file()
        assert result == {"dailies_dir": "/custom/path"}

    def test_load_config_file_invalid_toml(self, tmp_path, monkeypatch):
        """Returns empty dict if TOML is invalid."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("this is not { valid toml")
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)

        result = load_config_file()
        assert result == {}


class TestGetDailiesDir:
    """Tests for get_dailies_dir."""

    def test_get_dailies_dir_returns_path(self, tmp_path, monkeypatch):
        """Returns a Path."""
        monkeypatch.setattr("daily.config.DEFAULT_DAILIES_DIR", tmp_path / "dailies")
        monkeypatch.setattr("daily.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        monkeypatch.delenv("DAILY_DIR", raising=False)

        result = get_dailies_dir()
        assert isinstance(result, Path)

    def test_get_dailies_dir_creates_directory(self, tmp_path, monkeypatch):
        """Creates directory if it doesn't exist."""
        test_dir = tmp_path / "new_dailies"
        monkeypatch.setattr("daily.config.DEFAULT_DAILIES_DIR", test_dir)
        monkeypatch.setattr("daily.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        monkeypatch.delenv("DAILY_DIR", raising=False)

        result = get_dailies_dir()
        assert result.exists()
        assert result.is_dir()

    def test_env_var_has_priority(self, tmp_path, monkeypatch):
        """Environment variable has priority over everything."""
        env_dir = tmp_path / "env_dailies"
        config_file = tmp_path / "config.toml"
        config_file.write_text(f'dailies_dir = "{tmp_path / "config_dailies"}"')

        monkeypatch.setenv("DAILY_DIR", str(env_dir))
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)
        monkeypatch.setattr(
            "daily.config.DEFAULT_DAILIES_DIR", tmp_path / "default_dailies"
        )

        result = get_dailies_dir()
        assert result == env_dir

    def test_config_file_has_priority_over_default(self, tmp_path, monkeypatch):
        """Config file has priority over default."""
        config_dir = tmp_path / "config_dailies"
        config_file = tmp_path / "config.toml"
        config_file.write_text(f'dailies_dir = "{config_dir}"')

        monkeypatch.delenv("DAILY_DIR", raising=False)
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)
        monkeypatch.setattr(
            "daily.config.DEFAULT_DAILIES_DIR", tmp_path / "default_dailies"
        )

        result = get_dailies_dir()
        assert result == config_dir

    def test_default_used_when_no_config(self, tmp_path, monkeypatch):
        """Uses default when no env or config."""
        default_dir = tmp_path / "default_dailies"

        monkeypatch.delenv("DAILY_DIR", raising=False)
        monkeypatch.setattr("daily.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        monkeypatch.setattr("daily.config.DEFAULT_DAILIES_DIR", default_dir)

        result = get_dailies_dir()
        assert result == default_dir

    def test_config_expands_tilde(self, tmp_path, monkeypatch):
        """Expands ~ in config path."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('dailies_dir = "~/my_dailies"')

        monkeypatch.delenv("DAILY_DIR", raising=False)
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)

        result = get_dailies_dir()
        assert "~" not in str(result)
        assert "my_dailies" in str(result)


class TestCreateDefaultConfig:
    """Tests for create_default_config."""

    def test_creates_config_file(self, tmp_path, monkeypatch):
        """Creates config file."""
        config_dir = tmp_path / ".daily"
        config_file = config_dir / "config.toml"

        monkeypatch.setattr("daily.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)

        create_default_config()

        assert config_file.exists()
        content = config_file.read_text()
        assert "dailies_dir" in content

    def test_does_not_overwrite_existing(self, tmp_path, monkeypatch):
        """Doesn't overwrite existing file."""
        config_dir = tmp_path / ".daily"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text('dailies_dir = "/my/custom/path"')

        monkeypatch.setattr("daily.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("daily.config.CONFIG_FILE", config_file)

        create_default_config()

        content = config_file.read_text()
        assert "/my/custom/path" in content
