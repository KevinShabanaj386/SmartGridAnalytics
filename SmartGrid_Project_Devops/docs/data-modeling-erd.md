# Data Modeling - ERD dhe UML Diagrams

## Modelimi Konceptual, Logjik dhe Fizik

### 1. Modelimi Konceptual (Conceptual Model)

Modelimi konceptual përfaqëson entitetet kryesore dhe marrëdhëniet midis tyre në nivel të lartë.

#### Entitetet Kryesore:
- **Sensor** - Sensorët që matin të dhëna
- **Meter** - Matësit e energjisë
- **Customer** - Klientët që konsumojnë energji
- **Building** - Ndërtesat
- **Weather** - Të dhënat e motit
- **Anomaly** - Anomalitë e zbuluara
- **User** - Përdoruesit e sistemit
- **Notification** - Njoftimet

#### Marrëdhëniet:
- Sensor → Building (një sensor i përket një ndërtese)
- Meter → Customer (një matës i përket një klienti)
- Customer → Building (një klient mund të ketë shumë ndërtesa)
- Sensor → Anomaly (një sensor mund të ketë shumë anomalitë)
- Weather → Sensor (mot ndikon në sensorë)

---

### 2. Modelimi Logjik (Logical Model)

Modelimi logjik përcakton strukturën e detajuar e tabelave dhe marrëdhënieve.

#### Schema i Tabelave:

```sql
-- Sensor Data Domain
CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,  -- voltage, current, power, frequency
    value DECIMAL(10, 4) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    location GEOMETRY(POINT, 4326),
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meter Readings Domain
CREATE TABLE meter_readings (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    meter_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    reading DECIMAL(12, 4) NOT NULL,
    unit VARCHAR(10) DEFAULT 'kWh',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Domain
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Building Domain
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    building_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    location GEOMETRY(POINT, 4326),
    customer_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Weather Domain
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    pressure DECIMAL(7, 2),
    wind_speed DECIMAL(5, 2),
    weather_condition VARCHAR(50),
    location GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anomaly Detection Domain
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    sensor_id VARCHAR(100),
    building VARCHAR(50),
    floor INTEGER,
    electricity DOUBLE PRECISION,
    water DOUBLE PRECISION,
    anomaly_probability DOUBLE PRECISION,
    anomaly_type VARCHAR(50),  -- high_consumption, very_high, leak, moderate
    sensor_type VARCHAR(50),
    value DOUBLE PRECISION,
    location GEOMETRY(POINT, 4326),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Management Domain
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- admin, user, viewer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aggregates Domain (për analizë të shpejtë)
CREATE TABLE sensor_aggregates (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    avg_value DECIMAL(10, 4),
    min_value DECIMAL(10, 4),
    max_value DECIMAL(10, 4),
    count INTEGER,
    hour_bucket TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sensor_id, sensor_type, hour_bucket)
);

CREATE TABLE consumption_aggregates (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    total_consumption DECIMAL(12, 4),
    avg_consumption DECIMAL(12, 4),
    reading_count INTEGER,
    hour_bucket TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, hour_bucket)
);
```

---

### 3. Modelimi Fizik (Physical Model)

Modelimi fizik përfshin implementimin aktual në PostgreSQL me optimizime.

#### Indekset për Performancë:

```sql
-- Indekset për sensor_data
CREATE INDEX idx_sensor_id ON sensor_data(sensor_id);
CREATE INDEX idx_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_sensor_type ON sensor_data(sensor_type);
CREATE INDEX idx_location ON sensor_data USING GIST(location);

-- Indekset për meter_readings
CREATE INDEX idx_meter_id ON meter_readings(meter_id);
CREATE INDEX idx_customer_id ON meter_readings(customer_id);
CREATE INDEX idx_timestamp_meter ON meter_readings(timestamp);

-- Indekset për anomalies
CREATE INDEX idx_anomaly_timestamp ON anomalies(timestamp);
CREATE INDEX idx_anomaly_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomaly_sensor ON anomalies(sensor_id);

-- Indekset për aggregates
CREATE INDEX idx_aggregates_sensor ON sensor_aggregates(sensor_id, hour_bucket);
CREATE INDEX idx_aggregates_consumption ON consumption_aggregates(customer_id, hour_bucket);
```

