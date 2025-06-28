import sys
sys.path.append("..")
from app import app as application

# Vercel expects a 'handler' function
def handler(environ, start_response):
    return application.wsgi_app(environ, start_response)

# For local testing
if __name__ == "__main__":
    application.run()
