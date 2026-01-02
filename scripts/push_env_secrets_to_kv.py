import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from shutil import which
from typing import Any, Dict, List, Optional, Tuple


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env-style file into a dict of key/value pairs."""

    data: Dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Strip optional surrounding quotes so secrets are stored cleanly
        if (
            value
            and len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        data[key] = value
    return data


def secret_name_for_key(key: str) -> str:
    """Map env key to a valid Key Vault secret name."""

    known = {
        "ABUSEIPDB_API_KEY": "AbuseIpDbAPIKey",
    }
    if key in known:
        return known[key]

    sanitized = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in key)
    # Collapse consecutive dashes
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    sanitized = sanitized.strip("-")
    if not sanitized:
        raise SystemExit(f"Env key '{key}' cannot be converted to a valid secret name")
    return sanitized


def parse_rg_from_kv_id(kv_id: str) -> Optional[str]:
    """Extract resource group from a Key Vault resource ID."""
    parts = kv_id.split("/")
    # Expected format: /subscriptions/<sub>/resourceGroups/<rg>/providers/...
    if (
        len(parts) >= 5
        and parts[1] == "subscriptions"
        and parts[3].lower() == "resourcegroups"
    ):
        return parts[4]
    return None


def run_az(args: List[str], *, expect_json: bool = False) -> Tuple[int, Any]:
    """Run an az CLI command and optionally parse JSON output."""

    az_path = which("az")
    if not az_path:
        raise SystemExit(
            "Azure CLI 'az' not found on PATH. Please install or add to PATH."
        )

    proc = subprocess.run(
        [az_path, *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip()
        raise SystemExit(f"az command failed ({' '.join(args)}): {msg}")

    out = proc.stdout.strip()
    if expect_json:
        try:
            return proc.returncode, json.loads(out)
        except json.JSONDecodeError:
            raise SystemExit(f"Expected JSON output but got: {out}")
    return proc.returncode, out


def main() -> None:
    """Entry point to push secrets to Key Vault and wire Function App setting."""

    parser = argparse.ArgumentParser(
        description=(
            "Push secrets from an azd .env file into a Key Vault via az CLI."
        ),
    )
    parser.add_argument("--vault-name", required=True, help="Target Key Vault name")
    parser.add_argument(
        "--env-file",
        required=True,
        help=(
            "Path to the azd environment .env file "
            "(e.g., .azure/<env>.env)"
        ),
    )
    parser.add_argument(
        "--keys",
        help=(
            "Comma-separated list of keys to push; defaults to all keys "
            "in the file."
        ),
    )
    parser.add_argument(
        "--prefix",
        help=(
            "Optional prefix filter; only keys starting with this prefix are pushed."
        ),
    )
    parser.add_argument(
        "--function-app-name",
        help=(
            "Function App name to update app settings "
            "(falls back to AZURE_FUNCTION_NAME in env file)."
        ),
    )
    parser.add_argument(
        "--resource-group",
        help=(
            "Resource group for the Function App "
            "(falls back to KEY_VAULT_RESOURCE_ID parsed RG)."
        ),
    )
    parser.add_argument(
        "--app-setting-name",
        help=(
            "Override app setting key; defaults to the env key being pushed "
            "(e.g., ABUSEIPDB_API_KEY)."
        ),
    )
    args = parser.parse_args()

    env_path = Path(args.env_file).expanduser()
    if not env_path.is_file():
        raise SystemExit(f"Env file not found: {env_path}")

    env_values = parse_env_file(env_path)
    if not env_values:
        raise SystemExit("No key=value pairs found in env file")

    selected = env_values
    if args.prefix:
        selected = {k: v for k, v in selected.items() if k.startswith(args.prefix)}

    if args.keys:
        wanted = {k.strip() for k in args.keys.split(",") if k.strip()}
        selected = {k: v for k, v in selected.items() if k in wanted}

    if not selected:
        raise SystemExit("No keys selected for upload")

    # Determine defaults for function app and resource group
    fa_name = (
        args.function_app_name
        or env_values.get("AZURE_FUNCTION_NAME", "").strip('"')
    )
    kv_id = env_values.get("KEY_VAULT_RESOURCE_ID", "")
    rg_from_kv = parse_rg_from_kv_id(kv_id)
    rg_name = (
        args.resource_group or rg_from_kv or env_values.get("RESOURCE_GROUP_NAME", "")
    )

    for key, value in selected.items():
        secret_name = secret_name_for_key(key)

        # Set secret in Key Vault
        _, secret_obj = run_az(
            [
                "keyvault",
                "secret",
                "set",
                "--vault-name",
                args.vault_name,
                "--name",
                secret_name,
                "--value",
                value,
                "-o",
                "json",
            ],
            expect_json=True,
        )
        secret_uri = secret_obj.get("id") or secret_obj.get("kid")
        if not secret_uri:
            raise SystemExit("Secret set succeeded but no URI was returned.")

        print(
            f"Uploaded {key} as {secret_name} to Key Vault {args.vault_name}"
        )

        # Optionally set Function App setting to Key Vault reference
        if fa_name and rg_name:
            setting_name = args.app_setting_name or key
            kv_ref_value = f"@Microsoft.KeyVault(SecretUri={secret_uri})"

            # Use a temp file to avoid shell parsing issues with parentheses/equals
            with tempfile.NamedTemporaryFile(  # pragma: no cover - filesystem helper
                mode="w",
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(json.dumps({setting_name: kv_ref_value}))
                tmp_path = tmp.name

            try:
                run_az(
                    [
                        "functionapp",
                        "config",
                        "appsettings",
                        "set",
                        "--name",
                        fa_name,
                        "--resource-group",
                        rg_name,
                        "--settings",
                        f"@{tmp_path}",
                    ]
                )
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            # Validate the setting was applied
            _, settings_json = run_az(
                [
                    "functionapp",
                    "config",
                    "appsettings",
                    "list",
                    "--name",
                    fa_name,
                    "--resource-group",
                    rg_name,
                    "-o",
                    "json",
                ],
                expect_json=True,
            )
            found = next(
                (s for s in settings_json if s.get("name") == setting_name),
                None,
            )
            if not found or found.get("value") != kv_ref_value:
                raise SystemExit(
                    f"App setting {setting_name} was not set correctly on "
                    f"{fa_name} in {rg_name}."
                )
            print(
                f"Applied app setting {setting_name} -> Key Vault reference for "
                f"{fa_name} (RG: {rg_name})."
            )
        else:
            print(
                "Function App name or resource group not provided; "
                "skipped app setting update."
            )


if __name__ == "__main__":
    main()
