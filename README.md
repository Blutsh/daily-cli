# daily

Minimalist CLI for engineers to log daily work. Perfect for daily standups.

## Features

- **Fast capture**: Log work in under 10 seconds
- **Markdown-based**: Human-readable files, Git-friendly
- **Tag support**: Filter entries by project or topic
- **Cheat sheet**: Quick summary for daily standups
- **No database**: Plain files in `~/.daily/dailies/`

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/user/daily-cli.git
cd daily-cli

# Install
uv sync

# Run
uv run daily --help
```

### Using pip

```bash
pip install daily-cli
```

### From source

```bash
git clone https://github.com/user/daily-cli.git
cd daily-cli
pip install -e .
```

## Quick Start

```bash
# Log completed work
daily did "Fixed CI/CD pipeline" --tags cicd,infra

# Plan today's work
daily plan "Review pending PRs" --tags code-review

# Log a blocker
daily block "Waiting for AWS access" --tags aws

# Log a meeting
daily meeting "Sprint planning" --tags team

# Show cheat sheet for standup
daily cheat
```

## Commands

| Command | Description | Section |
|---------|-------------|---------|
| `daily did "text"` | Log completed work | Yesterday |
| `daily plan "text"` | Plan work for today | Today |
| `daily block "text"` | Log a blocker | Blockers |
| `daily meeting "text"` | Log a meeting | Meetings |
| `daily cheat` | Show standup cheat sheet | - |

All commands support `--tags` or `-t` for tagging:

```bash
daily did "Deploy to production" --tags deploy,aws
daily did "Code review" -t review
```

## Cheat Sheet

The `daily cheat` command generates a clean summary for standups:

```
YESTERDAY
- Fixed CI/CD pipeline
- Deployed new feature

MEETINGS
- Sprint planning
- 1:1 with manager

TODAY
- Review pending PRs
- Write documentation

BLOCKERS
- Waiting for AWS access
```

Filter by tags:

```bash
daily cheat --tags aws
```

## File Structure

Daily notes are stored in `~/.daily/dailies/` with format `YYYY-MM-DD-daily.md`:

```markdown
---
type: daily
date: 2026-01-27
---

## ✅ Yesterday
- Fixed CI/CD pipeline #tags: cicd,infra

## ▶️ Today
- Review pending PRs

## 🚧 Blockers
- Waiting for AWS access #tags: aws

## 🗓 Meetings
- Sprint planning #tags: team

## 🧠 Quick Notes
```

## Configuration

### Custom directory

Set `DAILY_DIR` environment variable:

```bash
export DAILY_DIR=/path/to/my/dailies
```

Or create `~/.daily/config.toml`:

```toml
dailies_dir = "/path/to/my/dailies"
```

Priority: Environment variable > Config file > Default (`~/.daily/dailies`)

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=daily

# Format code
uv run black daily tests

# Lint
uv run ruff check daily tests

# Type check
uv run mypy daily
```

## FAQ

**Q: Where are my notes stored?**
A: In `~/.daily/dailies/` by default. Each day creates a new file like `2026-01-27-daily.md`.

**Q: Can I edit files manually?**
A: Yes! Files are plain Markdown. Manual edits are preserved.

**Q: Does it work with Obsidian?**
A: Yes! Point Obsidian to your dailies directory for a nice viewing experience.

**Q: Can I use it with Git?**
A: Absolutely. The files are designed to be Git-friendly.

**Q: What if I forget to log something?**
A: You can edit the Markdown file directly, or use the API with a specific date.

## License

MIT
