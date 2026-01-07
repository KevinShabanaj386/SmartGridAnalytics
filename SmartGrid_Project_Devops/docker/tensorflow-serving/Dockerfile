FROM tensorflow/serving:2.15.0

# Copy saved models
COPY models /models

# Set environment variables
ENV MODEL_NAME=smartgrid-load-forecasting
ENV MODEL_BASE_PATH=/models

# Expose ports
EXPOSE 8500 8501

# Start TensorFlow Serving
CMD ["tensorflow_model_server", \
     "--port=8500", \
     "--rest_api_port=8501", \
     "--model_name=${MODEL_NAME}", \
     "--model_base_path=${MODEL_BASE_PATH}"]