#### Partitions (për të dhëna të mëdha):

```sql
-- Partitioning për sensor_data sipas muajit
CREATE TABLE sensor_data_2024_01 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE sensor_data_2024_02 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

---

## Data Domain Modeling

### Domain-et e Identifikuara:

1. **Sensor Domain**
   - Tabelat: `sensor_data`, `sensor_aggregates_realtime`
   - Përgjegjësi: Të dhënat e sensorëve, agregatat

2. **Meter Domain**
   - Tabelat: `meter_readings`, `consumption_aggregates_realtime`
   - Përgjegjësi: Leximet e matësve, konsumimi

3. **Weather Domain**
   - Tabelat: `weather_data`, `weather_aggregates_realtime`
   - Përgjegjësi: Të dhënat e motit

4. **Analytics Domain**
   - Tabelat: `anomalies`, `sensor_aggregates`
   - Përgjegjësi: Analiza, anomaly detection

5. **User Management Domain**
   - Tabelat: `users`, `roles`, `permissions`
   - Përgjegjësi: Autentikim, autorizim

6. **Notification Domain**
   - Tabelat: `notifications`, `alerts`
   - Përgjegjësi: Njoftimet dhe alertat

---

## ERD Diagram (Text Representation)

```
┌─────────────┐         ┌──────────────┐
│   Customer  │────────<│   Building   │
└─────────────┘   1:N   └──────────────┘
      │                      │
      │                      │ 1:N
      │                      │
      │ N:1                  ▼
      │              ┌──────────────┐
      │              │   Sensor     │
      │              └──────────────┘
      │                      │
      │                      │ 1:N
      │                      │
      │                      ▼
      │              ┌──────────────┐
      │              │ Sensor Data  │
      │              └──────────────┘
      │
      │ N:1
      │
      ▼
┌─────────────┐
│    Meter    │
└─────────────┘
      │
      │ 1:N
      │
      ▼
┌─────────────┐
│Meter Reading│
└─────────────┘

┌─────────────┐         ┌──────────────┐
│   Sensor    │────────>│   Anomaly    │
└─────────────┘   1:N   └──────────────┘

┌─────────────┐
│   Weather   │
└─────────────┘
      │
      │ 1:N
      │
      ▼
┌─────────────┐
│Weather Data │
└─────────────┘
```

---

## UML Class Diagram (Text Representation)

```
┌─────────────────────────────────────┐
│         SmartGridSystem             │
└─────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Sensor  │ │  Meter  │ │ Weather  │
│  Domain  │ │ Domain  │ │ Domain   │
└──────────┘ └──────────┘ └──────────┘
        │         │         │
        ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Analytics │ │Customer │ │  User    │
│ Domain   │ │ Domain  │ │ Domain   │
└──────────┘ └──────────┘ └──────────┘
```

---

## Hybrid Storage Models

### PostgreSQL (Relational):
- Të dhëna strukturuara: sensor_data, meter_readings, customers
- Agregatat: sensor_aggregates, consumption_aggregates
- Relationships: Foreign keys, joins

### MongoDB (NoSQL) - Për t'u shtuar:
- Audit logs: Logs të pa strukturuara
- Event history: Historiku i eventeve
- Metadata fleksibël: Metadata që ndryshon shpesh

### Cassandra (NoSQL) - Për t'u shtuar:
- Time-series data: Të dhëna historike për sensorët
- High write throughput: Shkrim i shpejtë i të dhënave

---

## Notes për Implementim

1. **PostGIS** përdoret për geospatial data (location fields)
2. **JSONB** përdoret për metadata fleksibël
3. **Partitioning** mund të përdoret për tabela të mëdha
4. **Indekset** janë optimizuar për queries më të shpeshta
5. **Domain separation** lehtëson shkallëzim dhe maintenance
