"""Tests for the core module."""

from datetime import datetime

import pytest

from daily.core import (
    ensure_daily_file_exists,
    generate_cheat,
    get_bullets_from_section,
    get_daily_file_path,
    get_filtered_bullets,
    insert_bullet,
    read_daily_file,
    write_daily_file,
)


@pytest.fixture
def temp_dailies_dir(tmp_path, monkeypatch):
    """Fixture that configures a temporary directory for dailies."""
    dailies_dir = tmp_path / "dailies"
    dailies_dir.mkdir()
    monkeypatch.setenv("DAILY_DIR", str(dailies_dir))
    return dailies_dir


class TestGetDailyFilePath:
    """Tests for get_daily_file_path."""

    def test_get_daily_file_path_with_date(self, temp_dailies_dir):
        """Generates correct path for a specific date."""
        date = datetime(2026, 1, 26)
        result = get_daily_file_path(date)

        assert result.name == "2026-01-26-daily.md"
        assert result.parent == temp_dailies_dir

    def test_get_daily_file_path_without_date(self, temp_dailies_dir):
        """Generates path for current date if not specified."""
        result = get_daily_file_path()
        today = datetime.now().strftime("%Y-%m-%d")

        assert result.name == f"{today}-daily.md"

    def test_get_daily_file_path_different_dates(self, temp_dailies_dir):
        """Generates different paths for different dates."""
        date1 = datetime(2026, 1, 26)
        date2 = datetime(2026, 1, 27)

        path1 = get_daily_file_path(date1)
        path2 = get_daily_file_path(date2)

        assert path1 != path2


class TestEnsureDailyFileExists:
    """Tests for ensure_daily_file_exists."""

    def test_ensure_daily_file_exists_creates_file(self, temp_dailies_dir):
        """Creates file with template if it doesn't exist."""
        date = datetime(2026, 1, 26)
        result = ensure_daily_file_exists(date)

        assert result.exists()
        content = result.read_text()
        assert "type: daily" in content
        assert "date: 2026-01-26" in content
        assert "## ✅ Yesterday" in content

    def test_ensure_daily_file_exists_idempotent(self, temp_dailies_dir):
        """Doesn't overwrite existing file."""
        date = datetime(2026, 1, 26)

        # Create initial file
        file_path = ensure_daily_file_exists(date)

        # Modify the file
        original_content = file_path.read_text()
        modified_content = original_content + "\n- Manually added task\n"
        file_path.write_text(modified_content)

        # Call again
        ensure_daily_file_exists(date)

        # Verify it wasn't overwritten
        assert file_path.read_text() == modified_content

    def test_ensure_daily_file_exists_returns_path(self, temp_dailies_dir):
        """Returns the file Path."""
        date = datetime(2026, 1, 26)
        result = ensure_daily_file_exists(date)

        assert result.name == "2026-01-26-daily.md"


class TestReadDailyFile:
    """Tests for read_daily_file."""

    def test_read_daily_file_existing(self, temp_dailies_dir):
        """Reads content of existing file."""
        date = datetime(2026, 1, 26)
        ensure_daily_file_exists(date)

        content = read_daily_file(date)

        assert "type: daily" in content
        assert "## ✅ Yesterday" in content

    def test_read_daily_file_not_found(self, temp_dailies_dir):
        """Raises error if file doesn't exist."""
        date = datetime(2026, 12, 31)

        with pytest.raises(FileNotFoundError, match="No daily file exists"):
            read_daily_file(date)


class TestWriteDailyFile:
    """Tests for write_daily_file."""

    def test_write_daily_file_creates(self, temp_dailies_dir):
        """Creates file with given content."""
        date = datetime(2026, 1, 26)
        content = "# Test content"

        result = write_daily_file(content, date)

        assert result.exists()
        assert result.read_text() == content

    def test_write_daily_file_overwrites(self, temp_dailies_dir):
        """Overwrites existing file."""
        date = datetime(2026, 1, 26)
        ensure_daily_file_exists(date)

        new_content = "# New content"
        result = write_daily_file(new_content, date)

        assert result.read_text() == new_content


class TestInsertBullet:
    """Tests for insert_bullet."""

    def test_insert_bullet_in_empty_section(self, temp_dailies_dir):
        """Inserts bullet in empty section."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Completed task", date=date)

        content = read_daily_file(date)
        assert "- Completed task" in content

    def test_insert_bullet_preserves_existing(self, temp_dailies_dir):
        """Doesn't delete previous content when inserting."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task 1", date=date)
        insert_bullet("did", "Task 2", date=date)

        content = read_daily_file(date)
        assert "- Task 1" in content
        assert "- Task 2" in content

    def test_insert_bullet_with_tags(self, temp_dailies_dir):
        """Inserts bullet with formatted tags."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Deploy", tags=["cicd", "aws"], date=date)

        content = read_daily_file(date)
        assert "- Deploy #tags: cicd,aws" in content

    def test_insert_bullet_different_sections(self, temp_dailies_dir):
        """Inserts in different sections correctly."""
        date = datetime(2026, 1, 26)

        insert_bullet("did", "Done task", date=date)
        insert_bullet("plan", "Planned task", date=date)
        insert_bullet("block", "Blocker", date=date)
        insert_bullet("meeting", "Meeting", date=date)

        content = read_daily_file(date)
        assert "- Done task" in content
        assert "- Planned task" in content
        assert "- Blocker" in content
        assert "- Meeting" in content

    def test_insert_bullet_invalid_section(self, temp_dailies_dir):
        """Raises error for invalid section."""
        date = datetime(2026, 1, 26)

        with pytest.raises(ValueError, match="Invalid section"):
            insert_bullet("invalid", "Task", date=date)

    def test_insert_bullet_creates_file_if_not_exists(self, temp_dailies_dir):
        """Creates file if it doesn't exist before inserting."""
        date = datetime(2026, 1, 26)
        file_path = get_daily_file_path(date)

        assert not file_path.exists()

        insert_bullet("did", "Task", date=date)

        assert file_path.exists()


