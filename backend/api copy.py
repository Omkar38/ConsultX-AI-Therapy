from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple
from urllib.parse import parse_qs, urlparse

from .auth import APIKeyAuthenticator, AuthenticationError
from .models import SenderRole, SessionStatus
from .session_tracking import (
    SessionClosed,
    SessionNotFound,
    SessionTracker,
)
from .storage import SessionStorage


def _get_authenticator() -> APIKeyAuthenticator:
    try:
        return APIKeyAuthenticator.from_env()
    except AuthenticationError as exc:
        raise RuntimeError(str(exc)) from None


def _get_tracker() -> SessionTracker:
    db_path = os.environ.get("CONSULTX_DB_PATH", "consultx.db")
    buffer_size = int(os.environ.get("CONSULTX_BUFFER_SIZE", "20"))
    storage = SessionStorage(db_path)
    return SessionTracker(storage=storage, buffer_size=buffer_size)


TRACKER = _get_tracker()
AUTH = _get_authenticator()


class SessionRequestHandler(BaseHTTPRequestHandler):
    """Minimal REST controller for the ConsultX session tracking backend."""

    server_version = "ConsultXSessionServer/0.1"

    # --- HTTP METHOD HANDLERS -------------------------------------------------

    def do_POST(self) -> None:  # noqa: D401 - inherited docstring not required.
        path, segments = self._path_parts()

        if not self._ensure_authenticated():
            return

        if path == "/sessions" and len(segments) == 1:
            self._create_session()
            return

        if path == "/mood-entries" and len(segments) == 1:
            self._add_mood_entry()
            return

        if path == "/signup" and len(segments) == 1:
            self._signup_user()
            return

        if path == "/login" and len(segments) == 1:
            self._login_user()
            return

        if len(segments) >= 3 and segments[0] == "sessions":
            session_id = segments[1]
            if len(segments) == 3 and segments[2] == "messages":
                self._append_message(session_id)
                return
            if len(segments) == 3 and segments[2] == "end":
                self._end_session(session_id)
                return

        self._send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def do_GET(self) -> None:  # noqa: D401
        path, segments = self._path_parts()

        if not self._ensure_authenticated():
            return

        if path == "/sessions" and len(segments) == 1:
            self._list_sessions()
            return

        if len(segments) >= 2 and segments[0] == "sessions":
            session_id = segments[1]
            if len(segments) == 2:
                self._retrieve_session(session_id)
                return
            if len(segments) == 3 and segments[2] == "summary":
                self._get_summary(session_id)
                return

        if path == "/weather" and len(segments) == 1:
            self._get_weather()
            return

        if path == "/mood-entries" and len(segments) == 1:
            self._get_mood_entries()
            return

        if len(segments) >= 2 and segments[0] == "user":
            user_id = segments[1]
            if len(segments) == 2:
                self._get_user(user_id)
                return

        self._send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def do_OPTIONS(self) -> None:  # noqa: D401
        """Handle CORS preflight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    # --- Endpoint implementations --------------------------------------------

    def _create_session(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        user_id = payload.get("user_id")
        if not user_id:
            self._send_error(HTTPStatus.BAD_REQUEST, "'user_id' is required.")
            return
        metadata = payload.get("metadata") or {}
        session = TRACKER.create_session(user_id=user_id, metadata=metadata)
        buffer = TRACKER.get_buffer(session.id)
        self._send_json(
            {
                "session": session.to_dict(),
                "buffer": buffer.to_dict(),
            },
            status=HTTPStatus.CREATED,
        )

    def _list_sessions(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        user_id = query.get("user_id", [None])[0]
        status_param = query.get("status", [None])[0]

        status = None
        if status_param:
            try:
                status = SessionStatus(status_param)
            except ValueError:
                self._send_error(HTTPStatus.BAD_REQUEST, f"Unknown status '{status_param}'.")
                return

        sessions = TRACKER.list_sessions(user_id=user_id, status=status)
        self._send_json({"sessions": [session.to_dict() for session in sessions]})

    def _retrieve_session(self, session_id: str) -> None:
        try:
            session = TRACKER.get_session(session_id)
            buffer = TRACKER.get_buffer(session_id)
            metrics = TRACKER.storage.get_metrics(session_id)
        except SessionNotFound as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        response = {
            "session": session.to_dict(),
            "buffer": buffer.to_dict(),
            "metrics": metrics.to_dict() if metrics else None,
        }
        self._send_json(response)

    def _append_message(self, session_id: str) -> None:
        payload = self._read_json()
        if payload is None:
            return
        sender_value = payload.get("sender")
        content = payload.get("content")
        if not sender_value or not content:
            self._send_error(HTTPStatus.BAD_REQUEST, "'sender' and 'content' are required.")
            return
        try:
            sender = SenderRole(sender_value)
        except ValueError:
            self._send_error(HTTPStatus.BAD_REQUEST, f"Invalid sender '{sender_value}'.")
            return

        try:
            result = TRACKER.append_message(
                session_id,
                sender=sender,
                content=content,
            )
        except SessionNotFound as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        except SessionClosed as exc:
            self._send_error(HTTPStatus.CONFLICT, str(exc))
            return

        self._send_json(
            {
                "message": result.message.to_dict(),
                "risk": result.risk.to_dict(),
                "buffer": result.buffer.to_dict(),
                "metrics": result.metrics.to_dict(),
            },
            status=HTTPStatus.CREATED,
        )

    def _end_session(self, session_id: str) -> None:
        try:
            summary = TRACKER.end_session(session_id)
        except SessionNotFound as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        self._send_json({"summary": summary.to_dict()})

    def _get_summary(self, session_id: str) -> None:
        try:
            summary = TRACKER.get_summary(session_id)
        except SessionNotFound as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        self._send_json({"summary": summary.to_dict()})
        
    
    def _signup_user(self) -> None:
        payload = self._read_json()
        username = payload.get("name")
        password = payload.get("password")
        if not username or not password:
            self._send_error(HTTPStatus.BAD_REQUEST, "'name' and 'password' are required.")
            return
        json_path = os.path.join(os.path.dirname(__file__), "..", "mock_data", "responses.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        if username in data:
            self._send_error(HTTPStatus.CONFLICT, "Username already exists.")
            return
        data[username] = {"password": password, "mood_entries": []}
        try: 
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to write user: {e}")
            return
        self._send_json({"success": True, "user": username})
        
    
    def _login_user(self) -> None:
        payload = self._read_json()
        username = payload.get("name")
        password = payload.get("password")
        if not username or not password:
            self._send_error(HTTPStatus.BAD_REQUEST, "'name' and 'password' are required.")
            return
        json_path = os.path.join(os.path.dirname(__file__), "..", "mock_data", "responses.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not read user data.")
            return
        user = data.get(username)
        if not user or user.get("password") != password:
            self._send_error(HTTPStatus.UNAUTHORIZED, "Invalid username or password.")
            return
        self._send_json({"success": True, "user": username})
    
    def _get_user(self, user_id: str) -> None:
        """Get user profile data."""
        # Hardcoded mock data for now
        mock_user = {
            "id": user_id,
            "name": "Alex",
            "email": "alex@example.com",
            "joined_date": "2025-01-15"
        }
        self._send_json({"user": mock_user})

    def _get_weather(self) -> None:
        """Get current weather data."""
        # Hardcoded mock data for now
        mock_weather = {
            "temperature": 72,
            "description": "Sunny",
            "humidity": 45,
            "location": "San Francisco, CA"
        }
        self._send_json({"weather": mock_weather})

    def _get_mood_entries(self) -> None:
        """Get mood entries for a user."""
        query = parse_qs(urlparse(self.path).query)
        user_id = query.get("user_id", [None])[0]
        
        if not user_id:
            self._send_error(HTTPStatus.BAD_REQUEST, "'user_id' query parameter is required.")
            return

        # load mood entries from storage - for now, return mock data from json file
        with open("mock_data/responses.json", "r") as f:
            mock_mood_entries = json.load(f)[user_id]["mood_entries"]
        self._send_json({"mood_entries": mock_mood_entries, "user_id": user_id})
        
    def _add_mood_entry(self) -> None:
        payload = self._read_json()
        user_id = payload.get("user_id")
        date = payload.get("date")
        mood = payload.get("mood")
        if not user_id or not date or not mood:
            self._send_error(HTTPStatus.BAD_REQUEST, "'user_id', 'date', and 'mood' are required.")
            return
        
        # Store the mood entry - for now, add it mock data file
        with open("mock_data/responses.json", "r+") as f:
            data = json.load(f)
            data["mood_entries"].append({
                "date": date,
                "mood": mood
            })
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        entry = {"user_id": user_id, "date": date, "mood": mood}
        self._send_json({"entry": entry}, status=HTTPStatus.CREATED)

    # --- Utility helpers -----------------------------------------------------

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Invalid Content-Length header.")
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Malformed JSON payload.")
            return None

    def _send_json(self, payload, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str, *, extra_headers: list[tuple[str, str]] | None = None) -> None:
        payload = {"error": message, "status": status.value}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for name, value in extra_headers:
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        """Send CORS headers to allow frontend access."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _ensure_authenticated(self) -> bool:
        if not AUTH.is_enabled():
            return True
        if AUTH.authenticate(self.headers):
            return True
        self._send_error(
            HTTPStatus.UNAUTHORIZED,
            "Missing or invalid API key.",
            extra_headers=[("WWW-Authenticate", 'Bearer realm="ConsultX"')],
        )
        return False

    def _path_parts(self) -> Tuple[str, list]:
        parsed = urlparse(self.path)
        segments = [part for part in parsed.path.split("/") if part]
        normalized = "/" + "/".join(segments) if segments else "/"
        return normalized, segments

    def log_message(self, *_args):  # noqa: D401
        # Suppress default logging to keep CLI output tidy.
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the HTTP server."""
    server = ThreadingHTTPServer((host, port), SessionRequestHandler)
    print(f"ConsultX session server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down session server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
