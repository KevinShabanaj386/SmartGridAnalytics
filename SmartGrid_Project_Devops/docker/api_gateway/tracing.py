"""
OpenTelemetry Tracing për API Gateway
Implementon distributed tracing për monitoring të kërkesave ndër mikrosherbime
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import os

def setup_tracing(app):
    """Konfiguron OpenTelemetry tracing për aplikacionin"""
    
    # Konfigurimi i resource
    resource = Resource.create({
        "service.name": "api-gateway",
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Konfigurimi i tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # Jaeger exporter (nëse është konfiguruar)
    jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://jaeger:14268/api/traces")
    if jaeger_endpoint:
        try:
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
                agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
            )
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
        except Exception as e:
            print(f"Warning: Could not setup Jaeger exporter: {e}")
    
    # Console exporter për development
    if os.getenv("ENVIRONMENT", "development") == "development":
        console_exporter = ConsoleSpanExporter()
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(console_exporter)
        )
    
    # Instrument Flask dhe Requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    
    return tracer

