import pytest

from elekto.core.encryption import encrypt, decrypt


def test_encrypt_decrypt_cycle(salt) -> None:
    passcode = '<PASSWORD>'
    target = 'very secret'

    encrypted = encrypt(salt, passcode, target)
    assert decrypt(salt, passcode, encrypted) == target


def test_decrypt_bad_passcode(salt) -> None:
    passcode = '<PASSWORD>'
    encrypted = encrypt(salt, passcode, '')

    with pytest.raises(Exception) as e:
        decrypt(salt, 'bad passcode', encrypted)
        assert "Wrong passcode. Decryption Failed!" in str(e)
