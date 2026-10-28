"""CLI output and the optional HTTP API."""

import json
import re

from starlette.testclient import TestClient

from cockup import fallback
from cockup.cli import main
from cockup.web import app


def test_cli_prints_a_map_line(capsys):
    assert main(["--seed", "session-123", "--country", "GB", "--rudeness", "stag_do"]) == 0
    line = capsys.readouterr().out.strip()
    assert re.fullmatch(r".+ \(-?\d+\.\d{2}, -?\d+\.\d{2}\) zoom \d+", line)


def test_cli_geojson_matches_the_library(capsys):
    assert main(["--geojson", "--seed", "session-123", "--country", "UK"]) == 0
    feature = json.loads(capsys.readouterr().out)
    place = fallback(seed="session-123", country="GB")
    assert feature == place.to_geojson()


def test_cli_unknown_country(capsys):
    assert main(["--country", "ZZ", "--seed", "1"]) == 2
    assert "no place" in capsys.readouterr().err


def test_serve_invokes_uvicorn(monkeypatch):
    called = {}

    def fake_run(application, host, port):
        called["app"] = application
        called["host"] = host
        called["port"] = port

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", fake_run)
    assert main(["serve", "--host", "0.0.0.0", "--port", "9001"]) == 0
    assert called == {"app": app, "host": "0.0.0.0", "port": 9001}


def test_health_and_cors():
    with TestClient(app) as client:
        response = client.get("/health", headers={"Origin": "https://charts.example"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["access-control-allow-origin"] == "*"


def test_fallback_endpoint_matches_the_library():
    params = {"rudeness": "stag_do", "seed": "session-123", "country": "GB"}
    with TestClient(app) as client:
        body = client.get("/v1/fallback", params=params)
        feature = client.get("/v1/fallback", params={**params, "format": "geojson"})
    place = fallback(rudeness="stag_do", seed="session-123", country="GB")
    assert body.status_code == 200
    assert body.json()["id"] == place.id
    assert body.json()["geojson"]["geometry"]["coordinates"] == [place.lon, place.lat]
    assert feature.status_code == 200
    assert feature.json() == place.to_geojson()


def test_rudeness_scale_and_place_index():
    with TestClient(app) as client:
        scale = client.get("/v1/rudeness")
        indexed = client.get("/v1/places", params={"rudeness": "cancelled", "country": "GB"})
        bad = client.get("/v1/fallback", params={"rudeness": "filthy"})
        missing = client.get("/v1/fallback", params={"country": "ZZ"})
    assert scale.status_code == 200
    body = scale.json()
    assert body["name"] == "rudeness knob"
    assert [item["slug"] for item in body["scale"]] == [
        "vicar",
        "school_run",
        "office_party",
        "stag_do",
        "rugby_tour",
        "cancelled",
    ]
    assert indexed.status_code == 200
    assert indexed.json() == []
    assert bad.status_code == 400
    assert missing.status_code == 404
