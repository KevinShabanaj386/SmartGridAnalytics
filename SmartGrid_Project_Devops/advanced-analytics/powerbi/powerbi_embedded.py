"""
Power BI Embedded Integration për Smart Grid Analytics
Implementon Power BI Embedded API për advanced business analytics
"""
import logging
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Power BI Configuration
POWERBI_CLIENT_ID = os.getenv('POWERBI_CLIENT_ID', '')
POWERBI_CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET', '')
POWERBI_TENANT_ID = os.getenv('POWERBI_TENANT_ID', '')
POWERBI_WORKSPACE_ID = os.getenv('POWERBI_WORKSPACE_ID', '')
POWERBI_API_URL = 'https://api.powerbi.com'

def get_powerbi_access_token() -> Optional[str]:
    """
    Merr access token për Power BI API.
    
    Returns:
        Access token ose None nëse dështon
    """
    try:
        token_url = f"https://login.microsoftonline.com/{POWERBI_TENANT_ID}/oauth2/v2.0/token"
        
        data = {
            'client_id': POWERBI_CLIENT_ID,
            'client_secret': POWERBI_CLIENT_SECRET,
            'scope': 'https://analysis.windows.net/powerbi/api/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            logger.error(f"Failed to get Power BI access token: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Power BI access token: {str(e)}")
        return None

def get_powerbi_reports(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Merr lista e reports nga Power BI workspace.
    
    Args:
        workspace_id: Workspace ID (optional, përdor default)
    
    Returns:
        Dict me lista e reports
    """
    try:
        access_token = get_powerbi_access_token()
        if not access_token:
            return {
                'status': 'error',
                'error': 'Failed to get access token'
            }
        
        workspace = workspace_id or POWERBI_WORKSPACE_ID
        if not workspace:
            return {
                'status': 'error',
                'error': 'Power BI workspace ID not configured'
            }
        
        url = f"{POWERBI_API_URL}/v1.0/myorg/groups/{workspace}/reports"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'reports': response.json().get('value', [])
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error getting Power BI reports: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_powerbi_embed_token(
    report_id: str,
    workspace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Merr embed token për Power BI report.
    
    Args:
        report_id: Report ID
        workspace_id: Workspace ID (optional)
    
    Returns:
        Dict me embed token dhe embed URL
    """
    try:
        access_token = get_powerbi_access_token()
        if not access_token:
            return {
                'status': 'error',
                'error': 'Failed to get access token'
            }
        
        workspace = workspace_id or POWERBI_WORKSPACE_ID
        if not workspace:
            return {
                'status': 'error',
                'error': 'Power BI workspace ID not configured'
            }
        
        url = f"{POWERBI_API_URL}/v1.0/myorg/groups/{workspace}/reports/{report_id}/GenerateToken"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Embed token request body
        payload = {
            'accessLevel': 'View',
            'allowSaveAs': False
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                'status': 'success',
                'embed_token': token_data.get('token'),
                'embed_url': token_data.get('embedUrl'),
                'token_expiry': token_data.get('expiration')
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error getting Power BI embed token: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def refresh_powerbi_dataset(
    dataset_id: str,
    workspace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Refresh dataset në Power BI.
    
    Args:
        dataset_id: Dataset ID
        workspace_id: Workspace ID (optional)
    
    Returns:
        Dict me refresh status
    """
    try:
        access_token = get_powerbi_access_token()
        if not access_token:
            return {
                'status': 'error',
                'error': 'Failed to get access token'
            }
        
        workspace = workspace_id or POWERBI_WORKSPACE_ID
        if not workspace:
            return {
                'status': 'error',
                'error': 'Power BI workspace ID not configured'
            }
        
        url = f"{POWERBI_API_URL}/v1.0/myorg/groups/{workspace}/datasets/{dataset_id}/refreshes"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 202]:
            return {
                'status': 'success',
                'message': 'Dataset refresh initiated'
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error refreshing Power BI dataset: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def export_powerbi_report(
    report_id: str,
    format: str = 'PDF',  # PDF, PPTX, PNG
    workspace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export Power BI report në format të specifikuar.
    
    Args:
        report_id: Report ID
        format: Export format (PDF, PPTX, PNG)
        workspace_id: Workspace ID (optional)
    
    Returns:
        Dict me export status dhe download URL
    """
    try:
        access_token = get_powerbi_access_token()
        if not access_token:
            return {
                'status': 'error',
                'error': 'Failed to get access token'
            }
        
        workspace = workspace_id or POWERBI_WORKSPACE_ID
        if not workspace:
            return {
                'status': 'error',
                'error': 'Power BI workspace ID not configured'
            }
        
        url = f"{POWERBI_API_URL}/v1.0/myorg/groups/{workspace}/reports/{report_id}/ExportTo"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'format': format
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code in [200, 202]:
            result = response.json()
            return {
                'status': 'success',
                'export_id': result.get('id'),
                'status_url': result.get('statusUrl')
            }
        else:
            return {
                'status': 'error',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error exporting Power BI report: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

