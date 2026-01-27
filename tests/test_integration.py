"""End-to-end integration tests."""

from datetime import datetime, timedelta

import pytest
from typer.testing import CliRunner

from daily.cli import app
from daily.core import get_daily_file_path, read_daily_file, ensure_daily_file_exists

runner = CliRunner()


@pytest.fixture
def temp_dailies_dir(tmp_path, monkeypatch):
    """Fixture that configures a temporary directory for dailies."""
    dailies_dir = tmp_path / "dailies"
    dailies_dir.mkdir()
    monkeypatch.setenv("DAILY_DIR", str(dailies_dir))
    return dailies_dir


class TestEndToEndFlow:
    """End-to-end flow tests."""

    def test_complete_daily_workflow(self, temp_dailies_dir):
        """Complete flow: create file -> insert bullets -> cheat."""
        # 1. Start fresh - no file exists
        file_path = get_daily_file_path()
        assert not file_path.exists()

        # 2. Add work done yesterday
        result = runner.invoke(app, ["did", "Fixed production bug", "-t", "hotfix"])
        assert result.exit_code == 0
        assert file_path.exists()

        # 3. Add a meeting
        result = runner.invoke(app, ["meeting", "Incident review"])
        assert result.exit_code == 0

        # 4. Add plan for today
        result = runner.invoke(app, ["plan", "Deploy fix to staging", "-t", "hotfix"])
        assert result.exit_code == 0

        # 5. Add a blocker
        result = runner.invoke(app, ["block", "Waiting for QA approval"])
        assert result.exit_code == 0

        # 6. Generate cheat sheet (use --today since we just created today's file)
        result = runner.invoke(app, ["cheat", "--today"])
        assert result.exit_code == 0
        assert "Fixed production bug" in result.output
        assert "Incident review" in result.output
        assert "Deploy fix to staging" in result.output
        assert "Waiting for QA approval" in result.output

        # 7. Filter cheat by tag
        result = runner.invoke(app, ["cheat", "--today", "--tags", "hotfix"])
        assert result.exit_code == 0
        assert "Fixed production bug" in result.output
        assert "Deploy fix to staging" in result.output
        assert "Incident review" not in result.output

    def test_multiple_insertions_same_day(self, temp_dailies_dir):
        """Multiple insertions in the same day preserve all content."""
        # Add multiple items to each section
        for i in range(3):
            runner.invoke(app, ["did", f"Task {i+1}"])
            runner.invoke(app, ["plan", f"Plan {i+1}"])
            runner.invoke(app, ["meeting", f"Meeting {i+1}"])

        content = read_daily_file()

        # Verify all items are present
        for i in range(3):
            assert f"- Task {i+1}" in content
            assert f"- Plan {i+1}" in content
            assert f"- Meeting {i+1}" in content

    def test_consecutive_days_isolation(self, temp_dailies_dir):
        """Different days don't overwrite each other."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # Create entry for yesterday
        from daily.core import insert_bullet
        insert_bullet("did", "Yesterday's work", date=yesterday)

        # Create entry for today
        runner.invoke(app, ["did", "Today's work"])

        # Verify both files exist with correct content
        yesterday_content = read_daily_file(yesterday)
        today_content = read_daily_file(today)

        assert "Yesterday's work" in yesterday_content
        assert "Yesterday's work" not in today_content
        assert "Today's work" in today_content
        assert "Today's work" not in yesterday_content

    def test_tags_with_special_characters(self, temp_dailies_dir):
        """Tags with various characters work correctly."""
        test_cases = [
            ("Task 1", ["tag-with-dash"]),
            ("Task 2", ["tag_with_underscore"]),
            ("Task 3", ["CamelCase"]),
            ("Task 4", ["tag123"]),
            ("Task 5", ["TAG", "tag"]),  # Case sensitivity
        ]

        for text, tags in test_cases:
            result = runner.invoke(app, ["did", text, "--tags", ",".join(tags)])
            assert result.exit_code == 0

        content = read_daily_file()
        assert "tag-with-dash" in content
        assert "tag_with_underscore" in content
        assert "CamelCase" in content
        assert "tag123" in content

    def test_long_multiword_text(self, temp_dailies_dir):
        """Long multi-word text is handled correctly."""
        long_text = "This is a very long description of work that spans multiple words and includes details about the implementation of a complex feature"

        result = runner.invoke(app, ["did", long_text])
        assert result.exit_code == 0

        content = read_daily_file()
        assert long_text in content

        # Verify it appears in cheat (use --today --plain to avoid line wrapping)
        result = runner.invoke(app, ["cheat", "--today", "--plain"])
        assert long_text in result.output

    def test_text_with_special_characters(self, temp_dailies_dir):
        """Text with special characters is preserved."""
        special_texts = [
            "Fixed bug in user's profile",
            "Updated README.md file",
            "Added support for UTF-8: áéíóú",
            "Config: key=value pairs",
            "Array [1, 2, 3] handling",
        ]

        for text in special_texts:
            result = runner.invoke(app, ["did", text])
            assert result.exit_code == 0

        content = read_daily_file()
        for text in special_texts:
            assert text in content


class TestEdgeCases:
    """Edge case tests."""

    def test_directory_created_automatically(self, tmp_path, monkeypatch):
        """Dailies directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_dailies_dir"
        assert not new_dir.exists()

        monkeypatch.setenv("DAILY_DIR", str(new_dir))

        result = runner.invoke(app, ["did", "First entry"])
        assert result.exit_code == 0
        assert new_dir.exists()

    def test_empty_file_handling(self, temp_dailies_dir):
        """Handles manually created empty file."""
        file_path = get_daily_file_path()
        file_path.write_text("")

        # Should fail gracefully when reading
        result = runner.invoke(app, ["cheat"])
        # Empty file won't have sections, so it should show no entries
        assert "(no entries)" in result.output or result.exit_code != 0

    def test_corrupted_file_missing_sections(self, temp_dailies_dir):
        """Handles file with missing sections."""
        file_path = get_daily_file_path()
        file_path.write_text("---\ntype: daily\n---\n\nSome random content\n")

        # Try to insert - should handle gracefully
        result = runner.invoke(app, ["did", "New task"])
        # This will fail because section doesn't exist
        assert result.exit_code != 0 or "error" in result.output.lower()

    def test_file_with_extra_content(self, temp_dailies_dir):
        """Preserves extra content added manually."""
        # Create file with template
        ensure_daily_file_exists()
        content = read_daily_file()

        # Add manual content
        modified = content.replace(
            "## 🧠 Quick Notes",
            "## 🧠 Quick Notes\n\nManual note here\n"
        )
        file_path = get_daily_file_path()
        file_path.write_text(modified)

        # Insert via CLI
        runner.invoke(app, ["did", "CLI task"])

        # Verify manual content is preserved
        final_content = read_daily_file()
        assert "Manual note here" in final_content
        assert "CLI task" in final_content

    def test_future_date_allowed(self, temp_dailies_dir):
        """Future dates are allowed (for planning)."""
        from daily.core import insert_bullet

        future = datetime.now() + timedelta(days=7)
        insert_bullet("plan", "Future planning", date=future)

        content = read_daily_file(future)
        assert "Future planning" in content

    def test_very_old_date(self, temp_dailies_dir):
        """Old dates work correctly."""
        from daily.core import insert_bullet

        old_date = datetime(2020, 1, 1)
        insert_bullet("did", "Historical entry", date=old_date)

        content = read_daily_file(old_date)
        assert "Historical entry" in content
        assert "date: 2020-01-01" in content

    def test_rapid_successive_writes(self, temp_dailies_dir):
        """Handles rapid successive writes without data loss."""
        entries = [f"Entry {i}" for i in range(20)]

        for entry in entries:
            result = runner.invoke(app, ["did", entry])
            assert result.exit_code == 0

        content = read_daily_file()
        for entry in entries:
            assert f"- {entry}" in content

    def test_unicode_in_all_fields(self, temp_dailies_dir):
        """Unicode works in text and tags."""
        result = runner.invoke(app, [
            "did",
            "Implementé la función de búsqueda 🔍",
            "--tags", "español,日本語"
        ])
        assert result.exit_code == 0

        content = read_daily_file()
        assert "Implementé la función de búsqueda 🔍" in content
        assert "español" in content
        assert "日本語" in content


class TestErrorHandling:
    """Error handling tests."""

    def test_read_nonexistent_file_error(self, temp_dailies_dir):
        """Clear error when reading nonexistent file."""
        result = runner.invoke(app, ["cheat"])
        assert result.exit_code == 1
        assert "No entries from yesterday" in result.output

    def test_permission_denied_simulation(self, temp_dailies_dir, monkeypatch):
        """Handles permission errors gracefully."""
        import os

        # Create a read-only directory
        readonly_dir = temp_dailies_dir / "readonly"
        readonly_dir.mkdir()

        # This test is platform-dependent, skip if we can't set permissions
        try:
            os.chmod(readonly_dir, 0o444)
            monkeypatch.setenv("DAILY_DIR", str(readonly_dir))

            result = runner.invoke(app, ["did", "Test"])
            # Should fail with some error
            assert result.exit_code != 0 or "error" in result.output.lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)
