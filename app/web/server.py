"""Read API for the reviewer app. The data layer is injected, so routing and guards test offline."""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

from app.web.cache import TTLCache
from app.web.rules import CASE_ID, LENSES

log = logging.getLogger("sludge.web")


def _default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def _json(payload, status=200):
    return Response(json.dumps(payload, default=_default), status_code=status, media_type="application/json")


def make_app(data, lens_cache=None):
    cache = lens_cache or TTLCache(300)

    def health(request):
        return _json({"ok": True})

    def queue(request):
        return _json({"queue": data.queue()})

    def override(request):
        return _json(data.override())

    def case(request):
        case_id = request.path_params["case_id"]
        if not CASE_ID.match(case_id):
            return _json({"error": "not found"}, 404)
        found = data.case(case_id)
        return _json(found) if found else _json({"error": "not found"}, 404)

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

    return Starlette(routes=[
        Route("/healthz", health),
        Route("/api/queue", queue),
        Route("/api/override", override),
        Route("/api/case/{case_id}", case),
        Route("/api/lens/{name}", lens),
    ])
