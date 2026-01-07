# Llogaritja e Kostos së Energjisë në Euro

## Përmbledhje

Tani të gjitha endpoint-et e konsumit kthejnë jo vetëm konsumin në kilowat (kW/MW), por edhe koston në Euro (€) bazuar në çmimet aktuale të energjisë nga Kosovo ose shtetet e tjera.

---

## ✅ Endpoint-et e Përditësuara

### 1. Daily Trends (`/api/v1/analytics/consumption/trends`)

**Response i ri**:
```json
{
  "status": "success",
  "trends": [
    {
      "date": "2024-01-07",
      "total_consumption_kwh": 15000.5,
      "total_consumption_mw": 15.0,
      "cost_eur": 1275.04,
      "avg_reading": 125.5,
      "reading_count": 120
    }
  ],
  "period_days": 30,
  "price_eur_per_kwh": 0.085,
  "currency": "EUR"
}
```

### 2. Monthly Trends (`/api/v1/analytics/consumption/trends/monthly`)

**Response i ri**:
```json
{
  "status": "success",
  "trends": [
    {
      "month": "2024-01-01",
      "total_consumption_kwh": 450000.0,
      "total_consumption_mw": 450.0,
      "cost_eur": 38250.0,
      "avg_reading": 150.0,
      "min_consumption": 100.0,
      "max_consumption": 200.0,
      "reading_count": 3000
    }
  ],
  "period_months": 12,
  "price_eur_per_kwh": 0.085,
  "currency": "EUR"
}
```

### 3. Seasonal Trends (`/api/v1/analytics/consumption/trends/seasonal`)

**Response i ri**:
```json
{
  "status": "success",
  "trends": [
    {
      "season": "Winter",
      "year": 2024,
      "total_consumption_kwh": 1350000.0,
      "total_consumption_mw": 1350.0,
      "cost_eur": 114750.0,
      "avg_reading": 150.0,
      "reading_count": 9000
    }
  ],
  "period_years": 2,
  "price_eur_per_kwh": 0.085,
  "currency": "EUR"
}
```

### 4. Year Comparison (`/api/v1/analytics/consumption/year-comparison`)

**Response i ri**:
```json
{
  "status": "success",
  "comparisons": [
    {
      "year": 2023,
      "total_consumption_kwh": 5400000.0,
      "total_consumption_mw": 5400.0,
      "cost_eur": 459000.0,
      "change_from_previous_year_percent": null,
      "cost_change_from_previous_year_percent": null
    },
    {
      "year": 2024,
      "total_consumption_kwh": 5800000.0,
      "total_consumption_mw": 5800.0,
      "cost_eur": 493000.0,
      "change_from_previous_year_percent": 7.41,
      "cost_change_from_previous_year_percent": 7.41
    }
  ],
  "years_compared": 2,
  "price_eur_per_kwh": 0.085,
  "currency": "EUR"
}
```

### 5. Growth Analysis (`/api/v1/analytics/consumption/growth-analysis`)

**Response i ri**:
```json
{
  "status": "success",
  "trend": "increasing",
  "trend_description": "Konsumi po rritet me 5.25%",
  "growth_percent": 5.25,
  "cost_growth_percent": 5.25,
  "daily_growth_rate_percent": 0.0144,
  "daily_cost_growth_rate_percent": 0.0144,
  "first_half_avg_consumption_kwh": 50000.0,
  "second_half_avg_consumption_kwh": 52625.0,
  "first_half_avg_cost_eur": 4250.0,
  "second_half_avg_cost_eur": 4473.13,
  "period_days": 365,
  "price_eur_per_kwh": 0.085,
  "currency": "EUR"
}
```

---

## 🔧 Si Funksionon

### 1. Marrja e Çmimit të Energjisë

Sistemi përpiqet të marrë çmimin aktual nga:
1. **Kosovo Energy Price Collector Service** (port 5008)
2. **Environment variable**: `KOSOVO_PRICE_SERVICE_URL`
3. **Fallback**: Default price 0.085 €/kWh (mesatare për Kosovën)

**Funksioni**: `get_energy_price_eur_per_kwh(tariff_type='residential')`

### 2. Llogaritja e Kostos

**Formula**: `Kosto (€) = Konsum (kWh) × Çmim (€/kWh)`

**Funksioni**: `calculate_cost_eur(consumption_kwh, price_eur_per_kwh)`

- Nëse konsumi është në MW, konvertohet automatikisht në kWh (MW × 1000)
- Rezultati rrumbullakoset në 2 shifra pas presjes

---

## 📊 Përdorimi në Dashboard

### Shembull: Shfaqja e Konsumit dhe Kostos

```javascript
// Merr të dhënat e trendeve
const response = await fetch('/api/v1/analytics/consumption/trends?days=30');
const data = await response.json();

// Krijo chart me dy aksa (dual-axis)
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: data.trends.map(t => t.date),
    datasets: [
      {
        label: 'Konsum (kWh)',
        data: data.trends.map(t => t.total_consumption_kwh),
        yAxisID: 'y',
        borderColor: 'rgb(37, 99, 235)',
        backgroundColor: 'rgba(37, 99, 235, 0.1)'
      },
      {
        label: 'Kosto (€)',
        data: data.trends.map(t => t.cost_eur),
        yAxisID: 'y1',
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)'
      }
    ]
  },
  options: {
    scales: {
      y: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: 'Konsum (kWh)' }
      },
      y1: {
        type: 'linear',
        position: 'right',
        title: { display: true, text: 'Kosto (€)' },
        grid: { drawOnChartArea: false }
      }
    }
  }
});
```

---

## 🌍 Çmimet e Energjisë për Shtete të Ndryshme

Sistemi mund të integrohet me çmime nga shtete të ndryshme:

### Kosovo
- **Default**: 0.085 €/kWh
- **Source**: KOSTT, ERO, KEK
- **Tariff types**: residential, commercial, industrial

### Shtetet e tjera
Mund të shtohen në `get_energy_price_eur_per_kwh()`:
- Shqipëria: ~0.10 €/kWh
- Maqedonia e Veriut: ~0.08 €/kWh
- Serbia: ~0.09 €/kWh
- etj.

---

## 🔄 Përditësimi i Çmimeve

Çmimet përditësohen automatikisht:
- **Kosovo Price Collector**: Çdo 24 orë (default)
- **Cache**: 5 minuta për të reduktuar API calls
- **Fallback**: Përdoret default price nëse service nuk është i disponueshëm

---

## 📝 Shënime

1. **Konvertimi i njësive**: 
   - Nëse konsumi është > 1000, supozohet që është në MW dhe konvertohet në kWh
   - Përndryshe, supozohet që është tashmë në kWh

2. **Çmimi default**: 
   - 0.085 €/kWh për Kosovën (mesatare)
   - Mund të ndryshohet në `get_energy_price_eur_per_kwh()`

3. **Currency**: 
   - Tani përdoret vetëm Euro (EUR)
   - Mund të shtohen currency të tjera në të ardhmen

---

## ✅ Statusi

- ✅ Daily trends me kosto
- ✅ Monthly trends me kosto
- ✅ Seasonal trends me kosto
- ✅ Year comparison me kosto
- ✅ Growth analysis me kosto
- ⏳ Dashboard visualization (në proces)

---

**Data e Implementimit**: 2024-01-07
**Version**: 1.0

