from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Set


class AuthenticationError(Exception):
    """Raised when a request lacks valid authentication credentials."""


def _load_keys_from_file(path: str) -> Set[str]:
    keys: Set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                value = line.strip()
                if value and not value.startswith("#"):
                    keys.add(value)
    except FileNotFoundError:
        raise AuthenticationError(f"API key file not found: {path}") from None
    return keys


@dataclass
class APIKeyAuthenticator:
    """Simple API-key based authentication helper for the HTTP server."""

    keys: Set[str]

    @classmethod
    def from_env(cls) -> "APIKeyAuthenticator":
        """Construct an authenticator from environment settings."""
        env_keys = {
            key.strip()
            for key in os.environ.get("CONSULTX_API_KEYS", "").split(",")
            if key.strip()
        }

        file_path = os.environ.get("CONSULTX_API_KEYS_FILE")
        if file_path:
            file_keys = _load_keys_from_file(file_path)
            env_keys.update(file_keys)

        return cls(keys=env_keys)

    def is_enabled(self) -> bool:
        return bool(self.keys)

    def authenticate(self, headers) -> bool:
        """Validate request headers.

        Accepts either an Authorization bearer token or X-API-Key header.
        """
        if not self.is_enabled():
            return True

        key = self._extract_key(headers)
        return key in self.keys if key else False

    def _extract_key(self, headers) -> Optional[str]:
        if not headers:
            return None
        auth_header = headers.get("Authorization")
        if auth_header:
            parts = auth_header.split(" ", 1)
            if len(parts) == 2 and parts[0].lower() in {"bearer", "token"}:
                return parts[1].strip()
        api_key = headers.get("X-API-Key")
        if api_key:
            return api_key.strip()
        return None

    def require(self, headers) -> None:
        if not self.authenticate(headers):
            raise AuthenticationError("Missing or invalid API key.")

