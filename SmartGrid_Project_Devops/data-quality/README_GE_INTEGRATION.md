# Great Expectations Integration me Airflow

## Përmbledhje

Ky dokument përshkruan integrimin e Great Expectations në Airflow DAG për data quality validation automatik.

## Komponentët

### 1. Great Expectations Helper Module
**Vendndodhja**: `data-quality/great_expectations_helper.py`

**Functions:**
- `validate_sensor_data_with_ge()` - Validon sensor data me Great Expectations
- `validate_meter_readings_with_ge()` - Validon meter readings me Great Expectations
- `generate_data_docs()` - Gjeneron HTML reports për validation results
- `get_data_from_postgres()` - Merr të dhëna nga PostgreSQL

### 2. Expectation Suites
**Vendndodhja**: `data-quality/great_expectations/expectations/`

**Suites:**
- `sensor_data_expectations.json` - Expectations për sensor data
- `meter_readings_expectations.json` - Expectations për meter readings

### 3. Airflow DAG Integration
**Vendndodhja**: `airflow/dags/smartgrid_etl.py`

**Changes:**
- `validate_data_quality()` function tani përdor Great Expectations
- Automatic validation për sensor data dhe meter readings
- Data Docs generation
- Validation results në XCom

## Expectation Suites

### Sensor Data Expectations

1. **Null Checks:**
   - `sensor_id` nuk duhet të jetë null
   - `sensor_type` nuk duhet të jetë null
   - `value` nuk duhet të jetë null
   - `timestamp` nuk duhet të jetë null

2. **Value Validation:**
   - `sensor_type` duhet të jetë në: ["voltage", "current", "power", "frequency"]
   - `value` duhet të jetë në rangun (0, 10000)

3. **Geographic Validation:**
   - `latitude` duhet të jetë në rangun (-90, 90)
   - `longitude` duhet të jetë në rangun (-180, 180)

4. **Type Validation:**
   - `timestamp` duhet të jetë datetime

### Meter Readings Expectations

1. **Null Checks:**
   - `meter_id` nuk duhet të jetë null
   - `customer_id` nuk duhet të jetë null
   - `reading` nuk duhet të jetë null
   - `timestamp` nuk duhet të jetë null

2. **Value Validation:**
   - `reading` duhet të jetë në rangun (0, 1000000) kWh
   - `unit` duhet të jetë "kWh"

3. **Business Logic:**
   - `reading` duhet të jetë në rritje (meter readings nuk duhet të zvogëlohen)

## Përdorimi

### Në Airflow DAG

```python
from great_expectations_helper import (
    validate_sensor_data_with_ge,
    validate_meter_readings_with_ge,
    generate_data_docs
)

def validate_data_quality(**context):
    # Validim për sensor data
    sensor_validation = validate_sensor_data_with_ge(
        query="SELECT * FROM sensor_data WHERE timestamp >= NOW() - INTERVAL '1 hour'",
        expectation_suite_name="sensor_data_suite"
    )
    
    # Validim për meter readings
    meter_validation = validate_meter_readings_with_ge(
        query="SELECT * FROM meter_readings WHERE timestamp >= NOW() - INTERVAL '1 hour'",
        expectation_suite_name="meter_readings_suite"
    )
    
    # Gjenero Data Docs
    sensor_docs = generate_data_docs(sensor_validation)
    meter_docs = generate_data_docs(meter_validation)
    
    return {
        'sensor_validation': sensor_validation,
        'meter_validation': meter_validation
    }
```

### Standalone Usage

```python
from great_expectations_helper import validate_sensor_data_with_ge

# Validim me default query
result = validate_sensor_data_with_ge()

# Validim me custom query
result = validate_sensor_data_with_ge(
    query="SELECT * FROM sensor_data WHERE sensor_type = 'voltage'"
)

print(f"Success: {result['success']}")
print(f"Quality Score: {result['data_quality_score']}%")
```

## Validation Results

### Structure

```python
{
    'success': True/False,
    'statistics': {
        'evaluated_expectations': 10,
        'successful_expectations': 9,
        'unsuccessful_expectations': 1,
        'success_percent': 90.0
    },
    'results': [...],  # Detailed results për çdo expectation
    'data_quality_score': 90.0
}
```

## Data Docs

Data Docs (HTML reports) gjenerohen automatikisht dhe ruhen në:
- `/tmp/ge_data_docs/sensor/validation_report.html`
- `/tmp/ge_data_docs/meter/validation_report.html`

Reports përmbajnë:
- Statistics (evaluated, successful, unsuccessful expectations)
- Success percentage
- Overall status (✅ Passed / ❌ Failed)

## Error Handling

### Fallback Mechanism

Nëse Great Expectations nuk është i disponueshëm, DAG përdor validim të thjeshtë:

```python
try:
    # Great Expectations validation
    result = validate_sensor_data_with_ge()
except ImportError:
    # Fallback në simple validation
    # ...
```

## Integration me Airflow

### XCom Data

Validation results ruhen në XCom dhe mund të përdoren nga task-et e tjera:

```python
# Në task-in tjetër
sensor_validation = context['ti'].xcom_pull(key='sensor_validation', task_ids='validate_data_quality')
sensor_docs_path = context['ti'].xcom_pull(key='sensor_docs_path', task_ids='validate_data_quality')
```

### Task Dependencies

```
extract_task >> transform_task >> validate_task >> load_task
```

`validate_task` tani përdor Great Expectations dhe do të dështojë nëse validation fails.

## Status

**Great Expectations Integration: 100% Implementuar** ✅

**Çfarë është implementuar:**
- ✅ Great Expectations helper module
- ✅ Expectation suites për sensor data dhe meter readings
- ✅ Integration në Airflow DAG
- ✅ Data Docs generation
- ✅ Error handling dhe fallback mechanism
- ✅ XCom integration për results sharing

## Hapat e Ardhshëm (Opsionale)

1. **Great Expectations Data Context** - Krijo full Data Context me datasources
2. **Checkpoints** - Implemento Checkpoints për automated validation
3. **Validation Actions** - Shto actions për alerting dhe notifications
4. **Data Docs në S3/GCS** - Store Data Docs në cloud storage
5. **Great Expectations Cloud** - Integro me Great Expectations Cloud për collaboration

