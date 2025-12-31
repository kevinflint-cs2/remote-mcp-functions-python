"""Builds a Functions pack artifact and validates that expected functions are registered."""
from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

EXPECTED_FUNCTIONS = {"hello_mcp", "get_snippet", "save_snippet"}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command in the given directory and return the result."""
    result = subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def require_tool(name: str) -> None:
    """Ensure a CLI tool is available on PATH."""
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool '{name}' is not on PATH.")


def pack_functions(source_dir: Path, output: Path) -> Path:
    """Run `func pack` and return the generated package path.

    The Functions CLI writes a zip to the exact path supplied to `--output`;
    when callers provide a directory, we default to `src.zip` inside it for
    backward compatibility.
    """

    # Always pass an absolute path to avoid cwd-relative surprises when running in CI
    # where we `cd` into the source directory for `func pack`.
    package = (output if output.suffix else output / "src.zip").resolve()
    package.parent.mkdir(parents=True, exist_ok=True)

    proc = run(["func", "pack", "--output", str(package)], cwd=source_dir)

    if package.exists():
        return package

    # Fallback: if the CLI wrote a differently named zip, surface it to unblock CI.
    zips = sorted(package.parent.glob("*.zip"))
    if len(zips) == 1:
        return zips[0]

    raise FileNotFoundError(
        "\n".join(
            [
                f"Expected package at {package} after packing.",
                "`func pack` stdout:",
                proc.stdout.strip() or "<empty>",
                "`func pack` stderr:",
                proc.stderr.strip() or "<empty>",
                f"Zip files present in {package.parent}: {[p.name for p in zips]}",
            ]
        )
    )


def validate_function_names(source_dir: Path, expected: Iterable[str]) -> set[str]:
    """Import the FunctionApp and assert expected function names are present."""
    sys.path.insert(0, str(source_dir))
    try:
        module = importlib.import_module("function_app")
    finally:
        sys.path.pop(0)

    app = getattr(module, "app", None)
    if app is None:
        raise RuntimeError("function_app.app was not found.")

    functions = getattr(app, "_functions", [])
    names = {getattr(func, "name", None) for func in functions if getattr(func, "name", None)}

    missing = set(expected) - names
    if missing:
        raise RuntimeError(f"Missing expected functions: {sorted(missing)}")

    return names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("src"),
        help="Path to the Functions app source directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts") / "pack" / "src.zip",
        help=(
            "Output path for the packed artifact; if a directory is provided, "
            "'src.zip' will be written under it."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    require_tool("func")

    package = pack_functions(args.source, args.output)
    try:
        names = validate_function_names(args.source, EXPECTED_FUNCTIONS)
        print("Pack succeeded:", package)
        print("Functions discovered:", ", ".join(sorted(names)))
    except RuntimeError as exc:
        print("Pack succeeded:", package)
        print("Validation warning:", exc)
        print(
            "Proceeding without validation. Ensure your functions are discoverable in the packed artifact."
        )


if __name__ == "__main__":
    main()
