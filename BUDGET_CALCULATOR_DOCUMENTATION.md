# Real-Time Energy Budget Calculator

## Përmbledhje

Kalkulator i buxhetit në kohë reale për energji që lejon përdoruesit të llogarisin sa kilowatt-orë (kWh) mund të konsumojnë për një shumë në Euro, ose anasjelltas. Kalkulatori përdor çmime dinamike të energjisë që mund të ndryshojnë me kalimin e kohës (peak vs off-peak hours ose përditësime ditore).

---

## ✅ Features

### 1. Forward Calculation (€ → kWh)
- **Input**: Shuma në Euro (€)
- **Output**: Sa kWh mund të konsumohen për atë shumë
- **Formula**: `kWh = Shuma (€) ÷ Çmim (€/kWh)`

### 2. Reverse Calculation (kWh → €)
- **Input**: Konsum në kilowatt-orë (kWh)
- **Output**: Kostoja në Euro (€)
- **Formula**: `Kosto (€) = kWh × Çmim (€/kWh)`

### 3. Dynamic Pricing
- **Peak Hours Detection**: Automatikisht detekton orët e pikut (8-10 AM, 6-8 PM)
- **Peak Hour Multiplier**: 15% më i lartë gjatë peak hours
- **Real-time Updates**: Çmimet përditësohen automatikisht çdo 60 sekonda

### 4. Tariff Information
- **Active Tariff**: Shfaq tarifën aktive (residential, commercial, industrial)
- **Validity Period**: Tregon për sa kohë është i vlefshëm çmimi (zakonisht 24 orë)
- **Price Source**: Tregon burimin e çmimit (KOSTT, ERO, default)

### 5. Transparency & Warnings
- **Price Change Warning**: Paralajmëron që çmimet mund të ndryshojnë në të ardhmen
- **Peak Hour Notice**: Informon përdoruesin kur është peak hour dhe jep këshilla për kursim
- **Validity Info**: Tregon për sa kohë është i vlefshëm çmimi aktual

---

## 🔧 API Endpoint

### `/api/v1/analytics/budget-calculator`

**Method**: `GET`

**Query Parameters**:
- `amount_eur` (float): Shuma në Euro për forward calculation (€ → kWh)
- `amount_kwh` (float): Shuma në kWh për reverse calculation (kWh → €)
- `tariff_type` (string): `residential`, `commercial`, `industrial` (default: `residential`)
- `include_peak_hours` (boolean): `true`/`false` (default: `true`) - përfshi peak hour pricing

**Examples**:

1. **Forward Calculation** (€ → kWh):
```bash
GET /api/v1/analytics/budget-calculator?amount_eur=10
```

**Response**:
```json
{
  "status": "success",
  "calculation_type": "forward",
  "input": {
    "amount_eur": 10.0,
    "currency": "EUR"
  },
  "output": {
    "kwh": 117.65,
    "mwh": null
  },
  "calculation": {
    "formula": "10.0 € ÷ 0.0850 €/kWh = 117.65 kWh",
    "price_per_kwh": 0.085
  },
  "price_info": {
    "price_eur_per_kwh": 0.085,
    "base_price_eur_per_kwh": 0.085,
    "is_peak_hour": false,
    "peak_multiplier": 1.0,
    "current_hour": 14,
    "tariff_type": "residential",
    "price_source": "default",
    "price_timestamp": "2024-01-07T14:30:00",
    "validity_until": "2024-01-08T14:30:00",
    "currency": "EUR"
  },
  "validity": {
    "valid_until": "2024-01-08T14:30:00",
    "valid_for_hours": 24.0,
    "note": "Price may change after this period. Recalculate for accurate results."
  },
  "calculated_at": "2024-01-07T14:30:00",
  "disclaimer": "Prices may change over time. This calculation is valid for the current moment only."
}
```

2. **Reverse Calculation** (kWh → €):
```bash
GET /api/v1/analytics/budget-calculator?amount_kwh=100
```

**Response**:
```json
{
  "status": "success",
  "calculation_type": "reverse",
  "input": {
    "kwh": 100.0,
    "mwh": null
  },
  "output": {
    "amount_eur": 8.50,
    "currency": "EUR"
  },
  "calculation": {
    "formula": "100.0 kWh × 0.0850 €/kWh = 8.50 €",
    "price_per_kwh": 0.085
  },
  "price_info": {
    "price_eur_per_kwh": 0.085,
    "base_price_eur_per_kwh": 0.085,
    "is_peak_hour": false,
    "peak_multiplier": 1.0,
    "current_hour": 14,
    "tariff_type": "residential",
    "price_source": "default",
    "price_timestamp": "2024-01-07T14:30:00",
    "validity_until": "2024-01-08T14:30:00",
    "currency": "EUR"
  },
  "validity": {
    "valid_until": "2024-01-08T14:30:00",
    "valid_for_hours": 24.0,
    "note": "Price may change after this period. Recalculate for accurate results."
  },
  "calculated_at": "2024-01-07T14:30:00",
  "disclaimer": "Prices may change over time. This calculation is valid for the current moment only."
}
```

