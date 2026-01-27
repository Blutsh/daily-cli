"""Business logic for daily."""

from datetime import datetime
from pathlib import Path

from daily.config import DAILY_FILE_FORMAT, SECTIONS, get_dailies_dir
from daily.markdown import (
    create_daily_template,
    extract_bullets_from_section,
    filter_bullets_by_tags,
    format_bullet_with_tags,
    insert_at_section,
)


def get_daily_file_path(date: datetime | None = None) -> Path:
    """Get the daily file path for a date.

    Args:
        date: Date for the file. If None, uses current date.

    Returns:
        Path to the daily file.
    """
    if date is None:
        date = datetime.now()

    filename = date.strftime(DAILY_FILE_FORMAT)
    return get_dailies_dir() / filename


def ensure_daily_file_exists(date: datetime | None = None) -> Path:
    """Create daily file if it doesn't exist.

    If the file doesn't exist, creates it with the default template.
    If it exists, doesn't modify it.

    Args:
        date: Date for the file. If None, uses current date.

    Returns:
        Path to the daily file (existing or newly created).
    """
    if date is None:
        date = datetime.now()

    file_path = get_daily_file_path(date)

    if not file_path.exists():
        template = create_daily_template(date)
        file_path.write_text(template)

    return file_path


def read_daily_file(date: datetime | None = None) -> str:
    """Read daily file content.

    Args:
        date: Date for the file. If None, uses current date.

    Returns:
        File content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    file_path = get_daily_file_path(date)

    if not file_path.exists():
        raise FileNotFoundError(f"No daily file exists for {file_path.name}")

    return file_path.read_text()


def write_daily_file(content: str, date: datetime | None = None) -> Path:
    """Save content to the daily file.

    Args:
        content: Content to save.
        date: Date for the file. If None, uses current date.

    Returns:
        Path to the saved file.
    """
    file_path = get_daily_file_path(date)
    file_path.write_text(content)
    return file_path


def insert_bullet(
    section: str, text: str, tags: list[str] | None = None, date: datetime | None = None
) -> Path:
    """Insert a bullet in a section of the daily file.

    Creates the file if it doesn't exist. Inserts the bullet at the end
    of the specified section.

    Args:
        section: Section name ("did", "plan", "block", "meeting", "notes").
        text: Bullet text.
        tags: Optional list of tags.
        date: Date for the file. If None, uses current date.

    Returns:
        Path to the modified file.

    Raises:
        ValueError: If the section is not valid.
    """
    if section not in SECTIONS:
        valid_sections = ", ".join(SECTIONS.keys())
        raise ValueError(f"Invalid section '{section}'. Use: {valid_sections}")

    if date is None:
        date = datetime.now()

    # Ensure file exists
    ensure_daily_file_exists(date)

    # Read current content
    content = read_daily_file(date)

    # Format bullet with tags
    bullet = format_bullet_with_tags(text, tags)

    # Insert in section
    section_title = SECTIONS[section]
    new_content = insert_at_section(content, section_title, bullet)

    # Save
    return write_daily_file(new_content, date)


def get_bullets_from_section(
    section: str, date: datetime | None = None
) -> list[str]:
    """Get all bullets from a section.

    Args:
        section: Section name ("did", "plan", "block", "meeting", "notes").
        date: Date for the file. If None, uses current date.

    Returns:
        List of bullets (without the "- " prefix).

    Raises:
        ValueError: If the section is not valid.
        FileNotFoundError: If the file doesn't exist.
    """
    if section not in SECTIONS:
        valid_sections = ", ".join(SECTIONS.keys())
        raise ValueError(f"Invalid section '{section}'. Use: {valid_sections}")

    content = read_daily_file(date)
    section_title = SECTIONS[section]
    return extract_bullets_from_section(content, section_title)


def get_filtered_bullets(
    section: str, tags: list[str], date: datetime | None = None
) -> list[str]:
    """Get bullets from a section filtered by tags.

    Args:
        section: Section name.
        tags: List of tags to filter by.
        date: Date for the file. If None, uses current date.

    Returns:
        List of bullets that contain at least one of the tags.
    """
    bullets = get_bullets_from_section(section, date)
    return filter_bullets_by_tags(bullets, tags)


def generate_cheat(
    filter_tags: list[str] | None = None, date: datetime | None = None
) -> str:
    """Generate formatted cheat sheet for the daily standup.

    Generates a plain text summary (no Markdown) with Yesterday, Meetings,
    Today and Blockers sections for use in daily standup.

    Args:
        filter_tags: Optional list of tags to filter bullets.
        date: Date for the file. If None, uses current date.

    Returns:
        Formatted string with the cheat sheet.

    Raises:
        FileNotFoundError: If no daily file exists for the date.
    """
    data = generate_cheat_data(filter_tags, date)

    output_lines = []
    for section in data:
        output_lines.append(section["title"])
        if section["bullets"]:
            for bullet in section["bullets"]:
                output_lines.append(f"- {bullet}")
        else:
            output_lines.append("(no entries)")
        output_lines.append("")

    # Remove last empty line
    if output_lines and output_lines[-1] == "":
        output_lines.pop()

    return "\n".join(output_lines)


def generate_cheat_data(
    filter_tags: list[str] | None = None, date: datetime | None = None
) -> list[dict]:
    """Generate structured cheat sheet data for the daily standup.

    Args:
        filter_tags: Optional list of tags to filter bullets.
        date: Date for the file. If None, uses current date.

    Returns:
        List of dicts with 'title', 'key', and 'bullets' for each section.

    Raises:
        FileNotFoundError: If no daily file exists for the date.
    """
    content = read_daily_file(date)

    # Sections to include in the cheat sheet (relevant for daily standup)
    cheat_sections = [
        ("DONE", "did"),
        ("MEETINGS", "meeting"),
        ("TO DO", "plan"),
        ("BLOCKERS", "block"),
    ]

    result = []

    for title, section_key in cheat_sections:
        section_title = SECTIONS[section_key]
        bullets = extract_bullets_from_section(content, section_title)

        # Filter by tags if specified
        if filter_tags:
            bullets = filter_bullets_by_tags(bullets, filter_tags)

        result.append({
            "title": title,
            "key": section_key,
            "bullets": bullets,
        })

    return result
