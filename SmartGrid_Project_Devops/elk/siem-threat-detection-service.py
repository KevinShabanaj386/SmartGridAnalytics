"""
SIEM Threat Detection Service
Integron me ELK Stack për real-time threat detection dhe correlation
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

# Elasticsearch configuration
ELASTICSEARCH_HOST = "http://smartgrid-elasticsearch:9200"
THREATS_INDEX = "smartgrid-threats-*"
LOGS_INDEX = "smartgrid-logs-*"

def search_threats(
    severity: Optional[str] = None,
    threat_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    size: int = 100
) -> List[Dict[str, Any]]:
    """
    Kërkon threats nga Elasticsearch (100% SECURITY)
    """
    query = {
        "bool": {
            "must": []
        }
    }
    
    if severity:
        query["bool"]["must"].append({
            "term": {"threat_severity.keyword": severity}
        })
    
    if threat_type:
        query["bool"]["must"].append({
            "term": {"threat_type.keyword": threat_type}
        })
    
    if start_time or end_time:
        time_range = {}
        if start_time:
            time_range["gte"] = start_time.isoformat()
        if end_time:
            time_range["lte"] = end_time.isoformat()
        query["bool"]["must"].append({
            "range": {"@timestamp": time_range}
        })
    
    search_body = {
        "query": query,
        "size": size,
        "sort": [{"@timestamp": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_HOST}/{THREATS_INDEX}/_search",
            json=search_body,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return [hit["_source"] for hit in data.get("hits", {}).get("hits", [])]
    except Exception as e:
        logger.error(f"Error searching threats: {str(e)}")
        return []

def correlate_threats(
    time_window_minutes: int = 5,
    min_correlation_count: int = 3
) -> List[Dict[str, Any]]:
    """
    Korrelon threats për të identifikuar attack patterns (100% SECURITY)
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=time_window_minutes)
    
    threats = search_threats(start_time=start_time, end_time=end_time, size=1000)
    
    # Group threats by IP address
    threats_by_ip = {}
    for threat in threats:
        ip = threat.get("ip_address")
        if ip:
            if ip not in threats_by_ip:
                threats_by_ip[ip] = []
            threats_by_ip[ip].append(threat)
    
    # Identify correlated threats
    correlated = []
    for ip, ip_threats in threats_by_ip.items():
        if len(ip_threats) >= min_correlation_count:
            threat_types = [t.get("threat_type") for t in ip_threats]
            unique_types = set(threat_types)
            
            correlated.append({
                "ip_address": ip,
                "threat_count": len(ip_threats),
                "threat_types": list(unique_types),
                "severity": max([t.get("threat_severity", "low") for t in ip_threats], key=lambda x: ["low", "medium", "high", "critical"].index(x) if x in ["low", "medium", "high", "critical"] else 0),
                "first_threat": min([t.get("@timestamp") for t in ip_threats]),
                "last_threat": max([t.get("@timestamp") for t in ip_threats]),
                "threats": ip_threats
            })
    
    return correlated

def get_threat_statistics(
    hours: int = 24
) -> Dict[str, Any]:
    """
    Merr statistika për threats (100% SECURITY)
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    threats = search_threats(start_time=start_time, end_time=end_time, size=10000)
    
    stats = {
        "total_threats": len(threats),
        "by_severity": {},
        "by_type": {},
        "by_ip": {},
        "timeline": {}
    }
    
    for threat in threats:
        # By severity
        severity = threat.get("threat_severity", "unknown")
        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        # By type
        threat_type = threat.get("threat_type", "unknown")
        stats["by_type"][threat_type] = stats["by_type"].get(threat_type, 0) + 1
        
        # By IP
        ip = threat.get("ip_address", "unknown")
        stats["by_ip"][ip] = stats["by_ip"].get(ip, 0) + 1
        
        # Timeline (by hour)
        timestamp = threat.get("@timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                stats["timeline"][hour_key] = stats["timeline"].get(hour_key, 0) + 1
            except:
                pass
    
    return stats

def detect_brute_force_attack(
    ip_address: str,
    time_window_minutes: int = 5,
    min_attempts: int = 5
) -> bool:
    """
    Detekton brute force attacks (100% SECURITY)
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=time_window_minutes)
    
    threats = search_threats(
        threat_type="authentication_failure",
        start_time=start_time,
        end_time=end_time,
        size=1000
    )
    
    # Count failed login attempts për IP
    failed_attempts = [t for t in threats if t.get("ip_address") == ip_address]
    
    return len(failed_attempts) >= min_attempts

def get_high_risk_ips(
    hours: int = 24,
    min_threat_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Merr IP addresses me risk të lartë (100% SECURITY)
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    threats = search_threats(start_time=start_time, end_time=end_time, size=10000)
    
    # Group by IP
    ip_stats = {}
    for threat in threats:
        ip = threat.get("ip_address")
        if ip:
            if ip not in ip_stats:
                ip_stats[ip] = {
                    "ip_address": ip,
                    "threat_count": 0,
                    "threat_types": set(),
                    "max_severity": "low",
                    "first_seen": threat.get("@timestamp"),
                    "last_seen": threat.get("@timestamp")
                }
            
            ip_stats[ip]["threat_count"] += 1
            ip_stats[ip]["threat_types"].add(threat.get("threat_type", "unknown"))
            
            severity = threat.get("threat_severity", "low")
            severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            current_level = severity_levels.get(ip_stats[ip]["max_severity"], 0)
            threat_level = severity_levels.get(severity, 0)
            if threat_level > current_level:
                ip_stats[ip]["max_severity"] = severity
            
            if threat.get("@timestamp") > ip_stats[ip]["last_seen"]:
                ip_stats[ip]["last_seen"] = threat.get("@timestamp")
    
    # Filter dhe sort
    high_risk_ips = [
        {
            **stats,
            "threat_types": list(stats["threat_types"])
        }
        for stats in ip_stats.values()
        if stats["threat_count"] >= min_threat_count
    ]
    
    high_risk_ips.sort(key=lambda x: x["threat_count"], reverse=True)
    
    return high_risk_ips

