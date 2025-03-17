
from routes import app


import os

if __name__ == "__main__":
    # Use environment variables for production, debug=True for development
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)