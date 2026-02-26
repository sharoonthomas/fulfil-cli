# Fulfil CLI

The Fulfil CLI (`fulfil`) — primary interface for humans and AI agents to interact with the Fulfil ERP platform.

## Install

```bash
uv tool install fulfil-cli
```

## Quick Start

```bash
# Authenticate
fulfil auth login

# List sales orders
fulfil sales_order list --where '{"state": "processing"}' --json

# Get a specific record
fulfil sales_order get 42 --fields id,reference,state

# List available models
fulfil models
```

See [AGENTS.md](AGENTS.md) for AI agent integration guide.
