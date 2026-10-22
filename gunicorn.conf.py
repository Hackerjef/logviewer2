import os

import dotenv
dotenv.load_dotenv()


port = os.getenv("PORT", "8080")
host = os.getenv("HOST", "0.0.0.0")

bind = f"{host}:{port}"
workers = 5
accesslog = "-"
proc_name = "logviewer2"