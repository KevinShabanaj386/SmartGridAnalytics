# PostGIS Geospatial Analytics - Smart Grid Analytics

## Përmbledhje

PostGIS është integruar në sistem për analiza gjeografike dhe hapësinore të të dhënave të Smart Grid. Kjo lejon analiza të avancuara bazuar në lokacionet e sensorëve.

## Karakteristika

### 1. Spatial Data Storage
- **PostGIS Extension**: Aktivizuar në PostgreSQL
- **Geometry Column**: `location` me tip `POINT` në SRID 4326 (WGS84)
- **Spatial Index**: GIST index për queries të shpejta

### 2. Geospatial Queries

#### Nearby Sensors
Gjen sensorët brenda një rrezeje specifike:
```bash
GET /api/v1/analytics/geospatial/nearby-sensors?lat=41.3275&lon=19.8187&radius_km=10
```

#### Heatmap Data
Kthen të dhëna për heatmap me grid aggregation:
```bash
GET /api/v1/analytics/geospatial/heatmap?hours=24&grid_size=0.1
```

#### Route Analysis
Analizon të dhënat përgjatë një rruge:
```bash
GET /api/v1/analytics/geospatial/route-analysis?points=[{"lat":41.3,"lon":19.8},{"lat":41.4,"lon":19.9}]
```

#### Sensor Clustering
K-Means clustering për grupim të sensorëve:
```bash
GET /api/v1/analytics/geospatial/clustering?k=5
```

#### Convex Hull
Kufiri minimal që përfshin të gjithë sensorët:
```bash
GET /api/v1/analytics/geospatial/convex-hull
```

## Struktura e Të Dhënave

### Tabela sensor_data

```sql
CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    value DECIMAL(10, 4) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    location GEOMETRY(POINT, 4326),  -- PostGIS geometry
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index për performancë
CREATE INDEX idx_sensor_data_location 
ON sensor_data USING GIST (location);
```

## Përdorimi

### 1. Dërgo të dhëna me lokacion

```bash
curl -X POST http://localhost:5000/api/v1/ingest/sensor \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "sensor_type": "voltage",
    "value": 220.5,
    "location": {"lat": 41.3275, "lon": 19.8187}
  }'
```

### 2. Gjej sensorët afër

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/geospatial/nearby-sensors?lat=41.3275&lon=19.8187&radius_km=5" \
  -H "Authorization: Bearer <token>"
```

### 3. Merr heatmap data

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/geospatial/heatmap?hours=24" \
  -H "Authorization: Bearer <token>"
```

### 4. Analizo rrugë

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/geospatial/route-analysis?points=[{\"lat\":41.3,\"lon\":19.8},{\"lat\":41.4,\"lon\":19.9}]" \
  -H "Authorization: Bearer <token>"
```

## PostGIS Functions të Përdorura

### ST_GeomFromText
Krijon geometry nga WKT (Well-Known Text)

### ST_SetSRID
Vendos SRID (Spatial Reference System ID)

### ST_Distance
Llogarit distancën midis dy geometries

### ST_DWithin
Kontrollon nëse një geometry është brenda distancës së specifikuar

### ST_Within
Kontrollon nëse një geometry është brenda një tjetri

### ST_ClusterKMeans
K-Means clustering për geometries

### ST_ConvexHull
Kthen convex hull të një grupi geometries

### ST_Collect
Kombinon geometries në një collection

## Performance Optimization

### Spatial Index
GIST index përdoret për queries të shpejta:
```sql
CREATE INDEX idx_sensor_data_location 
ON sensor_data USING GIST (location);
```

### Query Optimization
- Përdor `ST_DWithin` në vend të `ST_Distance < threshold`
- Përdor geography type për distanca të sakta në metra/km
- Limit rezultatet për queries të mëdha

## Use Cases

### 1. Network Coverage Analysis
Analizon mbulimin e rrjetit bazuar në lokacionet e sensorëve

### 2. Fault Location
Gjen lokacionin e dështimeve bazuar në anomalitë gjeografike

### 3. Load Distribution
Analizon shpërndarjen e ngarkesës në hapësirë

### 4. Infrastructure Planning
Ndihmon në planifikimin e infrastrukturës së re

## Integrim me Frontend

Frontend mund të përdorë këto endpoints për:
- Harta interaktive me sensorët
- Heatmaps për visualizim
- Route planning dhe analysis
- Clustering visualization

## Best Practices

1. **Koordinatat**: Përdorni WGS84 (SRID 4326) për konsistencë
2. **Indexing**: Gjithmonë krijoni spatial index për kolonat geometry
3. **Geography vs Geometry**: Përdorni geography për distanca të sakta
4. **Query Optimization**: Përdorni ST_DWithin në vend të ST_Distance

## Troubleshooting

### PostGIS extension nuk aktivizohet
```sql
-- Kontrollo nëse PostGIS është i instaluar
SELECT PostGIS_version();

-- Aktivizo extension
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Spatial queries janë të ngadalshme
```sql
-- Verifikoni që ka spatial index
\d+ sensor_data

-- Krijo index nëse mungon
CREATE INDEX idx_sensor_data_location 
ON sensor_data USING GIST (location);
```

## Hapi Tjetër

- [ ] Integrim me QGIS për visualization
- [ ] Shto më shumë geospatial algorithms
- [ ] Real-time geospatial streaming
- [ ] Integration me mapping libraries (Leaflet, Mapbox)

