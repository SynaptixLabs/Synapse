# _example Module

> **📘 Reference Implementation**  
> Copy this module to start new modules.

---

## Purpose

This is a template module demonstrating the standard structure and patterns.

**To use:** Copy entire `_example/` directory, rename, and customize.

```bash
cp -r backend/modules/_example backend/modules/{{your_module}}
```

---

## Structure

```
_example/
├── README.md           # This file (update for your module)
├── AGENTS.md           # Tier-3 rules
├── src/
│   ├── __init__.py     # Public exports
│   ├── models.py       # Data models
│   ├── services.py     # Business logic
│   ├── api.py          # API endpoints
│   └── cli.py          # CLI plugin
└── tests/
    ├── unit/           # Unit tests
    └── integration/    # Integration tests
```

---

## Provides

| Export | Description |
|--------|-------------|
| `ExampleModel` | Example data model |
| `ExampleService` | Example business logic |
| `example_router` | FastAPI router |
| `ExamplePlugin` | CLI plugin |

---

## Usage

```python
from modules._example import ExampleService

service = ExampleService()
result = await service.list_items()
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/example list` | List examples |
| `/example create --name X` | Create example |

---

## Dependencies

- `shared/config`
- `shared/db`

---

## Vibes

| Task | Vibes |
|------|-------|
| Extend this module | 5–10 V |
| Add new endpoint | 3–5 V |

---

*Reference implementation — do not deploy directly*
