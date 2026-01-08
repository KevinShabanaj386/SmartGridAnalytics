# Frontend Web Application - Smart Grid Analytics

## Përmbledhje

Frontend web application për vizualizim dhe menaxhim të sistemit Smart Grid Analytics me integrim të të dhënave për Kosovo, Albania, Serbia dhe Greece.

## Karakteristika

- ✅ Dashboard interaktive me grafikë
- ✅ Statistikat e sensorëve në kohë reale
- ✅ Parashikim ngarkese me ML models
- ✅ Zbulim anomalish
- ✅ Login dhe autentikim
- ✅ Design modern dhe responsive
- ✅ Të dhëna për shtete të ndryshme (Kosovo, Albania, Serbia, Greece)

## Struktura

```
frontend/
├── app.py                          # Flask backend application
├── dockerfile                      # Docker image
├── requirements.txt                # Python dependencies
│
├── static/                         # Static files
│   ├── css/                        # Stylesheets
│   │   ├── modern-style.css       # Main modern styles
│   │   ├── style.css              # Legacy styles
│   │   └── kosovo.css             # Country-specific styles
│   │
│   └── js/                         # JavaScript files
│       ├── dashboard.js           # Main dashboard
│       ├── dashboard-main.js      # Dashboard functionality
│       ├── kosovo-*.js            # Kosovo data visualization
│       ├── albania-*.js           # Albania data visualization
│       ├── serbia-*.js            # Serbia data visualization
│       └── greece-*.js           # Greece data visualization
│
└── templates/                      # HTML templates
    ├── index.html                 # Main dashboard
    ├── dashboard.html             # Detailed statistics
    ├── analytics.html             # Analytics page
    ├── sensors.html               # Sensors page
    ├── budget-calculator.html     # Budget calculator
    │
    ├── kosovo/                    # Kosovo data pages
    │   ├── dashboard.html         # Kosovo overview
    │   ├── weather.html           # Weather data
    │   ├── prices.html            # Energy prices
    │   └── consumption.html       # Consumption data
    │
    ├── albania/                   # Albania data pages
    ├── serbia/                    # Serbia data pages
    └── greece/                    # Greece data pages
```

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

## Faqet e Disponueshme

### Faqet Kryesore
- `/` - Dashboard kryesor
- `/dashboard` - Statistikat e detajuara
- `/analytics` - Analiza të avancuara
- `/sensors` - Menaxhimi i sensorëve
- `/budget-calculator` - Kalkulator i buxhetit për energji

### Të Dhëna për Shtete
- `/kosovo` - Dashboard për Kosovën
- `/kosovo/weather` - Të dhëna moti
- `/kosovo/prices` - Çmimet e energjisë
- `/kosovo/consumption` - Konsumi i energjisë

- `/albania` - Dashboard për Shqipërinë
- `/serbia` - Dashboard për Serbinë
- `/greece` - Dashboard për Greqinë

(Çdo shtet ka të njëjtat nënfaqe: weather, prices, consumption)

## API Endpoints

Frontend komunikon me API Gateway dhe services përmes endpoints:

### Authentication
- `/api/login` - Login
- `/api/logout` - Logout

### Analytics
- `/api/sensor-stats` - Statistikat e sensorëve
- `/api/load-forecast` - Parashikim ngarkese
- `/api/anomalies` - Zbulim anomalish
- `/api/v1/analytics/budget-calculator` - Budget calculator

### Country Data
- `/api/kosovo/weather` - Weather data për Kosovën
- `/api/kosovo/prices` - Energy prices për Kosovën
- `/api/kosovo/consumption` - Consumption data për Kosovën
- `/api/albania/*` - Të dhëna për Shqipërinë
- `/api/serbia/*` - Të dhëna për Serbinë
- `/api/greece/*` - Të dhëna për Greqinë

## Konfigurimi

### Environment Variables

```yaml
API_GATEWAY_URL=http://api-gateway:5000
ANALYTICS_SERVICE_URL=http://analytics-service:5002
KOSOVO_WEATHER_URL=http://kosovo-weather-collector:5007
KOSOVO_PRICE_URL=http://kosovo-energy-price-collector:5008
KOSOVO_CONSUMPTION_URL=http://kosovo-consumption-collector:5009
```

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

### Të dhënat e shteteve nuk shfaqen
1. Kontrolloni që API endpoints janë të disponueshme
2. Verifikoni që services janë running
3. Shikoni browser console për API errors

## Rebuild Container

Nëse bëni ndryshime në `app.py` ose templates, duhet të rebuild container:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose build frontend
docker-compose up -d frontend
```

**Note**: Templates dhe static files janë volume-mounted, kështu që ndryshimet në to nuk kërkojnë rebuild.
