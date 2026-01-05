# Runbooks dhe Playbooks për Incident Response

## Përmbledhje

Ky dokument përmban runbooks dhe playbooks për menaxhimin e incidenteve në Smart Grid Analytics, siç kërkohet nga kërkesat teknike të profesorit.

## Runbooks

### 1. Database Connection Failure

**Symptom**: Shërbimet nuk mund të lidhen me PostgreSQL

**Steps**:
1. Kontrollo statusin e PostgreSQL:
   ```bash
   docker ps | grep postgres
   docker logs smartgrid-postgres --tail 50
   ```

2. Kontrollo network connectivity:
   ```bash
   docker exec smartgrid-api-gateway ping smartgrid-postgres
   ```

3. Restart PostgreSQL nëse është down:
   ```bash
   docker restart smartgrid-postgres
   ```

4. Kontrollo connection pool:
   ```bash
   docker logs smartgrid-data-processing --tail 50 | grep -i "connection"
   ```

5. Nëse problemi vazhdon, kontrollo disk space:
   ```bash
   docker exec smartgrid-postgres df -h
   ```

**Recovery**: Restart shërbimet që varen nga PostgreSQL

### 2. Kafka Broker Down

**Symptom**: Mesazhet nuk dërgohen ose konsumohen

**Steps**:
1. Kontrollo statusin e Kafka:
   ```bash
   docker ps | grep kafka
   docker logs smartgrid-kafka --tail 50
   ```

2. Kontrollo Zookeeper:
   ```bash
   docker ps | grep zookeeper
   docker logs smartgrid-zookeeper --tail 50
   ```

3. Restart Kafka:
   ```bash
   docker restart smartgrid-kafka
   ```

4. Kontrollo topics:
   ```bash
   docker exec smartgrid-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

**Recovery**: Restart Kafka dhe Zookeeper, kontrollo offset positions

### 3. High Memory Usage

**Symptom**: Shërbimet konsumojnë shumë memorie

**Steps**:
1. Identifiko shërbimin me problem:
   ```bash
   docker stats --no-stream
   ```

2. Kontrollo logs për memory leaks:
   ```bash
   docker logs <service-name> --tail 100 | grep -i "memory\|oom"
   ```

3. Restart shërbimi:
   ```bash
   docker restart <service-name>
   ```

4. Nëse problemi vazhdon, rriti memory limits në docker-compose.yml

**Recovery**: Restart shërbimi, monitoro për 15 minuta

### 4. API Gateway Circuit Breaker Open

**Symptom**: API Gateway kthen 503 për shërbime të caktuara

**Steps**:
1. Kontrollo circuit breaker status:
   ```bash
   curl http://localhost:5000/api/test
   docker logs smartgrid-api-gateway --tail 50 | grep -i "circuit"
   ```

2. Identifiko shërbimin me problem:
   - Kontrollo health checks të shërbimeve
   - Shiko logs për errors

3. Restart shërbimin e dështuar:
   ```bash
   docker restart <service-name>
   ```

4. Prit 60 sekonda për circuit breaker timeout

**Recovery**: Circuit breaker do të mbyllët automatikisht pas 2 sukseseve

### 5. Redis Cache Failure

**Symptom**: Cache nuk funksionon, performance degradation

**Steps**:
1. Kontrollo Redis:
   ```bash
   docker ps | grep redis
   docker exec smartgrid-redis redis-cli ping
   ```

2. Restart Redis:
   ```bash
   docker restart smartgrid-redis
   ```

3. Kontrollo connectivity nga shërbimet:
   ```bash
   docker logs smartgrid-analytics --tail 50 | grep -i redis
   ```

**Recovery**: Redis do të rindërtojë cache automatikisht

## Playbooks

### Playbook 1: Full System Recovery

**Trigger**: Të gjitha shërbimet janë down

**Steps**:
1. Stop të gjitha containers:
   ```bash
   docker-compose down
   ```

2. Kontrollo disk space dhe resources:
   ```bash
   df -h
   free -h
   ```

3. Cleanup volumes nëse është e nevojshme:
   ```bash
   docker system prune -a --volumes
   ```

4. Restart të gjitha shërbimet:
   ```bash
   docker-compose up -d
   ```

5. Verifiko statusin:
   ```bash
   docker-compose ps
   ```

6. Test health checks:
   ```bash
   curl http://localhost:5000/api/test
   ```

### Playbook 2: Data Loss Recovery

**Trigger**: Të dhëna të humbura ose të korruptuara

**Steps**:
1. Stop shërbimet që shkruajnë në database:
   ```bash
   docker stop smartgrid-data-processing
   ```

2. Backup database:
   ```bash
   docker exec smartgrid-postgres pg_dump -U smartgrid smartgrid_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. Restore nga backup nëse është e nevojshme:
   ```bash
   docker exec -i smartgrid-postgres psql -U smartgrid smartgrid_db < backup.sql
   ```

4. Kontrollo integritetin e të dhënave:
   ```bash
   docker exec smartgrid-postgres psql -U smartgrid smartgrid_db -c "SELECT COUNT(*) FROM sensor_data;"
   ```

5. Restart shërbimet:
   ```bash
   docker start smartgrid-data-processing
   ```

### Playbook 3: Security Incident Response

**Trigger**: Aktivitet i dyshimtë ose breach i mundshëm

**Steps**:
1. Izoloni sistemin:
   ```bash
   docker-compose stop
   ```

2. Kontrollo audit logs:
   ```bash
   docker logs smartgrid-api-gateway | grep -i "unauthorized\|forbidden"
   docker logs smartgrid-user-management | grep -i "login\|auth"
   ```

3. Revoko tokens të komprometuar:
   ```bash
   docker exec smartgrid-postgres psql -U smartgrid smartgrid_db -c "DELETE FROM user_sessions WHERE expires_at < NOW();"
   ```

4. Ndrysho secrets:
   - Update JWT_SECRET në environment variables
   - Regjenero tokens

5. Restart shërbimet me secrets të reja

6. Monitoro për aktivitet të dyshimtë

## Monitoring dhe Alerting

### Health Check Endpoints

- API Gateway: `http://localhost:5000/health`
- Data Ingestion: `http://localhost:5001/health`
- Analytics: `http://localhost:5002/health`
- Notification: `http://localhost:5003/health`
- User Management: `http://localhost:5004/health`

### Key Metrics për Monitoring

1. **Response Time**: < 200ms për 95% të kërkesave
2. **Error Rate**: < 1% të kërkesave
3. **CPU Usage**: < 80%
4. **Memory Usage**: < 85%
5. **Database Connections**: < 80% të max connections

### Alerting Rules

- **Critical**: CPU > 90%, Memory > 95%, Error Rate > 5%
- **Warning**: CPU > 80%, Memory > 85%, Error Rate > 1%

## Escalation Path

1. **Level 1**: DevOps Engineer - Incidentet e zakonshme
2. **Level 2**: Senior DevOps - Incidentet komplekse
3. **Level 3**: Architect - Incidentet kritike që kërkojnë ndryshime arkitekture

## Post-Incident Review

Pas çdo incidenti:

1. Dokumento incidentin
2. Identifiko root cause
3. Krijo action items për parandalim
4. Update runbooks bazuar në mësimet e nxjerra
5. Share knowledge me ekipin

