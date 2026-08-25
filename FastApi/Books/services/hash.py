import hashlib
import secrets

def hash_password(password: str):
    salt = secrets.token_bytes(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
    )

    return salt.hex() + ":" + hashed.hex()


def verify_password(password: str, stored_password: str):
    salt_hex, stored_hash_hex = stored_password.split(":", 1)

    salt = bytes.fromhex(salt_hex)
    stored_hash = bytes.fromhex(stored_hash_hex)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
    )

    return secrets.compare_digest(hashed, stored_hash)


def verify_password(password: str, stored_password: str):
    salt_hex, stored_hash_hex = stored_password.split(":", 1)

    salt = bytes.fromhex(salt_hex)
    stored_hash = bytes.fromhex(stored_hash_hex)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
        #Run the algorithm 20 times
    )

    return secrets.compare_digest(hashed, stored_hash)

#Usage
# stored = hash_password("my-secret-password")

# print(verify_password("my-secret-password", stored))
# True

# print(verify_password("wrong-password", stored))
# False