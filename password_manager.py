import os, json
from dataclasses import dataclass
from argon2.low_level import hash_secret_raw, Type
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

@dataclass(frozen=True)
class Argon2Params:
    time_cost: int = 3 # iterations over memory
    memory_cost: int = 65536 # 64 MiB
    parallelism: int = 4 # threads
    hash_len: int = 32 # 256 bit
    salt_size: int = 16 # 128 bit
    iv_size: int = 12 # 96 bit

class PasswordManager:
    def __init__(self, params: Argon2Params = Argon2Params()):
        self.params = params

    def _derive_key(self, password: str, salt: bytes, params: Argon2Params) -> bytes:
        return hash_secret_raw(
            secret=password.encode(),
            salt=salt,
            time_cost=params.time_cost,
            memory_cost=params.memory_cost,
            parallelism=params.parallelism,
            hash_len=params.hash_len,
            type=Type.ID,
        )

    def encrypt_vault(self, password: str, data: dict) -> dict:
        p = self.params
        salt = os.urandom(p.salt_size)
        iv = os.urandom(p.iv_size)
        key = self._derive_key(password, salt, p)

        ciphertext = AESGCM(key).encrypt(iv, json.dumps(data).encode(), None)

        return {
            "kdf": {
                "type": "argon2id",
                "time_cost": p.time_cost,
                "memory_cost": p.memory_cost,
                "parallelism": p.parallelism,
                "hash_len": p.hash_len,
            },
            "salt": salt.hex(),
            "iv": iv.hex(),
            "ciphertext": ciphertext.hex(),
        }

    def decrypt_vault(self, password: str, payload: dict) -> dict | None:
        kdf = payload["kdf"]
        if kdf.get("type") != "argon2id":
            raise ValueError(f"Unsupported KDF: {kdf.get('type')!r}")

        stored_params = Argon2Params(
            time_cost=kdf["time_cost"],
            memory_cost=kdf["memory_cost"],
            parallelism=kdf["parallelism"],
            hash_len=kdf["hash_len"],
        )

        salt = bytes.fromhex(payload["salt"])
        iv = bytes.fromhex(payload["iv"])
        ciphertext = bytes.fromhex(payload["ciphertext"])

        key = self._derive_key(password, salt, stored_params)

        try:
            plaintext = AESGCM(key).decrypt(iv, ciphertext, None)
            return json.loads(plaintext)
        
        except InvalidTag:
            return None  # wrong password or tampered ciphertext

# demo
if __name__ == "__main__":
    pm = PasswordManager()
    vault_data = {"github.com": "hunter2", "gmail.com": "correct-horse-42!"}

    print("Encrypting vault...")
    payload = pm.encrypt_vault("my-master-password", vault_data)
    print("Stored:", json.dumps(payload, indent=2))

    print("\nDecrypting with correct password...")
    result = pm.decrypt_vault("my-master-password", payload)
    print("Decrypted:", result)

    print("\nDecrypting with wrong password...")
    result = pm.decrypt_vault("wrong-password", payload)
    print("Wrong password:", result)