class TestGetBulletsFromSection:
    """Tests for get_bullets_from_section."""

    def test_get_bullets_from_section(self, temp_dailies_dir):
        """Gets all bullets from a section."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task 1", date=date)
        insert_bullet("did", "Task 2", date=date)

        bullets = get_bullets_from_section("did", date)

        assert "Task 1" in bullets
        assert "Task 2" in bullets

    def test_get_bullets_from_empty_section(self, temp_dailies_dir):
        """Returns empty list for section without bullets."""
        date = datetime(2026, 1, 26)
        ensure_daily_file_exists(date)

        bullets = get_bullets_from_section("did", date)

        assert bullets == []

    def test_get_bullets_invalid_section(self, temp_dailies_dir):
        """Raises error for invalid section."""
        date = datetime(2026, 1, 26)
        ensure_daily_file_exists(date)

        with pytest.raises(ValueError, match="Invalid section"):
            get_bullets_from_section("invalid", date)


class TestGetFilteredBullets:
    """Tests for get_filtered_bullets."""

    def test_get_filtered_bullets(self, temp_dailies_dir):
        """Filters bullets by tags."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task 1", tags=["cicd"], date=date)
        insert_bullet("did", "Task 2", tags=["infra"], date=date)
        insert_bullet("did", "Task 3", tags=["cicd", "aws"], date=date)

        bullets = get_filtered_bullets("did", ["cicd"], date)

        assert len(bullets) == 2
        assert any("Task 1" in b for b in bullets)
        assert any("Task 3" in b for b in bullets)


class TestGenerateCheat:
    """Tests for generate_cheat."""

    def test_generate_cheat_basic(self, temp_dailies_dir):
        """Generates cheat sheet with all sections."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Deploy completed", date=date)
        insert_bullet("plan", "Review PR", date=date)
        insert_bullet("block", "Waiting for permissions", date=date)

        cheat = generate_cheat(date=date)

        assert "DONE" in cheat
        assert "TO DO" in cheat
        assert "BLOCKERS" in cheat
        assert "Deploy completed" in cheat
        assert "Review PR" in cheat
        assert "Waiting for permissions" in cheat

    def test_generate_cheat_no_markdown(self, temp_dailies_dir):
        """Output is plain text without Markdown."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task", date=date)

        cheat = generate_cheat(date=date)

        # Should not contain Markdown headers
        assert "##" not in cheat
        assert "✅" not in cheat
        assert "▶️" not in cheat
        assert "🚧" not in cheat

    def test_generate_cheat_removes_tags(self, temp_dailies_dir):
        """Doesn't show tags in output."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Deploy", tags=["cicd", "aws"], date=date)

        cheat = generate_cheat(date=date)

        assert "Deploy" in cheat
        assert "#tags:" not in cheat
        assert "cicd" not in cheat

    def test_generate_cheat_with_filter_tags(self, temp_dailies_dir):
        """Filters bullets by tags."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task cicd", tags=["cicd"], date=date)
        insert_bullet("did", "Task infra", tags=["infra"], date=date)
        insert_bullet("plan", "Plan cicd", tags=["cicd"], date=date)

        cheat = generate_cheat(filter_tags=["cicd"], date=date)

        assert "Task cicd" in cheat
        assert "Task infra" not in cheat
        assert "Plan cicd" in cheat

    def test_generate_cheat_empty_sections(self, temp_dailies_dir):
        """Handles empty sections."""
        date = datetime(2026, 1, 26)
        ensure_daily_file_exists(date)

        cheat = generate_cheat(date=date)

        assert "DONE" in cheat
        assert "TO DO" in cheat
        assert "BLOCKERS" in cheat
        assert "(no entries)" in cheat

    def test_generate_cheat_no_file(self, temp_dailies_dir):
        """Raises error if file doesn't exist."""
        date = datetime(2026, 12, 31)

        with pytest.raises(FileNotFoundError):
            generate_cheat(date=date)

    def test_generate_cheat_includes_meetings(self, temp_dailies_dir):
        """Includes Done, Meetings, To Do, Blockers (not Notes)."""
        date = datetime(2026, 1, 26)
        insert_bullet("did", "Task", date=date)
        insert_bullet("meeting", "Important meeting", date=date)
        insert_bullet("notes", "Quick note", date=date)

        cheat = generate_cheat(date=date)

        assert "DONE" in cheat
        assert "MEETINGS" in cheat
        assert "TO DO" in cheat
        assert "BLOCKERS" in cheat
        assert "Important meeting" in cheat
        # Quick notes are not included in cheat
        assert "Quick note" not in cheat
