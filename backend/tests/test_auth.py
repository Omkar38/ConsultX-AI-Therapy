import os
import tempfile
import unittest
from unittest import mock

from backend.auth import APIKeyAuthenticator, AuthenticationError


class APIKeyAuthenticatorTests(unittest.TestCase):
    def test_disabled_authenticator_allows_requests(self):
        auth = APIKeyAuthenticator(keys=set())
        self.assertFalse(auth.is_enabled())
        self.assertTrue(auth.authenticate({"Authorization": "Bearer whatever"}))

    def test_bearer_token_authentication(self):
        auth = APIKeyAuthenticator(keys={"secret-token"})
        headers = {"Authorization": "Bearer secret-token"}
        self.assertTrue(auth.authenticate(headers))

    def test_x_api_key_authentication(self):
        auth = APIKeyAuthenticator(keys={"secret-token"})
        headers = {"X-API-Key": "secret-token"}
        self.assertTrue(auth.authenticate(headers))

    def test_missing_key_rejected(self):
        auth = APIKeyAuthenticator(keys={"secret-token"})
        headers = {"Authorization": "Bearer wrong"}
        self.assertFalse(auth.authenticate(headers))
        with self.assertRaises(AuthenticationError):
            auth.require(headers)

    def test_from_env_supports_inline_keys(self):
        with mock.patch.dict(os.environ, {"CONSULTX_API_KEYS": "alpha, beta"}):
            auth = APIKeyAuthenticator.from_env()
            self.assertTrue(auth.authenticate({"Authorization": "Bearer alpha"}))
            self.assertTrue(auth.authenticate({"X-API-Key": "beta"}))

    def test_from_env_supports_key_file(self):
        handle = tempfile.NamedTemporaryFile("w", prefix="consultx-keys-", delete=False)
        path = handle.name
        try:
            handle.write("# comment line\nsecret-one\nsecret-two\n")
            handle.close()
            with mock.patch.dict(
                os.environ,
                {
                    "CONSULTX_API_KEYS": "inline",
                    "CONSULTX_API_KEYS_FILE": path,
                },
                clear=True,
            ):
                auth = APIKeyAuthenticator.from_env()
                # File keys are merged with inline keys.
                self.assertTrue(auth.authenticate({"Authorization": "Bearer inline"}))
                self.assertTrue(auth.authenticate({"Authorization": "Bearer secret-one"}))
                self.assertTrue(auth.authenticate({"X-API-Key": "secret-two"}))
        finally:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def test_missing_key_file_raises(self):
        with mock.patch.dict(
            os.environ,
            {"CONSULTX_API_KEYS_FILE": "/tmp/consultx-missing-keys"},
            clear=True,
        ):
            with self.assertRaises(AuthenticationError):
                APIKeyAuthenticator.from_env()


if __name__ == "__main__":
    unittest.main()
