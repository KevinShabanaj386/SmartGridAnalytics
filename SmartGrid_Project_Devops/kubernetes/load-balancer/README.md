# Load Balancer Configuration - NGINX

## Përmbledhje

Ky dokument përshkruan konfigurimin e Layer 7 load balancing me NGINX për Smart Grid Analytics.

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

## Deployment

```bash
# Apply NGINX configuration
kubectl apply -f kubernetes/load-balancer/nginx-config.yaml

# Deploy NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

## Best Practices

1. **Health Checks**: Gjithmonë përdorni health checks
2. **Circuit Breakers**: Implementoni circuit breakers për resiliency
3. **Rate Limiting**: Përdorni rate limiting për të mbrojtur services
4. **Caching**: Cache static content dhe API responses
5. **SSL/TLS**: Gjithmonë përdorni HTTPS
6. **Monitoring**: Monitoroni load balancer metrics
7. **Logging**: Logoni të gjitha requests për debugging

