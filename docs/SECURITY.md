# Security notes (API keys & config)

## Do not commit secrets

- Never commit real API keys (Google/Brave, etc.) into the repository.
- In this repo, `config.json` and `.env` are intentionally git-ignored.

## Recommended configuration

- Put secrets in environment variables (or a local `.env` file loaded by your runtime):
  - `GOOGLE_API_KEY`
  - `GOOGLE_CSE_ID`
  - `BRAVE_API_KEY`

- Keep `config.json` for non-secret defaults (e.g. `searxng.base_url`, `duckduckgo.region`) or for local-only setups.

## If a key was exposed

1. **Rotate the key immediately** in the provider console.
2. Audit usage/quota dashboards for suspicious activity.
3. Update local `.env` or deployment secrets.

## Placeholder strings

This project treats placeholder values like `YOUR_GOOGLE_API_KEY_HERE` as **unset** to avoid accidentally enabling engines with invalid credentials.