3. **Peak Hour Example** (8-10 AM, 6-8 PM):
```bash
GET /api/v1/analytics/budget-calculator?amount_eur=10&include_peak_hours=true
```

**Response** (nëse është peak hour):
```json
{
  "status": "success",
  "calculation_type": "forward",
  "input": {
    "amount_eur": 10.0,
    "currency": "EUR"
  },
  "output": {
    "kwh": 102.30,
    "mwh": null
  },
  "price_info": {
    "price_eur_per_kwh": 0.0978,
    "base_price_eur_per_kwh": 0.085,
    "is_peak_hour": true,
    "peak_multiplier": 1.15,
    "current_hour": 9
  },
  "peak_hour_notice": {
    "message": "Current time is peak hour (9:00). Price includes 1.15x multiplier.",
    "base_price": 0.085,
    "current_price": 0.0978,
    "savings_tip": "Consider using energy during off-peak hours (outside 9:00) to save 13.1%"
  }
}
```

---

## 🎨 Frontend Interface

### URL
```
http://localhost:8080/budget-calculator
```

### Features
- **Tab-based Interface**: Switch midis € → kWh dhe kWh → €
- **Real-time Calculation**: Llogaritje e menjëhershme kur përdoruesi shkruan
- **Auto-refresh**: Përditësohet automatikisht çdo 60 sekonda për çmime të reja
- **Visual Feedback**: 
  - Gradient result card
  - Peak hour warnings
  - Validity period display
  - Price breakdown

### UI Components
1. **Input Fields**: Me ikona (€ dhe ⚡)
2. **Calculate Button**: Me hover effects
3. **Result Card**: Me animacion slide-in
4. **Price Info Panel**: Detaje për çmimin aktual
5. **Peak Hour Notice**: Paralajmërim dhe këshilla për kursim
6. **Validity Info**: Koha e vlefshmërisë së çmimit
7. **Disclaimer**: Paralajmërim për ndryshimet e çmimeve

---

## ⚙️ Configuration

### Peak Hours
- **Default Peak Hours**: 8-10 AM dhe 6-8 PM
- **Peak Multiplier**: 1.15 (15% më i lartë)
- **Configurable**: Mund të ndryshohet në `get_energy_price_eur_per_kwh()`

### Default Price
- **Kosovo**: 0.085 €/kWh (mesatare)
- **Fallback**: Përdoret nëse price service nuk është i disponueshëm

### Cache
- **TTL**: 60 sekonda (real-time updates)
- **Purpose**: Redukton API calls, por mban çmimet aktuale

---

## 🔄 Integration

### Backend
- **Service**: Analytics Service (`smartgrid-analytics:5002`)
- **Endpoint**: `/api/v1/analytics/budget-calculator`
- **Dependencies**: Kosovo Price Collector Service

### Frontend
- **Route**: `/budget-calculator`
- **Template**: `templates/budget-calculator.html`
- **Proxy**: Frontend service proxy për analytics service

### Navigation
- **Link**: Shtuar në navigation bar si "💰 Buxheti"
- **Accessible**: Nga çdo faqe e dashboard-it

---

## 📊 Use Cases

1. **Budget Planning**: "Sa kWh mund të konsumoj me 50 €?"
2. **Cost Estimation**: "Sa do të më kushtojë 200 kWh?"
3. **Peak Hour Awareness**: "A duhet të pres deri në off-peak hours?"
4. **Real-time Decision Making**: "Mund të përdor energji tani ose duhet të pres?"

---

## 🚀 Future Enhancements

- [ ] Historical price trends në calculator
- [ ] Comparison midis peak dhe off-peak pricing
- [ ] Savings calculator (sa mund të kursesh duke shmangur peak hours)
- [ ] Multi-currency support
- [ ] Export results si PDF/CSV
- [ ] Mobile app integration

---

## ✅ Status

- ✅ Backend endpoint implementuar
- ✅ Peak/off-peak price detection
- ✅ Frontend calculator component
- ✅ Real-time updates (60s refresh)
- ✅ Tariff validity period display
- ✅ Price change warnings
- ✅ Navigation integration
- ✅ Documentation complete

---

**Data e Implementimit**: 2024-01-07
**Version**: 1.0

