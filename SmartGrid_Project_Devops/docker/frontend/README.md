# Frontend Web Application - Smart Grid Analytics

## Përmbledhje

Frontend web application për vizualizim dhe menaxhim të sistemit Smart Grid Analytics.

## Karakteristika

- ✅ Dashboard interaktive me grafikë
- ✅ Statistikat e sensorëve në kohë reale
- ✅ Parashikim ngarkese me ML models
- ✅ Zbulim anomalish
- ✅ Login dhe autentikim
- ✅ Design modern dhe responsive

## Përdorimi

### Nisja

Frontend niset automatikisht me docker-compose:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d frontend
```

### Hapja në Shfletues

**URL**: http://localhost:8080

### Login

- **Username**: `admin`
- **Password**: `admin123`

## Struktura

```
frontend/
├── app.py              # Flask backend
├── templates/          # HTML templates
│   ├── index.html      # Dashboard kryesor
│   └── dashboard.html  # Statistikat
├── static/             # CSS dhe JavaScript
│   ├── style.css
│   └── dashboard.js
└── requirements.txt    # Python dependencies
```

## API Endpoints

Frontend komunikon me API Gateway përmes endpoints:

- `/api/login` - Login
- `/api/sensor-stats` - Statistikat e sensorëve
- `/api/load-forecast` - Parashikim ngarkese
- `/api/anomalies` - Zbulim anomalish
- `/api/ingest-sensor` - Dërgim të dhënash

## Troubleshooting

### Frontend nuk hapet

1. Kontrolloni që porti 8080 është i lirë
2. Shikoni logs: `docker-compose logs frontend`
3. Verifikoni që API Gateway është në funksion

### Login nuk funksionon

1. Kontrolloni që User Management Service është në funksion
2. Verifikoni kredencialet
3. Shikoni console në shfletues për errors

### Grafikët nuk shfaqen

1. Kontrolloni që Analytics Service është në funksion
2. Verifikoni që ka të dhëna në database
3. Shikoni network tab në browser developer tools

