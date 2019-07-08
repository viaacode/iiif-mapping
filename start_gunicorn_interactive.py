from lump.gunicorn import GunicornInteractiveApplication
from app import app
import logging

logging.basicConfig(level=logging.WARNING)

if __name__ == '__main__':
    app = GunicornInteractiveApplication(app)
    app.print_help()
    app.run()

