#!/usr/bin/env python3
"""
WSGI entry point for VoyagerAI Flask application
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
