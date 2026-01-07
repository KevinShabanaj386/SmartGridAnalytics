# Frontend Structure - Reorganized

## 📁 Struktura e Re e File-ave

```
frontend/
├── app.py                          # Backend Flask application
├── dockerfile                      # Docker image
├── requirements.txt                # Dependencies
├── README.md                       # Documentation
├── FRONTEND_STRUCTURE.md          # This file
│
├── static/                         # Static files
│   ├── css/                        # Stylesheets
│   │   ├── modern-style.css       # Main modern styles
│   │   ├── style.css              # Legacy styles
│   │   └── kosovo.css             # Kosovo-specific styles
│   │
│   └── js/                         # JavaScript files
│       ├── dashboard.js           # Dashboard functionality
│       ├── kosovo-dashboard.js    # Kosovo main dashboard
│       ├── kosovo-weather.js      # Weather data visualization
│       ├── kosovo-prices.js       # Prices visualization
│       └── kosovo-consumption.js # Consumption visualization
│
└── templates/                      # HTML templates
    ├── index.html                 # Main dashboard
    ├── dashboard.html             # Detailed statistics
    ├── analytics.html             # Analytics page
    ├── sensors.html               # Sensors page
    │
    └── kosovo/                    # Kosovo data pages
        ├── dashboard.html         # Kosovo overview
        ├── weather.html           # Weather data
        ├── prices.html            # Energy prices
        └── consumption.html       # Consumption data
```

## 🎯 Features të Reja

### Kosovo Data Integration:
- ✅ Kosovo Dashboard (`/kosovo`) - Overview i të gjitha të dhënave
- ✅ Weather Data (`/kosovo/weather`) - Të dhëna moti për 5 qytete
- ✅ Energy Prices (`/kosovo/prices`) - Çmimet nga KOSTT, ERO
- ✅ Consumption (`/kosovo/consumption`) - Konsumi rajonal dhe historik

### API Endpoints të Reja:
- `/api/kosovo/weather` - Weather data
- `/api/kosovo/weather/cities` - Lista e qyteteve
- `/api/kosovo/prices` - Energy prices
- `/api/kosovo/consumption` - Consumption data
- `/api/kosovo/consumption/historical` - Historical consumption

## 🔧 Organizimi

### CSS Files:
- `css/modern-style.css` - Main styles (moved from root)
- `css/style.css` - Legacy styles (moved from root)
- `css/kosovo.css` - Kosovo-specific styles (new)

### JavaScript Files:
- `js/dashboard.js` - Main dashboard (moved from root)
- `js/kosovo-*.js` - Kosovo data visualization (new)

### Templates:
- Main pages in root `templates/`
- Kosovo pages in `templates/kosovo/` subdirectory

## 🚀 Benefits

1. **Better Organization**: CSS dhe JS files janë të organizuara në folders
2. **Kosovo Integration**: Të gjitha të dhënat e Kosovës janë të integruara
3. **Modular Structure**: Çdo feature ka file-at e veta
4. **Easy Maintenance**: Strukturë e qartë për shtim features të reja
