# Codex App-Server Schema 0.159.0

Generated with:

```powershell
codex app-server generate-json-schema --out generated/codex-app-server/0.159.0
```

The combined `codex_app_server_protocol*.schemas.json` files are the primary
contract. Individual JSON files are the generator's split view for inspection.
This directory is pinned to the local `codex-cli 0.159.0` used for the
deployment verification; a CLI upgrade must regenerate and rerun the contract
tests.
