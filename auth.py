"""Local CSV accounts with salted scrypt hashes; no default accounts."""
import argparse
import csv
import getpass
import hashlib
import hmac
import os
from pathlib import Path
import secrets

ROLES = {'Admin', 'Manager', 'Staff'}
DEFAULT_USERS = Path(__file__).resolve().with_name('users.csv')


class AuthenticationError(RuntimeError):
    pass


def hash_password(password):
    if len(password) < 12:
        raise ValueError('Use a password of at least 12 characters')
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f'scrypt$16384$8$1${salt}${digest}'


def verify_password(password, encoded):
    try:
        scheme, n, r, p, salt, digest = encoded.split('$')
        if (scheme, n, r, p) != ('scrypt', '16384', '8', '1') or len(salt) != 32 or len(digest) != 128:
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False


def users_path():
    return Path(os.getenv('FINVENTORY_USERS_FILE', DEFAULT_USERS))


def read_users(path):
    try:
        with path.open(newline='') as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ['username', 'password_hash', 'role']:
                raise AuthenticationError('Invalid account file schema')
            rows = list(reader)
        names = [row['username'] for row in rows]
        if len(names) != len(set(names)) or any(not row['username'] or row['role'] not in ROLES for row in rows):
            raise AuthenticationError('Invalid accounts')
        return rows
    except (OSError, csv.Error, KeyError) as exc:
        raise AuthenticationError('Cannot read accounts') from exc


def authenticate(username, password):
    rows = read_users(users_path())
    for row in rows:
        if row['username'] == username and verify_password(password, row['password_hash']):
            return row['role']
    return None


def main():
    parser = argparse.ArgumentParser(description='Create a hashed local account (password prompted privately)')
    parser.add_argument('username')
    parser.add_argument('--role', choices=sorted(ROLES), default='Staff')
    args = parser.parse_args()
    path = users_path()
    rows = read_users(path) if path.exists() else []
    if not args.username.strip() or any(row['username'] == args.username for row in rows):
        parser.error('Username must be nonempty and unique')
    password = getpass.getpass('Password (12+ characters): ')
    if password != getpass.getpass('Confirm password: '):
        parser.error('Passwords do not match')
    try:
        encoded = hash_password(password)
    except ValueError as exc:
        parser.error(str(exc))
    rows.append(dict(username=args.username, password_hash=encoded, role=args.role))
    # Atomic replacement; only the owner can read credentials.
    temp = path.with_name(path.name + '.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['username', 'password_hash', 'role'])
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


if __name__ == '__main__':
    main()
