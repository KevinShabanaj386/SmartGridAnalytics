# Load Balancer Configuration - NGINX & Envoy

## Përmbledhje

Ky dokument përshkruan konfigurimin e Layer 7 load balancing me NGINX dhe Envoy për Smart Grid Analytics.

## NGINX Load Balancer

### Features

1. **Layer 7 Load Balancing**
   - Path-based routing
   - Header-based routing
   - Content-based routing
   - SSL/TLS termination

2. **Intelligent Routing**
   - Route bazuar në request path
   - Route bazuar në custom headers
   - Route bazuar në content type
   - Route bazuar në request size

3. **Performance Optimization**
   - Keepalive connections
   - Connection pooling
   - Caching (proxy_cache)
   - Compression

4. **Security**
   - Rate limiting
   - SSL/TLS
   - CORS support
   - Request size limits

### Configuration

**Vendndodhja**: `kubernetes/load-balancer/nginx-config.yaml`

**Load Balancing Algorithms:**
- `least_conn` - Least connections (default)
- `round_robin` - Round robin
- `ip_hash` - IP-based sticky sessions
- `hash $request_uri` - URI-based routing

**Intelligent Routing Examples:**

```nginx
# Path-based routing
location /api/v1/analytics {
    proxy_pass http://analytics_backend;
}

# Header-based routing (A/B testing)
location /api/v1/features {
    if ($http_x_feature_flag = "new_analytics") {
        proxy_pass http://analytics_backend_v2;
    }
    proxy_pass http://analytics_backend;
}

# Content-based routing
location /api/v1/data {
    if ($content_type ~* "application/json") {
        proxy_pass http://data_processing_backend;
    }
}
```

## Envoy Proxy

### Features

1. **Advanced Traffic Management**
   - Circuit breakers
   - Retry policies
   - Timeout configuration
   - Health checks

2. **Intelligent Routing**
   - Path matching
   - Header matching
   - Content-based routing
   - Weighted routing

3. **Observability**
   - Access logs
   - Metrics
   - Distributed tracing

### Configuration

**Vendndodhja**: `kubernetes/load-balancer/envoy-config.yaml`

**Load Balancing Policies:**
- `LEAST_REQUEST` - Least requests
- `ROUND_ROBIN` - Round robin
- `RANDOM` - Random selection
- `RING_HASH` - Consistent hashing

**Intelligent Routing Examples:**

```yaml
# Path-based routing
- match:
    path: "/api/v1/analytics"
  route:
    cluster: analytics_service

# Header-based routing
- match:
    path: "/api/v1/features"
    headers:
    - name: "x-feature-flag"
      exact_match: "new_analytics"
  route:
    cluster: analytics_service_v2

# Content-based routing
- match:
    path: "/api/v1/data"
    headers:
    - name: "content-type"
      exact_match: "application/json"
  route:
    cluster: data_processing_service_json
```

## Comparison: NGINX vs Envoy

| Feature | NGINX | Envoy |
|---------|-------|-------|
| **Maturity** | ✅ Very Mature | ⚠️ Modern |
| **Performance** | ✅ Excellent | ✅ Excellent |
| **Configuration** | ✅ Simple | ⚠️ Complex |
| **Service Mesh** | ❌ | ✅ Native |
| **Observability** | ⚠️ Basic | ✅ Advanced |
| **Dynamic Config** | ⚠️ Limited | ✅ Full Support |

## Deployment

### NGINX

```bash
# Apply NGINX configuration
kubectl apply -f kubernetes/load-balancer/nginx-config.yaml

# Deploy NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

### Envoy

```bash
# Apply Envoy configuration
kubectl apply -f kubernetes/load-balancer/envoy-config.yaml

# Deploy Envoy Proxy
kubectl apply -f kubernetes/load-balancer/envoy-deployment.yaml
```

## Best Practices

1. **Health Checks**: Gjithmonë përdorni health checks
2. **Circuit Breakers**: Implementoni circuit breakers për resiliency
3. **Rate Limiting**: Përdorni rate limiting për të mbrojtur services
4. **Caching**: Cache static content dhe API responses
5. **SSL/TLS**: Gjithmonë përdorni HTTPS
6. **Monitoring**: Monitoroni load balancer metrics
7. **Logging**: Logoni të gjitha requests për debugging

