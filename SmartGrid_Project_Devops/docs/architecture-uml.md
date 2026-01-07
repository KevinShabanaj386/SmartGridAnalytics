# Architecture UML Diagrams

## System Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Smart Grid Analytics                      │
│                      System Architecture                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │      │  API Gateway │      │   Services   │
│   (React)    │─────>│  (Flask)     │─────>│  Layer       │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Data         │      │ Data         │      │ Analytics    │
│ Ingestion    │      │ Processing    │      │ Service      │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │    Kafka      │
                    │  (Event Bus)  │
                    └──────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ PostgreSQL   │      │   MongoDB    │      │  Cassandra   │
│ (Relational) │      │  (NoSQL)     │      │ (Time-Series)│
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## Microservices Architecture

### Service Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│  - Routing                                                   │
│  - Load Balancing                                            │
│  - Circuit Breaker                                           │
│  - Service Discovery (Consul)                               │
└─────────────────────────────────────────────────────────────┘
        │           │           │           │           │
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Data    │ │  Data    │ │Analytics │ │Notification│ │  User   │
│Ingestion │ │Processing│ │ Service  │ │  Service  │ │Management│
│ Service  │ │ Service  │ │          │ │           │ │ Service  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
     │            │            │            │            │
     │            │            │            │            │
     └────────────┴────────────┴────────────┴────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Kafka Topics   │
                    │  - sensor-data   │
                    │  - meter-readings│
                    │  - alerts        │
                    │  - notifications │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ PostgreSQL   │      │   Spark       │      │  Schema      │
│              │      │  Streaming    │      │  Registry    │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## Event-Driven Architecture Flow

```
┌──────────────┐
│   Sensors    │
│   (IoT)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│   Data       │─────>│    Kafka     │
│  Ingestion   │      │   Producer   │
│   Service    │      └──────┬───────┘
└──────────────┘             │
                             │ Events
                             ▼
                    ┌──────────────┐
                    │   Kafka      │
                    │   Topics      │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Data       │  │   Spark      │  │ Notification│
│ Processing   │  │  Streaming    │  │   Service   │
│  Consumer    │  │  Consumer    │  │  Consumer   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ PostgreSQL   │  │   Send       │
│              │  │ (Aggregates) │  │ Notifications│
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Data Flow Diagram

### Real-time Processing Flow

```
┌──────────────┐
│  Sensor Data │
│  (Stream)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Kafka      │
│  (Topic)     │
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   Spark      │  │   Data       │
│  Streaming   │  │ Processing   │
│  (Real-time) │  │  (Batch)     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Aggregates   │  │ Raw Data     │
│ (PostgreSQL) │  │ (PostgreSQL) │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌──────────────┐
        │  Analytics   │
        │   Service    │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   Grafana    │
        │  Dashboards  │
        └──────────────┘
```

---

## Deployment Architecture

### Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Namespace: smartgrid                     │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │   API    │  │   Data   │  │ Analytics│          │  │
│  │  │ Gateway  │  │Ingestion │  │ Service  │          │  │
│  │  │ (3 pods) │  │ (3 pods) │  │ (2 pods) │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │   Data   │  │Notification│ │   User   │          │  │
│  │  │Processing│  │  Service  │  │Management│          │  │
│  │  │ (2 pods) │  │ (2 pods) │  │ (2 pods) │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │  Kafka   │  │PostgreSQL│  │  Redis   │          │  │
│  │  │ Cluster  │  │ (Stateful)│ │ (Cache)  │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │Prometheus│  │ Grafana  │  │  Jaeger  │          │  │
│  │  │(Metrics) │  │(Dashboards)│ │(Tracing)│          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Zero Trust Model

```
┌─────────────────────────────────────────────────────────────┐
│                    External Request                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  API Gateway    │
                    │  (Auth Check)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  JWT Validation │
                    │  (User Mgmt)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  RBAC Check     │
                    │  (Permissions)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Service        │
                    │  (mTLS)         │
                    └─────────────────┘
```

---

## Notes

- Të gjitha diagramet janë në format tekst për dokumentim
- Mund të konvertohen në format vizual (PNG/SVG) me mjete si PlantUML, Mermaid, ose draw.io
- Diagramet përfaqësojnë arkitekturën aktuale dhe të planifikuar të sistemit
