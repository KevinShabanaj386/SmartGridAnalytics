"""
Behavioral Analytics për Smart Grid Analytics
Identifikon sjellje jonormale përmes algoritmeve të mësimit makinerik
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

# Database configuration
import os
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

def get_user_behavior_features(user_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Merr behavioral features për një user
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Merr audit logs për user
        cursor.execute("""
            SELECT 
                action,
                request_path,
                ip_address,
                timestamp,
                response_status
            FROM audit_logs
            WHERE user_id = %s
            AND timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
        """, (user_id, days))
        
        logs = cursor.fetchall()
        
        if len(logs) == 0:
            return {}
        
        # Llogarit features
        features = {
            'total_actions': len(logs),
            'unique_endpoints': len(set(log['request_path'] for log in logs)),
            'unique_ips': len(set(log['ip_address'] for log in logs if log['ip_address'])),
            'failed_requests': sum(1 for log in logs if log['response_status'] and log['response_status'] >= 400),
            'successful_requests': sum(1 for log in logs if log['response_status'] and 200 <= log['response_status'] < 300),
            'actions_per_hour': defaultdict(int),
            'endpoint_frequency': defaultdict(int),
            'ip_frequency': defaultdict(int),
            'time_patterns': defaultdict(int)  # Hour of day
        }
        
        # Llogarit patterns
        for log in logs:
            # Actions per hour
            hour = log['timestamp'].hour if log['timestamp'] else 0
            features['actions_per_hour'][hour] += 1
            
            # Endpoint frequency
            if log['request_path']:
                features['endpoint_frequency'][log['request_path']] += 1
            
            # IP frequency
            if log['ip_address']:
                features['ip_frequency'][str(log['ip_address'])] += 1
            
            # Time patterns
            features['time_patterns'][hour] += 1
        
        # Normalize
        features['failure_rate'] = features['failed_requests'] / len(logs) if len(logs) > 0 else 0
        features['success_rate'] = features['successful_requests'] / len(logs) if len(logs) > 0 else 0
        
        return features
        
    except Exception as e:
        logger.error(f"Error getting user behavior features: {str(e)}")
        return {}
    finally:
        conn.close()

def detect_behavioral_anomalies(user_id: int, current_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Zbulon anomalitë në sjelljen e user-it duke krahasuar me baseline
    """
    try:
        # Merr baseline (mesatarja e features për 30 ditët e fundit)
        baseline = get_user_behavior_features(user_id, days=30)
        
        if not baseline or baseline.get('total_actions', 0) == 0:
            return {
                'is_anomaly': False,
                'risk_score': 0,
                'anomalies': [],
                'message': 'Insufficient data for analysis'
            }
        
        anomalies = []
        risk_score = 0
        
        # 1. Check për unusual activity volume
        if current_features.get('total_actions', 0) > baseline.get('total_actions', 0) * 3:
            anomalies.append({
                'type': 'unusual_activity_volume',
                'severity': 'high',
                'description': f"Activity volume is {current_features.get('total_actions', 0) / baseline.get('total_actions', 1):.2f}x higher than baseline"
            })
            risk_score += 30
        
        # 2. Check për new IP addresses
        current_ips = set(current_features.get('ip_frequency', {}).keys())
        baseline_ips = set(baseline.get('ip_frequency', {}).keys())
        new_ips = current_ips - baseline_ips
        
        if len(new_ips) > 0 and len(baseline_ips) > 0:
            anomalies.append({
                'type': 'new_ip_address',
                'severity': 'medium',
                'description': f"Access from {len(new_ips)} new IP address(es): {', '.join(list(new_ips)[:3])}"
            })
            risk_score += 20
        
        # 3. Check për unusual endpoints
        current_endpoints = set(current_features.get('endpoint_frequency', {}).keys())
        baseline_endpoints = set(baseline.get('endpoint_frequency', {}).keys())
        new_endpoints = current_endpoints - baseline_endpoints
        
        if len(new_endpoints) > 0:
            anomalies.append({
                'type': 'unusual_endpoint_access',
                'severity': 'medium',
                'description': f"Access to {len(new_endpoints)} new endpoint(s)"
            })
            risk_score += 15
        
        # 4. Check për failure rate
        if current_features.get('failure_rate', 0) > baseline.get('failure_rate', 0) * 2:
            anomalies.append({
                'type': 'high_failure_rate',
                'severity': 'medium',
                'description': f"Failure rate is {current_features.get('failure_rate', 0):.2%} vs baseline {baseline.get('failure_rate', 0):.2%}"
            })
            risk_score += 15
        
        # 5. Check për unusual time patterns
        current_hours = set(current_features.get('time_patterns', {}).keys())
        baseline_hours = set(baseline.get('time_patterns', {}).keys())
        
        # Check për activity në orët e pazakonta
        unusual_hours = []
        for hour in current_hours:
            if hour not in baseline_hours or \
               current_features['time_patterns'].get(hour, 0) > baseline.get('time_patterns', {}).get(hour, 0) * 2:
                unusual_hours.append(hour)
        
        if unusual_hours:
            anomalies.append({
                'type': 'unusual_time_pattern',
                'severity': 'low',
                'description': f"Unusual activity at hours: {unusual_hours}"
            })
            risk_score += 10
        
        # Determine overall risk
        is_anomaly = risk_score >= 30  # Threshold për anomaly
        
        return {
            'is_anomaly': is_anomaly,
            'risk_score': min(risk_score, 100),  # Cap at 100
            'anomalies': anomalies,
            'baseline': {
                'total_actions': baseline.get('total_actions', 0),
                'unique_endpoints': baseline.get('unique_endpoints', 0),
                'unique_ips': baseline.get('unique_ips', 0),
                'failure_rate': baseline.get('failure_rate', 0)
            },
            'current': {
                'total_actions': current_features.get('total_actions', 0),
                'unique_endpoints': current_features.get('unique_endpoints', 0),
                'unique_ips': current_features.get('unique_ips', 0),
                'failure_rate': current_features.get('failure_rate', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error detecting behavioral anomalies: {str(e)}")
        return {
            'is_anomaly': False,
            'risk_score': 0,
            'anomalies': [],
            'error': str(e)
        }

def calculate_user_risk_score(user_id: int) -> Dict[str, Any]:
    """
    Llogarit risk score për një user bazuar në behavioral analytics
    """
    try:
        # Merr current behavior (last 24 hours)
        current_features = get_user_behavior_features(user_id, days=1)
        
        if not current_features or current_features.get('total_actions', 0) == 0:
            return {
                'user_id': user_id,
                'risk_score': 0,
                'risk_level': 'low',
                'message': 'No recent activity'
            }
        
        # Detect anomalies
        anomaly_result = detect_behavioral_anomalies(user_id, current_features)
        
        # Determine risk level
        risk_score = anomaly_result.get('risk_score', 0)
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'user_id': user_id,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'is_anomaly': anomaly_result.get('is_anomaly', False),
            'anomalies': anomaly_result.get('anomalies', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating user risk score: {str(e)}")
        return {
            'user_id': user_id,
            'risk_score': 0,
            'risk_level': 'unknown',
            'error': str(e)
        }

def get_high_risk_users(threshold: int = 50) -> List[Dict[str, Any]]:
    """
    Merr listën e users me risk score të lartë
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Merr të gjithë users që kanë aktivitet
        cursor.execute("""
            SELECT DISTINCT user_id
            FROM audit_logs
            WHERE user_id IS NOT NULL
            AND timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        users = cursor.fetchall()
        high_risk_users = []
        
        for user in users:
            user_id = user['user_id']
            risk_result = calculate_user_risk_score(user_id)
            
            if risk_result.get('risk_score', 0) >= threshold:
                high_risk_users.append(risk_result)
        
        # Sort by risk score
        high_risk_users.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        return high_risk_users
        
    except Exception as e:
        logger.error(f"Error getting high risk users: {str(e)}")
        return []
    finally:
        conn.close()

