"""Optional HTTP API. Installed with ``pip install cockup[web]``."""

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from cockup.fallback import NoPlaceError, fallback, places
from cockup.rudeness import RudenessKnob


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def rudeness_index(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "name": "rudeness knob",
            "scale": [
                {
                    "value": int(level),
                    "slug": level.slug,
                    "label": level.label,
                    "description": level.description,
                }
                for level in RudenessKnob
            ]
        }
    )


async def places_index(request: Request) -> JSONResponse:
    try:
        found = places(
            rudeness=_blank_as_none(request.query_params.get("rudeness")),
            country=_blank_as_none(request.query_params.get("country")),
        )
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return JSONResponse([place.to_dict() for place in found])


async def fallback_route(request: Request) -> JSONResponse:
    params = request.query_params
    try:
        place = fallback(
            rudeness=_blank_as_none(params.get("rudeness")) or RudenessKnob.STAG_DO,
            seed=_blank_as_none(params.get("seed")),
            country=_blank_as_none(params.get("country")),
        )
    except NoPlaceError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if params.get("format") == "geojson":
        return JSONResponse(place.to_geojson())
    return JSONResponse(place.to_dict())


def _blank_as_none(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/v1/rudeness", rudeness_index, methods=["GET"]),
        Route("/v1/places", places_index, methods=["GET"]),
        Route("/v1/fallback", fallback_route, methods=["GET"]),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
        )
    ],
)
