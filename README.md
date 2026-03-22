# Kronos (クロノス)
> a really cool password manager

![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

## Table of Contents

1. [What it is](#what-it-is)
2. [Features](#features)
3. [Security](#security)
4. [Installation](#installation)
5. [Running](#running)
6. [Web UI](#web-ui)
7. [Project Structure](#project-structure)
8. [Roadmap](#roadmap)
9. [Notes](#notes)

---

## What it is

Kronos is a locally-hosted password manager — fitted with various beautiful themes, special password generation, and thick encryption so *you* don't have to worry about breaches.

Your vault lives entirely on your machine as a single encrypted file (`vault.json`). No cloud. No accounts. No telemetry. The server is just a thin local API that handles crypto; the frontend is a static HTML/JS app that talks to it.

---

## Features

- **AES-256-GCM encryption** — authenticated, tamper-evident ciphertext
- **Argon2id key derivation** — memory-hard KDF resistant to brute-force
- **Six hand-crafted themes** — Brutalist Broadsheet, Terminal/Phosphor, Obsidian, Soft Clay, Constructivist, Risograph/Zine
- **Password generator** — cryptographically random, 20-character passwords
- **Password strength meter** — visual indicator on every credential
- **Search** — instant filtering across site names and usernames
- **Zero plaintext transmission** — master password never leaves your machine; the server only ever sees ciphertext
- **Auto-save** — vault is re-encrypted and written on every change

---

## Security

| Property | Detail |
|---|---|
| KDF | Argon2id — 64 MiB memory, 3 iterations, 4 threads |
| Cipher | AES-256-GCM (authenticated encryption) |
| Salt | 128-bit random, regenerated on every save |
| IV/Nonce | 96-bit random, regenerated on every save |
| Storage | Local only (`vault.json`) |
| Master password | Stays in browser memory; never sent to any external server |

Wrong password → `AESGCM.decrypt` raises `InvalidTag` → `null` returned. No timing oracle. No partial decryption.

---

## Installation

**Requirements:** Python 3.11+, pip

```bash
# Clone
git clone https://github.com/yourname/kronos.git
cd kronos

# Install Python dependencies
pip install -r backend/requirements.txt
```

The only non-stdlib dependencies are `argon2-cffi` (KDF), `cryptography` (AES-GCM), `fastapi`, `uvicorn`, and `pydantic`.

---

## Running

```bash
uvicorn backend.main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

On first launch there is no vault — just enter a passphrase of 8+ characters and Kronos will create one. On subsequent launches, the same passphrase decrypts it.

**Environment variables (optional):**

| Variable | Default | Description |
|---|---|---|
| `KRONOS_VAULT_FILE` | `vault.json` | Path to the encrypted vault file |
| `KRONOS_FRONTEND_DIR` | `frontend/` | Path to the frontend directory |

---

## Web UI

The UI is a single-page app split into a lock screen and a vault screen.

**Lock screen** — enter your master passphrase to decrypt and load the vault. If no `vault.json` exists yet, submitting a passphrase ≥ 8 characters creates a fresh one.

**Vault screen** — a two-panel layout with a searchable sidebar listing all entries and a detail panel showing the selected credential. From here you can:

- Add / edit / delete entries (site, URL, username, password, notes)
- Generate a strong random password
- Reveal or copy passwords
- View the password strength indicator
- Lock the vault (clears in-memory state)

**Settings / Themes** — navigate to `/settings.html` (or click *Change Theme* / *Theme* in any theme) to switch between the six visual styles. The chosen theme is stored in `localStorage` and persists across sessions.

### Themes

| Theme | Vibe |
|---|---|
| Brutalist Broadsheet | Aged newsprint · heavy serif  print column rules |
| Terminal / Phosphor | Green-on-black · CRT scanlines · monospace CLI |
| Obsidian | Near-black · hairline borders · no color |
| Soft Clay | Warm greige · rounded corners · tactile depth |
| Constructivist | Navy + crimson · diagonal stripes · Impact type |
| Risograph / Zine | Cream · two-ink overprint circles · indie print |

---

## Project Structure

```
kronos/
├── backend/
│   ├── main.py              # FastAPI app — /unlock, /save, static serving
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Redirects to active theme
│   ├── settings.html        # Theme picker
│   └── themes/
│       ├── kronos-core.js   # Shared vault logic (encrypt/decrypt, CRUD, keybinds)
│       ├── broadsheet.html
│       ├── terminal.html
│       ├── obsidian.html
│       ├── clay.html
│       ├── constructivist.html
│       └── risograph.html
├── password_manager.py      # Argon2id + AES-256-GCM crypto layer
├── vault.json               # Encrypted vault (created on first save; git-ignored)
└── README.md
```

`kronos-core.js` is the single source of truth for vault logic — all themes share it. Each theme HTML file is purely presentational: it wires up DOM elements to the core via a callback bridge passed to `KronosCore.init()`.

---

## Roadmap

| Feature | Priority | Notes |
|---------|----------|-------|
| TOTP / 2FA code generation | medium |  |
| Import from Bitwarden / 1Password / KeePass CSV | low |  |
| Export to encrypted JSON or CSV | low |  |
| Browser extension for autofill | high |  |
| Vault password change (re-encrypt in place) | high |  |
| Tags / folders for credential organisation | low |  |
| Breach check via HaveIBeenPwned k-anonymity API | medium |  |

---

## Notes

- The vault is re-encrypted with a fresh salt and IV on **every save**, so no two writes produce the same ciphertext even if the data is unchanged.
- Kronos does not support multiple vaults or multiple users. It is designed for single-user, local-only use.
- If you forget your master passphrase, the vault **cannot be recovered**. There is no reset mechanism by design.
- The `vault.json` in the repo is a demo file and is listed in `.gitignore` for your own vault — keep it that way.