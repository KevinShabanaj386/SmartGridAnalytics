"""
Swagger UI integration për API Gateway
"""
from flask import Flask, send_from_directory
import os

def setup_swagger_ui(app: Flask):
    """Setup Swagger UI për API Gateway"""
    try:
        from flask_swagger_ui import get_swaggerui_blueprint
        
        SWAGGER_URL = '/api-docs'
        API_URL = '/api/openapi.yaml'
        
        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={
                'app_name': "Smart Grid Analytics API",
                'docExpansion': 'list',
                'deepLinking': True,
                'displayRequestDuration': True,
                'filter': True,
                'showExtensions': True,
                'showCommonExtensions': True,
            }
        )
        
        app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
        
        # Serve OpenAPI spec
        @app.route('/api/openapi.yaml')
        def serve_openapi_spec():
            """Serve OpenAPI specification"""
            openapi_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'openapi',
                'openapi.yaml'
            )
            if os.path.exists(openapi_path):
                return send_from_directory(
                    os.path.dirname(openapi_path),
                    'openapi.yaml',
                    mimetype='application/x-yaml'
                )
            else:
                return {'error': 'OpenAPI spec not found'}, 404
        
        return True
    except ImportError:
        return False

