# Loading 80 000 NUFORC UAP Reports Into a Fast, Interactive Map  
*End‑to‑end recipe: database → tiles → React/MapLibre front‑end*

---

## 1 One‑time Bulk Ingest into PostGIS

```bash
# 1  Run Postgres + PostGIS (Docker)
docker run -d --name uapdb -e POSTGRES_PASSWORD=secret -p 5432:5432 postgis/postgis:16-3.4

# 2  Load the cleaned NUFORC CSV (≈ 80 k rows)
ogr2ogr -f "PostgreSQL"   PG:"host=localhost user=postgres dbname=postgres password=secret"   nuforc_clean.csv   -oo X_POSSIBLE_NAMES=longitude   -oo Y_POSSIBLE_NAMES=latitude   -nln uap_reports   -nlt POINT   -lco GEOMETRY_NAME=geom   -lco FID=id

# 3  Spatial index for speed
psql -U postgres -c "CREATE INDEX uap_geom_idx ON uap_reports USING GIST (geom);"
```

> **Why PostGIS?** 80 k points are negligible for a spatial index, and you get `ST_AsMVT` (vector‑tile output) for free.

---

## 2 Serve Vector Tiles Directly From the DB (FastAPI)

```python
from fastapi import FastAPI, Response
import asyncpg

app = FastAPI()
POOL = None

@app.on_event("startup")
async def startup():
    global POOL
    POOL = await asyncpg.create_pool(
        dsn="postgresql://postgres:secret@localhost/postgres"
    )

@app.get(
    "/tiles/{z}/{x}/{y}.pbf",
    response_class=Response,
    responses={200: {"content": {"application/x-protobuf": {}}}},
)
async def tile(z: int, x: int, y: int):
    sql = """
    WITH bounds AS (
      SELECT ST_TileEnvelope($1,$2,$3) AS geom
    ),
    mvt AS (
      SELECT ST_AsMVT(tile,'layer0',4096,'geom') AS data
      FROM (
        SELECT id, shape, event_date,
               ST_AsMVTGeom(r.geom, bounds.geom, 4096, 64, true) AS geom
        FROM uap_reports r, bounds
        WHERE ST_Intersects(r.geom, bounds.geom)
      ) tile
    )
    SELECT data FROM mvt;
    """
    async with POOL.acquire() as con:
        buf = await con.fetchval(sql, z, x, y)
    return Response(content=buf, media_type="application/x-protobuf")
```

Now any client can hit `https://api.yoursite.com/tiles/{z}/{x}/{y}.pbf`.

---

## 3 React / MapLibre Front‑End

```js
import maplibregl from 'maplibre-gl';

const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',   // any basemap
  center: [-99, 41],
  zoom: 4
});

map.on('load', () => {
  map.addSource('uap', {
    type: 'vector',
    tiles: ['https://api.yoursite.com/tiles/{z}/{x}/{y}.pbf'],
    minzoom: 0,
    maxzoom: 14
  });

  // Heat layer
  map.addLayer({
    id: 'uap-heat',
    type: 'heatmap',
    source: 'uap',
    'source-layer': 'layer0',
    paint: {
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 0.2, 8, 1]
    }
  });

  // Points for close zoom
  map.addLayer({
    id: 'uap-circle',
    type: 'circle',
    source: 'uap',
    'source-layer': 'layer0',
    minzoom: 7,
    paint: {
      'circle-radius': 4,
      'circle-color': '#ff6a00',
      'circle-stroke-width': 0.5,
      'circle-stroke-color': '#ffffff'
    }
  });
});
```

*Result:* only the sightings that fall inside the user’s current 256 × 256 px tile travel over the wire—smooth even on mobile.

---

## 4 Static & Serverless Alternative (PMTiles)

1. **Bake once** with Tippecanoe  
   ```bash
   tippecanoe -zg -o uap.pmtiles --read-parallel      --drop-rate=1 -l uap nuforc_clean.geojson
   ```
2. **Upload** `uap.pmtiles` to S3 / GitHub Pages.  
3. **Add** `maplibre-gl-pmtiles` plugin in the client; point to the file URL.  
No backend required—great for demos or GitHub‑Pages hosting.

---

## 5 Performance / Cost Snapshot

| Tier | What runs | Typical cost |
|------|-----------|--------------|
| **DB + FastAPI** | t4g.small PostGIS + uvicorn | < \$10 / mo (spot) |
| **Static PMTiles** | S3 + CloudFront | Pennies per 100 k tile hits |
| **Client** | Browser MapLibre‑GL | Free |

---

## 6 Checklist

```text
[ ] Clean NUFORC CSV → nuforc_clean.csv
[ ] Import into PostGIS, add GIST index
[ ] Wire FastAPI `/tiles/{z}/{x}/{y}.pbf`
[ ] Build MapLibre front‑end (heat & circle layers)
[ ] (Optional) Static PMTiles fallback
```

*Done! Your 80 000‑point UFO dataset now feels weightless.*
