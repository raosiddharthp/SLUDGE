"""API for the reviewer app. The data layer is injected, so routing, guards and caching test offline."""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from pathlib import Path

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.web.cache import TTLCache
from app.web.rules import CASE_ID, LENSES, clean_decide, clean_member

log = logging.getLogger("sludge.web")
MAX_BODY = 4096
STATIC = Path(__file__).parent / "static"
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
                               "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
                               "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


def _default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def _json(payload, status=200):
    return Response(json.dumps(payload, default=_default), status_code=status, media_type="application/json")


async def _read(request):
    """Returns (body, error_response). Rejects oversized or malformed JSON before anything else runs."""
    try:
        declared = int(request.headers.get("content-length") or 0)
    except ValueError:
        declared = 0
    if declared > MAX_BODY:
        return None, _json({"error": "request too large"}, 413)
    raw = await request.body()
    if len(raw) > MAX_BODY:
        return None, _json({"error": "request too large"}, 413)
    try:
        return json.loads(raw or b"null"), None
    except ValueError:
        return None, _json({"error": "invalid JSON"}, 400)


def make_app(data, lens_cache=None):
    cache = lens_cache or TTLCache(300)

    def home(request):
        return FileResponse(STATIC / "index.html", media_type="text/html")

    def health(request):
        return _json({"ok": True})

    def queue(request):
        return _json({"queue": data.queue()})

    def override(request):
        return _json(data.override())

    def usage(request):
        return _json(data.usage())

    def case(request):
        case_id = request.path_params["case_id"]
        if not CASE_ID.match(case_id):
            return _json({"error": "not found"}, 404)
        found = data.case(case_id)
        if not found:
            return _json({"error": "not found"}, 404)
        try:
            data.log_view(case_id, found.get("member_id"))
        except Exception as exc:
            # Fail closed: a view that cannot be logged is not shown.
            log.warning("access log write failed: %s", type(exc).__name__)
            return _json({"error": "access log unavailable"}, 503)
        return _json(found)

    def lens(request):
        name = request.path_params["name"]
        if name not in LENSES:
            return _json({"error": "not found"}, 404)
        try:
            rows = cache.get(name, lambda: data.lens(name))
        except Exception as exc:
            log.warning("lens %s failed: %s", name, type(exc).__name__)
            return _json({"error": "lens unavailable"}, 502)
        return _json({"lens": name, "rows": rows})

    async def assess(request):
        body, error = await _read(request)
        if error:
            return error
        try:
            member = clean_member(body)
        except ValueError as exc:
            return _json({"error": str(exc)}, 400)
        slot = await run_in_threadpool(data.take_slot)
        if not slot["allowed"]:
            return _json({"error": "daily limit reached", "usage": slot}, 429)
        try:
            result = await run_in_threadpool(data.assess, member)
        except Exception as exc:
            log.warning("assessment failed: %s", type(exc).__name__)
            return _json({"error": "assessment failed", "usage": slot}, 502)
        return _json({"result": result, "usage": slot})

    async def decide(request):
        body, error = await _read(request)
        if error:
            return error
        try:
            case_id, decisions, reviewer, note = clean_decide(body)
        except ValueError as exc:
            return _json({"error": str(exc)}, 400)
        try:
            outcome = await run_in_threadpool(data.decide, case_id, decisions, reviewer, note)
        except ValueError as exc:
            return _json({"error": str(exc)}, 400)
        except KeyError:
            return _json({"error": "not found"}, 404)
        except Exception as exc:
            log.warning("decide failed: %s", type(exc).__name__)
            return _json({"error": "could not record the decision"}, 500)
        return _json(outcome)

    return Starlette(middleware=[Middleware(SecurityHeaders)], routes=[
        Route("/", home),
        Mount("/static", app=StaticFiles(directory=STATIC), name="static"),
        Route("/health", health),
        Route("/api/queue", queue),
        Route("/api/override", override),
        Route("/api/usage", usage),
        Route("/api/case/{case_id}", case),
        Route("/api/lens/{name}", lens),
        Route("/api/assess", assess, methods=["POST"]),
        Route("/api/decide", decide, methods=["POST"]),
    ])
