"""Command line: ``cockup`` picks a place, ``cockup serve`` starts the web extra."""

import argparse
import json
import sys

from cockup.fallback import NoPlaceError, fallback
from cockup.place import Place


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "serve":
        return _serve(args[1:])
    return _print_fallback(args)


def _print_fallback(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="cockup",
        description="Pick an amusing real place when a sailing session has no fix.",
        epilog="Run `cockup serve --help` to start the HTTP API.",
    )
    parser.add_argument(
        "--rudeness",
        default="stag_do",
        help="rudeness knob: vicar, school_run, office_party, stag_do, rugby_tour, or cancelled (default: stag_do)",
    )
    parser.add_argument(
        "--seed",
        default=None,
        help="stable pick for a session id; omit for a random place",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="ISO 3166-1 alpha-2 code, or UK",
    )
    parser.add_argument(
        "--geojson",
        action="store_true",
        help="print a GeoJSON Feature",
    )
    namespace = parser.parse_args(argv)
    try:
        place = fallback(
            rudeness=namespace.rudeness,
            seed=namespace.seed,
            country=namespace.country,
        )
    except (NoPlaceError, ValueError, TypeError) as exc:
        print(f"cockup: {exc}", file=sys.stderr)
        return 2
    if namespace.geojson:
        json.dump(place.to_geojson(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(_line(place))
    return 0


def _line(place: Place) -> str:
    zoom = int(place.zoom) if place.zoom == int(place.zoom) else place.zoom
    return f"{place.name} ({place.lat:.2f}, {place.lon:.2f}) zoom {zoom}"


def _serve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="cockup serve",
        description="Serve the fallback gazetteer over HTTP.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    namespace = parser.parse_args(argv)
    try:
        import uvicorn
        from cockup.web import app
    except ImportError:
        print(
            "cockup: serve needs the web extra. Install it with: pip install 'cockup[web]'",
            file=sys.stderr,
        )
        return 1
    uvicorn.run(app, host=namespace.host, port=namespace.port)
    return 0
