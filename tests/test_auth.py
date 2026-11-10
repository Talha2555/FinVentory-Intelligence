import csv

import pytest

import auth


def test_salted_hash_and_verification():
    first = auth.hash_password('a secure password')
    assert first != auth.hash_password('a secure password')
    assert auth.verify_password('a secure password', first)
    assert not auth.verify_password('incorrect', first)
    assert not auth.verify_password('admin123', 'admin123')
    assert not auth.verify_password('anything', 'scrypt$999999999$8$1$aa$bb')
    with pytest.raises(ValueError):
        auth.hash_password('short')


def test_accounts(tmp_path, monkeypatch):
    path = tmp_path / 'users.csv'
    monkeypatch.setenv('FINVENTORY_USERS_FILE', str(path))
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate('admin', 'password')
    path.write_text('username,password,role\nadmin,admin123,Admin\n')
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate('admin', 'admin123')
    with path.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['username', 'password_hash', 'role'])
        writer.writerow(['owner', auth.hash_password('a secure password'), 'Admin'])
    assert auth.authenticate('owner', 'a secure password') == 'Admin'
    assert auth.authenticate('owner', 'bad') is None
    assert auth.authenticate('missing', 'a secure password') is None
    path.write_text(path.read_text() + path.read_text().splitlines()[1] + '\n')
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate('owner', 'a secure password')


def test_account_setup_cli(tmp_path, monkeypatch):
    import stat
    import sys
    path = tmp_path / 'private.csv'
    monkeypatch.setenv('FINVENTORY_USERS_FILE', str(path))
    monkeypatch.setattr(sys, 'argv', ['auth.py', 'owner', '--role', 'Admin'])
    monkeypatch.setattr(auth.getpass, 'getpass', lambda _: 'a secure password')
    auth.main()
    assert auth.authenticate('owner', 'a secure password') == 'Admin'
    assert 'a secure password' not in path.read_text()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(SystemExit):
        auth.main()  # duplicate usernames are rejected
