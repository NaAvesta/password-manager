"""
Password Manager — store and retrieve passwords with AES encryption.

A command-line tool to store passwords locally, encrypted with Fernet
(AES-128 + HMAC). Protected by a master password that is never stored.

Usage:
    python vault.py init              Create a new vault
    python vault.py add <site>        Add or update a password
    python vault.py get <site>        Show username + password
    python vault.py list              List all saved sites

How it works:
    1. Master password → PBKDF2-HMAC-SHA256 (600,000 iterations) + salt → key
    2. Passwords stored in vault.enc (encrypted with Fernet)
    3. Salt stored in vault.salt (16 random bytes, not secret)

Security:
    - Master password is NEVER stored
    - Wrong password returns None (does not destroy vault)
    - Fernet = AES-128-CBC + HMAC-SHA256 (authenticated encryption)
    - Salt prevents rainbow table attacks

⚠️  For learning purposes only. For real passwords, use Bitwarden or KeePassXC.

Files:
    ~/Desktop/Password-Manager/vault.enc    ← encrypted data (NOT committed)
    ~/Desktop/Password-Manager/vault.salt   ← random salt (NOT committed)

Environment:
    PASSWORD_MANAGER — override default folder

See README.md for full documentation.
"""
import argparse
import base64
import getpass
import hashlib
import json
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

PATH = Path(os.getenv('PASSWORD_MANAGER', Path.home() / 'Desktop' / 'Password-Manager'))
PATH.mkdir(parents=True, exist_ok=True)
FILE = PATH / 'vault.enc'
SALT_FILE = PATH / 'vault.salt'

def load_vault(master: str) -> dict:
    if not FILE.exists() or not SALT_FILE.exists():
        return {}

    salt = SALT_FILE.read_bytes()
    key = derive_key(master, salt)
    fernet = Fernet(key)
    encrypted = FILE.read_bytes()
    try:
        decrypted = fernet.decrypt(encrypted)
    except InvalidToken:
        print('❌ Wrong master password!')
        return None
    return json.loads(decrypted)

def save_vault(master:  str, data: dict) -> None:
    salt = SALT_FILE.read_bytes()
    key = derive_key(master, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(json.dumps(data).encode())
    FILE.write_bytes(encrypted)

def cmd_add(site: str) -> None:
    master = getpass.getpass("Master password: ")
    vault = load_vault(master)
    if vault is None:
        return

    username = input('Username: ')
    password = getpass.getpass('Password: ')

    vault[site] = {
        'username': username,
        'password': password,
    }
    save_vault(master, vault)
    print("✅ Saved")

def cmd_get(site: str) -> None:
    master = getpass.getpass("Master password: ")
    vault = load_vault(master)
    if vault is None:
        return
    
    if site not in vault:
        print(f'{site} Not found.')
        return

    print(vault[site]['username'])
    print(vault[site]['password'])
    return

def cmd_list() -> None:
    master = getpass.getpass("Master password: ")
    vault = load_vault(master)
    if vault is None:
        return
    
    if not vault:
        print('No entries')
        return

    for site, data in vault.items():
        username = data['username']
        print(f'{site}: {username}')

    return

def cmd_init() -> None:
    if FILE.exists():
        overwrite = input("Vault already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Cancelled.")
            return
        
    master = getpass.getpass("Set master password: ")
    confirm = getpass.getpass("Confirm master password: ")

    if confirm != master:
        print("❌ Passwords don't match!")
        return

    salt = secrets.token_bytes(16)
    SALT_FILE.write_bytes(salt)
    key = derive_key(master, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(b'{}')
    FILE.write_bytes(encrypted)
    print("✅ Vault created")

def derive_key(master: str, salt: bytes) -> bytes:
    h = hashlib.pbkdf2_hmac(
        'sha256',
        master.encode(),
        salt,
        600_000,
        dklen=32
    )
    base = base64.urlsafe_b64encode(h)
    return base

def main():
    parser = argparse.ArgumentParser(description='Password Manager')
    subparser = parser.add_subparsers(dest='command', required=True)
    subparser.add_parser(
        'init',
        help='Create new vault'
    )
    p_add = subparser.add_parser('add', help='Add a password')
    p_add.add_argument(
        'site',
        help='Site name (e.g. github)',
    )
    p_get = subparser.add_parser('get', help='Get a password')
    p_get.add_argument(
        'site',
    )
    subparser.add_parser('list', help='List all sites')

    args = parser.parse_args()

    if args.command == 'init':
        cmd_init()
    elif args.command == 'add':
        cmd_add(args.site)
    elif args.command == 'get':
        cmd_get(args.site)
    elif args.command == 'list':
        cmd_list()    

if __name__ == '__main__':
    main()