import uvicorn
from app.server import asgi_app

if __name__ == "__main__":
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
