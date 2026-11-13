"""ASGI entry point: python -m uvicorn app.web.main:app"""
from app.web import data
from app.web.server import make_app

app = make_app(data)
