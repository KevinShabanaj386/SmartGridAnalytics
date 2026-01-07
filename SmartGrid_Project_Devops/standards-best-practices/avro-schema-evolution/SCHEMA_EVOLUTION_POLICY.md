# Avro Schema Evolution Policy

## Përmbledhje

Kjo policy përcakton rregullat për schema evolution në Smart Grid Analytics, duke siguruar backward dhe forward compatibility.

## Schema Evolution Rules

### Backward Compatibility

**New schema can read data written with old schema.**

#### Allowed Changes (Backward Compatible)

1. **Add Fields** (with defaults)
   ```json
   // Old schema
   {"name": "sensor_id", "type": "string"}
   
   // New schema (backward compatible)
   {
     "name": "sensor_id", "type": "string"
   },
   {
     "name": "sensor_name", "type": "string", "default": ""
   }
   ```

2. **Remove Fields** (if optional or has default)
   ```json
   // Old schema
   {
     "name": "metadata",
     "type": ["null", "string"],
     "default": null
   }
   
   // New schema (backward compatible - field removed)
   ```

3. **Change Field Order** (order doesn't matter in Avro)

#### Not Allowed (Breaking Changes)

1. **Remove Required Fields**
2. **Change Field Types** (without union)
3. **Rename Fields** (without alias)
4. **Add Required Fields** (without default)

### Forward Compatibility

**Old schema can read data written with new schema.**

#### Allowed Changes (Forward Compatible)

1. **Remove Fields** (old readers ignore new fields)
2. **Add Optional Fields** (old readers ignore)

#### Not Allowed (Breaking Changes)

1. **Add Required Fields**
2. **Change Field Types**

## Schema Versioning

### Version Format

```
<schema-name>-v<major>.<minor>.<patch>.avsc
```

- **MAJOR**: Breaking changes
- **MINOR**: Backward compatible additions
- **PATCH**: Bug fixes

### Examples

```
sensor_data-v1.0.0.avsc  # Initial version
sensor_data-v1.1.0.avsc  # Added optional field (backward compatible)
sensor_data-v2.0.0.avsc  # Breaking change (removed required field)
```

## Schema Registry Integration

### Schema Registration

```python
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

# Register schema
schema_registry_client = SchemaRegistryClient({'url': 'http://schema-registry:8081'})
schema_registry_client.register_schema(
    subject_name='sensor_data-value',
    schema=schema_str,
    schema_type='AVRO'
)
```

### Compatibility Modes

1. **BACKWARD**: New schema can read old data
2. **FORWARD**: Old schema can read new data
3. **FULL**: Both backward and forward compatible
4. **NONE**: No compatibility checks

### Recommended: FULL Compatibility

```python
# Set compatibility mode
schema_registry_client.set_compatibility(
    subject_name='sensor_data-value',
    compatibility='FULL'
)
```

## Migration Strategy

### Gradual Migration

1. **Add New Field** (with default)
   ```json
   {
     "name": "new_field",
     "type": "string",
     "default": ""
   }
   ```

2. **Update Producers** (start writing new field)

3. **Update Consumers** (start reading new field)

4. **Remove Old Field** (after all consumers updated)

### Breaking Changes

1. **Create New Schema Version** (v2.0.0)
2. **Maintain Both Versions** (during migration)
3. **Update Producers** (to v2.0.0)
4. **Update Consumers** (to v2.0.0)
5. **Deprecate Old Version** (after migration)

## Best Practices

1. **Always Provide Defaults**: For new optional fields
2. **Use Unions**: For type changes
3. **Use Aliases**: For field renames
4. **Test Compatibility**: Before deploying
5. **Document Changes**: In CHANGELOG
6. **Version Schemas**: Use semantic versioning
7. **Monitor Compatibility**: Check Schema Registry

## Examples

### Example 1: Adding Optional Field (Backward Compatible)

**Old Schema (v1.0.0)**:
```json
{
  "type": "record",
  "name": "SensorData",
  "fields": [
    {"name": "sensor_id", "type": "string"},
    {"name": "value", "type": "double"}
  ]
}
```

**New Schema (v1.1.0)**:
```json
{
  "type": "record",
  "name": "SensorData",
  "fields": [
    {"name": "sensor_id", "type": "string"},
    {"name": "value", "type": "double"},
    {"name": "metadata", "type": ["null", "string"], "default": null}
  ]
}
```

✅ **Backward Compatible**: Old readers ignore new field

### Example 2: Type Change with Union (Compatible)

**Old Schema**:
```json
{"name": "value", "type": "double"}
```

**New Schema**:
```json
{"name": "value", "type": ["double", "int"]}
```

✅ **Compatible**: Union allows both types

### Example 3: Field Rename with Alias (Compatible)

**Old Schema**:
```json
{"name": "sensor_id", "type": "string"}
```

**New Schema**:
```json
{
  "name": "device_id",
  "type": "string",
  "aliases": ["sensor_id"]
}
```

✅ **Compatible**: Alias allows old name

## Testing Schema Evolution

### Compatibility Tests

```python
import avro.schema
from avro.compatibility import SchemaCompatibilityChecker

# Load schemas
old_schema = avro.schema.parse(open("sensor_data-v1.0.0.avsc").read())
new_schema = avro.schema.parse(open("sensor_data-v1.1.0.avsc").read())

# Check compatibility
checker = SchemaCompatibilityChecker()
result = checker.check_compatibility(old_schema, new_schema)

if result.compatible:
    print("Schemas are compatible")
else:
    print(f"Incompatible: {result.messages}")
```

## Schema Registry Best Practices

1. **Use Schema Registry**: Centralized schema management
2. **Enable Compatibility Checks**: Prevent breaking changes
3. **Version Schemas**: Track schema versions
4. **Monitor Changes**: Alert on schema changes
5. **Document Evolution**: Document all changes

