from flask import render_template, send_file, redirect, make_response, request
import secrets



class Website:
    def __init__(self, app) -> None:
        self.app = app
        self.routes = {
            '/': {
                'function': self._index,
                'methods': ['GET', 'POST']
            },
            '/assets/<folder>/<file>': {
                'function': self._assets,
                'methods': ['GET', 'POST']
            }
        }

    def _get_or_create_session_id(self):
        session_id = request.cookies.get("_archseek_server_session")
        if not session_id:
            session_id = secrets.token_hex(16)
        return session_id

    def _index(self):
        response = make_response(render_template("index.html"))
        # Set the session cookie if it doesn't exist
        session_id = self._get_or_create_session_id()
        response.set_cookie(
            "_archseek_server_session",
            session_id,
            httponly=False,  # Changed to False for development
            secure=False,    # Changed to False for development
            samesite="Lax",
            max_age=60 * 60,
        )
        return response

    def _assets(self, folder: str, file: str):
        try:
            return send_file(f"./../client/{folder}/{file}", as_attachment=False)
        except:
            return "File not found", 404
