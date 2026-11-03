# OS Automation Microservice

## Overview
The `os_automation` microservice gives Thanatos controlled, audited agency over the host operating system, including GUI automation, application control, and process supervision.

## Key Modules
- `system_control.py`: High-level operating system controls (volume, power, application launching).
- `input_controller.py`: Mouse and keyboard simulation for desktop automation.
- `process_manager.py`: Host process monitoring, listing, and lifecycle management.
- `router.py`: Command routing and permission validation.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To test system control in a standalone session:
```bash
uv run python -c "from services.os_automation.system_control import SystemController; sc = SystemController(); print('OS automation ready')"
```
