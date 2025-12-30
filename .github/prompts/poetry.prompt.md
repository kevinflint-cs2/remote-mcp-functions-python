You are GitHub Copilot working in my repository.

IMPORTANT WORKFLOW RULE:
- You MUST NOT run any commands or modify files immediately.
- First, perform a read-only inspection (directory listing only).
- Then, produce a clear, step-by-step PLAN of the commands and file changes you intend to make.
- WAIT for my explicit approval (e.g., “Approved”, “Proceed”, or “Yes”) before running ANY commands or modifying files.
- Once approved, execute the plan exactly as written.

Initial inspection (read-only):
- Perform a directory listing to understand existing files and structure:
  - existing pyproject.toml
  - requirements.txt
  - .venv
  - src/ layout
  - existing tool configs
- Do NOT delete or modify anything during inspection.

Core rules:
- Code lives in ./src
- Poetry MUST always use a virtual environment
- Poetry virtualenv MUST be in-project at ./.venv
- If ./.venv exists, reuse it (do not recreate or delete)
- If requirements.txt exists, preserve its intent
- After ANY dependency change, ALWAYS update requirements.txt via Poetry export
- Python version: 3.12

Poetry initialization:
- If Poetry is not initialized, run `poetry init` in INTERACTIVE MODE only
- Never use non-interactive Poetry init
- If requirements.txt exists, import dependencies into Poetry on a best-effort basis after init

Dependencies / tooling:
- ruff (linting + formatting)
- mypy (type checking)
- pytest (testing)
- poe the poet (task runner)

Task runner (poe the poet):
- export:
  - poetry export -f requirements.txt --output requirements.txt --without-hashes
- lint:
  - ruff format src
  - ruff check src --fix
  - ruff check src
- typecheck:
  - mypy src
- test:
  - pytest
- check (combined task):
  - runs export, lint, typecheck, then test (in that order)

Configuration requirements:
- Configure Poetry to always use in-project virtualenvs (.venv)
- Add minimal, correct tool configuration in pyproject.toml:
  - ruff targeting src/
  - mypy targeting src/
  - pytest default discovery
- Define poe tasks under [tool.poe.tasks]

Deliverables:
PHASE 1 — PLAN (NO CHANGES):
- List the exact commands that will be run (in order)
- List the exact files that will be created or modified
- Show the full proposed pyproject.toml changes
- Show the exact requirements.txt export command
- WAIT for approval

PHASE 2 — EXECUTION (AFTER APPROVAL ONLY):
- Run the approved commands
- Apply the approved file change
