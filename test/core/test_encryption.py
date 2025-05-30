import pytest
from unittest import mock

from ..conftest import KDF_KEY_MOCK
from elekto.core.encryption import encrypt, decrypt


@mock.patch('elekto.core.encryption.pwhash.argon2i.kdf', return_value=KDF_KEY_MOCK)
def test_encrypt_decrypt_cycle(salt) -> None:
    passcode = '<PASSWORD>'
    target = 'very secret'

    encrypted = encrypt(salt, passcode, target)
    assert decrypt(salt, passcode, encrypted) == target


@mock.patch('elekto.core.encryption.pwhash.argon2i.kdf', return_value=KDF_KEY_MOCK)
def test_decrypt_bad_passcode(salt) -> None:
    passcode = '<PASSWORD>'
    encrypted = encrypt(salt, passcode, '')

    with pytest.raises(Exception) as e:
        decrypt(salt, 'bad passcode', encrypted)
        assert "Wrong passcode. Decryption Failed!" in str(e)
