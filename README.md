# cockup

A fallback gazetteer for when there is no location. Instead of an empty map, you get a real place with an amusing name, a centre, a zoom, and a bounding box. A rudeness knob decides how smutty that name is allowed to be.

```bash
pip install cockup
```

```python
from cockup import fallback, RudenessKnob

session_id = "session-123"
p = fallback(rudeness=RudenessKnob.STAG_DO, seed=session_id, country="GB")
p.name, p.lat, p.lon, p.zoom, p.bbox
p.to_geojson()
```

`seed` keeps the same place for the same session. `42` and `"42"` match. Leave it out for a different place each call. `country` is an ISO 3166-1 alpha-2 code, and `UK` is accepted as `GB`. Omit it to mean anywhere.

The pick is a rendezvous hash of the seed and the place id. Adding a name to a later release only moves the sessions that now prefer the new one.

## The rudeness knob

`RudenessKnob` is how smutty a name you are prepared to put on the map. Higher is ruder. You get a place at the setting you asked for, not a random mix of every calmer name.

- `VICAR` (0) — safe enough to say in front of the vicar. Dull, Boring, Pity Me, No Place, Lost.
- `SCHOOL_RUN` (1) — sayable on the school run, just. Wetwang, Ugley, Crackpot, Blubberhouses, Come By Chance.
- `OFFICE_PARTY` (2) — innuendo, once someone has opened the wine. Cockermouth, Penistone, Thong, Cocking, Lusty Glaze.
- `STAG_DO` (3) — the mask slips. Great Cockup, Bell End, Sandy Balls, Brown Willy, Intercourse.
- `RUGBY_TOUR` (4) — swearing, and nobody is writing it down. Shitterton, Twatt, Muff, Effin, Bitche.
- `CANCELLED` (5) — no plausible denial. Dildo, Fugging, Wank, Cunter, Dickshooter.

If that country has nothing at the setting you asked for, the knob steps down one stop at a time and stays inside the country. Britain runs out at the rugby tour, so `CANCELLED` in `GB` comes back as a rugby-tour place. `Place.rudeness` is the setting you actually got. An unknown country raises `NoPlaceError` rather than quietly sending the session somewhere else.

`places()` lists the catalogue with the same filters and does not step down.

## Command line

```bash
cockup --country GB --seed session-123
cockup --geojson --rudeness rugby_tour --country GB --seed session-123
```

The first line looks like `Great Cockup (54.69, -3.13) zoom 13`. `--geojson` prints a Feature, with coordinates in `[longitude, latitude]` order.

## Web

The library itself has no dependencies. The HTTP API is an extra:

```bash
pip install "cockup[web]"
cockup serve
```

- `GET /v1/fallback?rudeness=stag_do&seed=session-123&country=GB` — the place, including a `geojson` field
- `GET /v1/fallback?format=geojson` — the Feature on its own
- `GET /v1/places` and `GET /v1/rudeness` — the catalogue and the rudeness knob
- `GET /health`

CORS is open. There is no auth.

```bash
docker build -t cockup .
docker run -p 8000:8000 cockup
```

## Places

Every entry is a real place, with a coordinate taken from OpenStreetMap or Wikidata and recorded in `source`. Notes are ours. The list is bawdy or absurd on purpose. It does not include slurs, and where the joke only exists in English the note says so.

## License

MIT.
