#!/usr/bin/env python3
"""Test script to check Random Forest import"""
import sys
import traceback

try:
    from random_forest_anomaly import detect_anomalies_with_rf, classify_anomaly_type
    print("SUCCESS: Random Forest module imported successfully")
    print(f"detect_anomalies_with_rf: {detect_anomalies_with_rf}")
    print(f"classify_anomaly_type: {classify_anomaly_type}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
