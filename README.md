# Password Manager

A command-line password manager that stores your passwords encrypted with AES.

## Features

- **AES encryption** — all passwords encrypted with `Fernet` (AES + HMAC)
- **Master password** — only one password to remember (never stored)
- **Strong key derivation** — PBKDF2-HMAC-SHA256 (600,000 iterations)
- **Random salt** — per vault, prevents rainbow table attacks
- **Hidden input** — passwords typed invisibly (`getpass`)
- **Safe** — wrong master password never destroys the vault
- **CLI with subcommands** — like `git` (`init`, `add`, `get`, `list`)
- **Cross-platform** — Windows, Linux, macOS
- **No internet** — fully offline, nothing leaves your machine

## ⚠️ Security notice

**This project is for learning.** It implements core cryptographic concepts
(AES, PBKDF2, salt) in a clean way, but it has not been audited.

**For real-world use**, prefer audited tools:
- [Bitwarden](https://bitwarden.com) (open-source, cloud sync)
- [KeePassXC](https://keepassxc.org) (open-source, offline)

**If you use this project for real passwords:**
- Back up `vault.enc` AND `vault.salt` together
- If you forget your master password, **there is no recovery**
- Never commit `vault.enc` or `vault.salt` to Git

## Requirements

- **Python 3.10+**
- **`cryptography`** library

## Setup

### 1. Install dependencies

```bash
pip install cryptography
```

### 2. (Optional) Set the vault folder

By default, the vault is stored in `~/Desktop/Password-Manager/`. To change:

```bash
# Windows CMD
set PASSWORD_MANAGER=D:\MyVault
python vault.py init

# Git Bash / Linux / macOS
export PASSWORD_MANAGER=~/MyVault
python vault.py init
```

### Project structure

```
password-manager/
├── vault.py              ← main code
├── README.md
├── LICENSE
├── .gitignore
├── vault.enc             ← encrypted data (NOT committed)
└── vault.salt            ← random salt (NOT committed)
```

## Usage

### Initialize a new vault

```bash
python vault.py init
```

Output:

```
Set master password: ********
Confirm master password: ********
✅ Vault created
```

- If a vault already exists, you'll be asked to **overwrite** (`y/n`)
- Master password is **never stored** anywhere
- `vault.salt` (16 random bytes) is created

### Add a password

```bash
python vault.py add github
```

Output:

```
Master password: ********
Username: your_username
Password: ********
✅ Saved
```

- `Username` is visible (not secret)
- `Password` is hidden (`getpass`)
- If the site already exists, it is **overwritten**

### Get a password

```bash
python vault.py get github
```

Output:

```
Master password: ********
your_username
test123
```

- Requires master password (every time)
- If site is not found: `github Not found.`
- If master password is wrong: `❌ Wrong master password!`

### List all sites

```bash
python vault.py list
```

Output:

```
Master password: ********
github: your_username
gmail: your_username@gmail.com
twitter: your_username_dev
```

- Passwords are **not shown**, only sites + usernames

### Show help

```bash
python vault.py --help
python vault.py init --help
python vault.py add --help
```

## CLI reference

| Command | Description |
| :--- | :--- |
| `python vault.py init` | Create a new vault (asks for master password twice) |
| `python vault.py add <site>` | Add or update a password for `<site>` |
| `python vault.py get <site>` | Show username + password for `<site>` |
| `python vault.py list` | List all sites (without passwords) |
| `python vault.py --help` | Show help |

## How it works

### Flow

```
Master password (user input)
      │
      ▼
[PBKDF2-HMAC-SHA256, 600,000 iterations, salt]
      │
      ▼
    Key (32 bytes → base64 = 44 chars)
      │
      ▼
[Fernet — AES-128-CBC + HMAC-SHA256]
      │
      ▼
vault.enc  (encrypted JSON)
      │
      ▼
{site: {username, password}, ...}  (after decryption)
```

### Key derivation

```python
def derive_key(master, salt):
    h = hashlib.pbkdf2_hmac(
        'sha256',
        master.encode(),
        salt,
        600_000,       # 600,000 iterations
        dklen=32,      # 32 bytes
    )
    return base64.urlsafe_b64encode(h)   # Fernet needs base64
```

- **600,000 iterations** — each attempt takes ~0.3s, slowing brute-force
- **salt** — 16 random bytes, unique per vault
- **32 bytes** — Fernet key = AES-128 key (16) + HMAC key (16)

### Encryption

```python
fernet = Fernet(key)
encrypted = fernet.encrypt(json.dumps(data).encode())
FILE.write_bytes(encrypted)
```

- **Fernet** = AES-128-CBC + HMAC-SHA256
- **HMAC** = detects tampering (`InvalidToken`)

### Why `None` for wrong password

`load_vault()` returns:
- `{}` — vault doesn't exist yet (first run)
- `None` — wrong master password
- `{...}` — successful decryption

**Why?** If we returned `{}` for wrong password, `cmd_add` would think the vault is empty and overwrite the existing vault — **destroying all saved passwords**.

## Security details

### ✅ What this project does right

| | |
|---|---|
| Master password never stored | Only the derived key is used, then discarded |
| Strong KDF | PBKDF2-HMAC-SHA256, 600,000 iterations |
| Random salt | `secrets.token_bytes(16)` per vault |
| Authenticated encryption | Fernet (AES + HMAC) |
| Hidden input | `getpass` for password entry |
| Safe failure | Wrong password → `None` → early return |

### ⚠️ What it does NOT do (limitations)

| | Why it matters |
|---|---|
| No cloud sync | Local only — you must copy the vault yourself |
| No 2FA | Only master password |
| No audit | Doesn't check for weak/reused passwords |
| No auto-lock | Key stays in memory during execution |
| No memory wiping | Python doesn't zero out strings |
| Fernet (AES-128) | AES-256 would be stronger |

### Threats mitigated

- **Database leak** — `vault.enc` alone is useless without master password
- **Rainbow tables** — salt makes precomputed hashes useless
- **Brute-force** — 600k iterations makes guessing slow
- **Tampering** — HMAC detects modified ciphertext

### Threats NOT mitigated

- **Keylogger** — if malware records your master password, no encryption helps
- **Weak master password** — `1234` is broken regardless of KDF
- **Forgotten password** — no recovery mechanism (by design)
- **Corrupted vault** — if `vault.enc` is damaged, passwords are lost (back up!)

## Common workflows

**"I need to create a new vault"**

```bash
python vault.py init
```

**"I want to save a new password"**

```bash
python vault.py add github
```

**"I forgot a password"**

```bash
python vault.py get github
```

**"What sites do I have saved?"**

```bash
python vault.py list
```

**"I want to update my GitHub password"**

```bash
python vault.py add github   # overwrites existing
```

**"I forgot my master password"**

⚠️ **There is no recovery.** The vault cannot be decrypted without the correct master password. This is by design — the security of the vault depends on it.

## Backup

To back up your vault, copy **both** files together:

```bash
# Windows CMD
copy "%USERPROFILE%\Desktop\Password-Manager\vault.enc" D:\Backup\
copy "%USERPROFILE%\Desktop\Password-Manager\vault.salt" D:\Backup\

# Git Bash / Linux / macOS
cp ~/Desktop/Password-Manager/vault.{enc,salt} /media/usb/backup/
```

**Without `vault.salt`, you cannot decrypt `vault.enc`.** Back them up together.

## Troubleshooting

| Error | Cause | Fix |
| :--- | :--- | :--- |
| `❌ Wrong master password!` | Typo or different password | Try again |
| `ModuleNotFoundError: cryptography` | Library not installed | `pip install cryptography` |
| `site Not found.` | Site not in vault | Check with `list` |
| `Vault already exists` | `init` on existing vault | Answer `y` to overwrite (⚠️ destroys data) |
| `JSONDecodeError` | `vault.enc` corrupted | Restore from backup |

## Environment variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PASSWORD_MANAGER` | `~/Desktop/Password-Manager` | Folder for `vault.enc` and `vault.salt` |

## What NOT to do

❌ **Never commit `vault.enc` or `vault.salt` to Git** — anyone with the repo + your master password can decrypt.

❌ **Never share your master password** — it's the only thing protecting the vault.

❌ **Never use `input()` for passwords** — use `getpass` (this project does).

❌ **Never use `random` for salt** — use `secrets` (this project does).

❌ **Never skip the HMAC check** — `InvalidToken` matters.

## File permissions (advanced)

For extra safety, restrict permissions on the vault files:

```bash
# Linux / macOS
chmod 600 vault.enc vault.salt

# Windows (PowerShell, run as admin)
icacls vault.enc /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
icacls vault.salt /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
```

## License

MIT — see [LICENSE](LICENSE).