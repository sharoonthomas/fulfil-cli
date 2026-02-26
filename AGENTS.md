# Fulfil CLI — Agent Guide

## What is this?

The Fulfil CLI (`fulfil`) is a command-line interface for the Fulfil ERP platform. It communicates via JSON-RPC 2.0 with the Fulfil v3 API.

## Quick Start

```bash
# Install
uv tool install fulfil-cli

# Authenticate
fulfil auth login --workspace acme.fulfil.io --api-key sk_live_...

# Use
fulfil sales_order list --where '{"state": "processing"}' --json
fulfil sales_order get 42 --fields id,reference,state --json
fulfil models --json
```

## For AI Agents

- **Always use `--json`** for structured output (auto-enabled when stdout is not a TTY)
- **Env vars**: `FULFIL_API_KEY`, `FULFIL_WORKSPACE`, `FULFIL_JSON=1`
- **Exit codes**: 0=ok, 2=usage, 3=config, 4=auth, 5=not-found, 6=forbidden, 7=validation, 8=rate-limit, 9=server, 10=network
- **Error output** goes to stderr; data output goes to stdout
- **NDJSON streaming**: `fulfil sales_order list --all --json` outputs one record per line

## Command Reference

| Command | Description |
|---------|-------------|
| `fulfil <model> list` | List records with filters |
| `fulfil <model> get <ids>` | Get records by ID |
| `fulfil <model> create --data '{...}'` | Create records |
| `fulfil <model> update <ids> --data '{...}'` | Update records |
| `fulfil <model> delete <ids>` | Delete records |
| `fulfil <model> count --where '{...}'` | Count matching records |
| `fulfil <model> call <method>` | Call a custom model method |
| `fulfil <model> fields` | Describe model fields |
| `fulfil models` | List available models |
| `fulfil api '<json>'` | Raw JSON-RPC call |
| `fulfil auth login` | Authenticate |
| `fulfil auth status` | Check auth status |
| `fulfil auth workspaces` | List stored workspaces |
| `fulfil auth use <workspace>` | Switch active workspace |
| `fulfil whoami` | Show user/workspace info |
| `fulfil version` | Show CLI version |

## JSON-RPC Raw Call

```bash
fulfil api '{"method": "sales_order.find", "params": {"where": {"state": "draft"}, "fields": ["id", "reference"]}}'
```

## Project Structure

```
src/fulfil/
  cli/           # CLI commands (Typer + Click)
  client/        # JSON-RPC 2.0 HTTP client
  auth/          # API key resolution + keyring
  config/        # TOML config + XDG paths
  output/        # JSON/table formatting
```
