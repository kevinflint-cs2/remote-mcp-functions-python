## Remote MCP Functions (Python)

Azure Functions (Python v2 decorator model) that exposes Model Context Protocol tools
for greeting, saving snippets into Azure Blob Storage, and retrieving them by name.
Poetry manages dependencies and Poe tasks orchestrate linting, typing, testing, and
packing.

> [!IMPORTANT]
> Always deploy the `src.zip` produced by `func pack` (or
> `scripts/pack_and_validate.py`), not a hand-made archive, so generated
> `function.json` files are present.

## Features

- MCP tool triggers for `hello_mcp`, `save_snippet`, and `get_snippet`
- Snippet persistence in blob storage under `snippets/{snippetname}.json`
- Strict typing, Ruff formatting/linting, and pytest coverage for edge cases
- Packaging guard script to ensure required functions are discoverable before deploy

## Architecture

| Component | Purpose |
| --- | --- |
| src/function_app.py | Declares the `FunctionApp`, MCP tool schemas, and imports functions for discovery |
| src/functions/hello_mcp.py | Returns a simple greeting |
| src/functions/save_snippet.py | Writes snippet content to blob storage via output binding |
| src/functions/get_snippet.py | Reads a snippet by name via input binding |
| scripts/pack_and_validate.py | Runs `func pack` and asserts all expected functions are registered |

## Prerequisites

- Python 3.11+ and Poetry installed
- Azure Functions Core Tools v4 on PATH (`func`)
- Azure Storage connection string for `AzureWebJobsStorage`
- Optional: Azurite for local storage emulation

## Quickstart

1. Install dependencies and tooling:

   ```bash
   poetry install
   ```

2. Activate the virtual environment (optional if you prefix commands with
   `poetry run`):

   ```bash
   poetry shell
   ```

3. Configure `AzureWebJobsStorage` in `src/local.settings.json` or your shell
   environment.

4. Start the Functions host from `src`:

   ```bash
   cd src
   func start
   ```

## MCP Tools

- `hello_mcp`: Returns a greeting string.
- `save_snippet`: Expects arguments `snippetname` and `snippet`; writes content to
  `snippets/{snippetname}.json`.
- `get_snippet`: Expects argument `snippetname`; returns stored snippet content.

Example payload for saving a snippet:

```json
{
  "arguments": {
    "snippetname": "example",
    "snippet": "print('hello')"
  }
}
```

> [!NOTE]
> The MCP trigger context is treated as a JSON string; invalid JSON returns an
> error message instead of writing to storage.

## Testing and Quality

- Format and lint: `poetry run poe lint`
- Type checking: `poetry run poe typecheck`
- Tests: `poetry run poe test`
- Full suite: `poetry run poe check`

## Packaging and Deployment

- Validate and build the pack artifact:

  ```bash
  python scripts/pack_and_validate.py --source src --output artifacts/pack
  ```

- Deploy the generated `artifacts/pack/src.zip` to Azure Functions (Flex
  Consumption or equivalent). After deploy, confirm functions with:

  ```bash
  az functionapp function list -n <app> -g <resource-group>
  ```

## Configuration

- Storage path: snippets are stored at `snippets/{snippetname}.json` in the default
  container.
- Logging: Application Insights sampling is enabled via `host.json`.
- Extension bundle: Uses `Microsoft.Azure.Functions.ExtensionBundle.Experimental`
  version `[4.*, 5.0.0)`.

> [!TIP]
> If local decoding errors occur when reading blobs, ensure stored content is
> UTF-8 encoded.
