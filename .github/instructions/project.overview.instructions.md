---
description: 'Project overview and workflow guidance for remote-mcp-functions-python'
applyTo: '**'
---

# Project Overview

This repo hosts a Python Azure Functions app (Python v2 decorator model) that exposes MCP tools for snippet storage and a hello tool. It uses Poetry for dependency management and Poe tasks for common automation. Function metadata must be generated via `func pack` before deployment.

## Development Lifecycle

- Plan: Propose options; confirm the approach before coding when scope is unclear.
- Design: Break the chosen option into concrete, ordered steps; surface risks and testing impact.
- Implement: Write production-ready code without further approval steps once the plan is set.
- Test: Add/maintain unit tests under `src/tests`; prefer fast, deterministic tests.
- Check: Run lint/format/type checks; keep output clean before commits.
- Document: Update README, inline docs, and examples when behavior changes; add usage snippets when helpful.
- Commit: Use concise, descriptive messages; group related changes.

## Tooling and Commands

- Env: `poetry install` to create the venv; activate via `poetry shell` or `.venv/Scripts/Activate.ps1` on Windows.
- Aggregate checks: `poetry run poe check` (runs export → lint/format → typecheck → tests).
- Lint/format only: `poetry run poe lint` (ruff format + ruff check).
- Type checking: `poetry run poe typecheck` (mypy).
- Tests: `poetry run poe test` (pytest under `src`).
- Pack validation: `python scripts/pack_and_validate.py --source src --output artifacts/pack` (requires `func` Core Tools v4 on PATH). Ensures `src.zip` exists and functions are discovered.
- Package manually: `cd src && func pack --output ../deploy.zip` (creates `src.zip` inside output dir). Deploy the inner `src.zip`.

## Deployment Notes

- Primary workflow: use the packed artifact produced by `func pack` (or the validation script) for zip deploys to Azure Functions Flex Consumption. The deployed zip must include generated `.azurefunctions/*/function.json`.
- Do not hand-zip the repo; always rely on `func pack` to emit metadata.
- App settings like `FUNCTIONS_WORKER_RUNTIME` are managed by the plan; avoid overriding in Flex Consumption.
- Use `az functionapp function list -n <app> -g <rg>` post-deploy to confirm all functions (`hello_mcp`, `get_snippet`, `save_snippet`) are registered.

## Project Structure (key paths)

- `src/function_app.py`: Function app entrypoint; imports function modules for discovery.
- `src/functions/`: Individual function modules (`hello_mcp.py`, `get_snippet.py`, `save_snippet.py`).
- `src/tests/`: Unit tests.
- `scripts/pack_and_validate.py`: Guard script to pack and assert function discovery.
- `.github/workflows/ci.yml`: CI workflow running pack/validate on pushes/PRs.
- `infra/`: Bicep templates for the Function App and related Azure resources.
- `.azure/`: azd environment metadata.

## Coding Conventions

- Python: follow PEP 8; keep imports ordered (stdlib → third-party → local). Type hints required; triggers annotated as `str` for MCP tools to satisfy worker validation.
- Keep function modules importable so the Azure Functions indexer can load decorators (static imports in `function_app.py`).
- Avoid leaving generated/unpacked artifacts (`packed_local*`, `deploy_unzipped`) in `src/`; they break lint/typecheck.

## Working Agreements

- Prefer small, focused PRs; keep CI green before merge.
- When changing triggers/bindings, re-run `pack_and_validate.py` to ensure metadata generation still succeeds.
- Surface deployment-impacting changes (bindings, app settings) in the PR description and update any runbooks.
