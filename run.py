"""Start the AgriAuction Flask application.

Local development:
    python run.py

Then open http://localhost:5000
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    if os.getenv("FLASK_ENV") == "production":
        debug = False
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=debug)
