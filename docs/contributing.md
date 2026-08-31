# Contributing to Thanatos

Thank you for your interest in contributing to **Thanatos**! We welcome contributions from developers of all skill levels, including bug fixes, documentation improvements, new sub-agent skills, and performance optimizations.

---

## 📑 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [1. Reporting Bugs](#1-reporting-bugs)
  - [2. Suggesting Features](#2-suggesting-features)
  - [3. Submitting Pull Requests](#3-submitting-pull-requests)
- [Development Workflow](#development-workflow)
- [Coding Standards & Conventions](#coding-standards--conventions)
- [Adding New Sub-Agent Skills](#adding-new-sub-agent-skills)
- [Testing & Quality Assurance](#testing--quality-assurance)

---

## Code of Conduct

Thanatos is committed to providing a welcoming, inclusive, and harassment-free experience for everyone. Please be respectful, constructive, and collaborative in all discussions and pull requests.

---

## How to Contribute

### 1. Reporting Bugs
- Check existing GitHub Issues to see if the bug has already been reported.
- If not, open a new issue with a clear title and detailed reproduction steps, including:
  - Your OS version and Python version
  - The model used (e.g. `qwen2.5:7b`, `deepseek-r1:7b`)
  - Full traceback or server log output

### 2. Suggesting Features
- Open an issue describing the feature, rationale, and proposed implementation.
- Discuss with maintainers before undertaking major architectural changes.

### 3. Submitting Pull Requests
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-skill
   ```
2. Make your modifications following our [Coding Standards](#coding-standards--conventions).
3. Ensure all automated tests pass:
   ```bash
   pytest tests -v
   ```
4. Commit your changes with clear, semantic commit messages:
   ```bash
   git commit -m "feat(skills): add weather forecast agent skill"
   ```
5. Push to your fork and submit a Pull Request to `main`.

---

## Development Workflow

1. **Clone & Environment**:
   ```bash
   git clone https://github.com/<your-username>/Thanatos.git
   cd Thanatos
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Run the Backend Server**:
   ```bash
   uvicorn apps.api_server.main:app --reload
   ```
3. **Run the Flutter Client** (if modifying UI):
   ```bash
   cd apps/client_flutter
   flutter run
   ```

---

## Coding Standards & Conventions

- **Python Version**: Python 3.12+ (compatible with Python 3.14).
- **Type Annotations**: Mandatory type hints on all public functions, classes, and router endpoints.
- **Pydantic Models**: All data models must use Pydantic v2 conventions (`model_dump()`, `Field()`).
- **Async First**: Use asynchronous handlers (`async def`) for all I/O, API routes, and skill executions.
- **Shared Contracts**: Use models from `shared/models/` (`ToolCall`, `ToolResult`, `ToolDefinition`) rather than creating duplicate interfaces.
- **Logging**: Use Python's standard `logging.getLogger(__name__)` instead of `print()` statements.

---

## Adding New Sub-Agent Skills

To add a new skill to Thanatos:
1. Create a new directory in `plugins/system_skills/<skill_name>/`.
2. Implement your skill class inheriting from `BaseSkill` (`plugins/base/skill_interface.py`).
3. Define tool definitions using `ToolDefinition` with clear JSON Schema parameters.
4. Return `ToolResult.success_result()` or `ToolResult.error_result()`.
5. Register the skill in `plugins/base/registry.py` under `init_default_skills()`.
6. Add unit tests in `tests/unit/`.

Refer to the [Plugin Development Guide](./plugin_dev_guide.md) for full instructions.

---

## Testing & Quality Assurance

Before opening a PR, ensure all 48 tests pass cleanly:

```bash
# Run complete test suite
pytest tests -v

# Run with test coverage
pytest --cov=apps --cov=services --cov=plugins tests/
```

Thank you for helping make Thanatos better for everyone! 🚀
