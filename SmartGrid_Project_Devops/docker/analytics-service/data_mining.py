"""
Data Mining Module për Smart Grid Analytics
Implementon Clustering dhe Association Rule Mining (kërkesë e profesorit)
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def kmeans_clustering(data: pd.DataFrame, n_clusters: int = 3, features: List[str] = None) -> Dict[str, Any]:
    """
    K-Means Clustering për grupim të inteligjent të të dhënave.
    
    Args:
        data: DataFrame me të dhëna
        n_clusters: Numri i cluster-ave
        features: Lista e features për clustering
    
    Returns:
        Dict me cluster assignments dhe centroids
    """
    try:
        if features is None:
            # Përdor të gjitha kolonat numerike
            features = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(features) == 0:
            raise ValueError("No numeric features found for clustering")
        
        # Përgatit të dhënat
        X = data[features].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Shto cluster assignments në data
        data_with_clusters = data.copy()
        data_with_clusters['cluster'] = clusters
        
        # Llogarit centroids
        centroids = kmeans.cluster_centers_
        
        # Statistikat për çdo cluster
        cluster_stats = []
        for i in range(n_clusters):
            cluster_data = data_with_clusters[data_with_clusters['cluster'] == i]
            stats = {
                'cluster_id': int(i),
                'size': len(cluster_data),
                'centroid': centroids[i].tolist(),
                'features': features
            }
            # Shto statistikat për çdo feature
            for feature in features:
                stats[f'{feature}_mean'] = float(cluster_data[feature].mean())
                stats[f'{feature}_std'] = float(cluster_data[feature].std())
            
            cluster_stats.append(stats)
        
        return {
            'status': 'success',
            'n_clusters': n_clusters,
            'clusters': cluster_stats,
            'data_with_clusters': data_with_clusters.to_dict('records'),
            'inertia': float(kmeans.inertia_)
        }
        
    except Exception as e:
        logger.error(f"Error in K-Means clustering: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def dbscan_clustering(data: pd.DataFrame, eps: float = 0.5, min_samples: int = 5, features: List[str] = None) -> Dict[str, Any]:
    """
    DBSCAN Clustering për grupim bazuar në densitet.
    
    Args:
        data: DataFrame me të dhëna
        eps: Distanca maksimale midis pikave në të njëjtin cluster
        min_samples: Numri minimal i pikave për cluster
        features: Lista e features për clustering
    
    Returns:
        Dict me cluster assignments
    """
    try:
        if features is None:
            features = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(features) == 0:
            raise ValueError("No numeric features found for clustering")
        
        # Përgatit të dhënat
        X = data[features].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(X_scaled)
        
        # Shto cluster assignments
        data_with_clusters = data.copy()
        data_with_clusters['cluster'] = clusters
        
        # Numri i cluster-ave (duke përjashtuar noise points: -1)
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        # Statistikat
        cluster_stats = []
        for i in range(n_clusters):
            cluster_data = data_with_clusters[data_with_clusters['cluster'] == i]
            stats = {
                'cluster_id': int(i),
                'size': len(cluster_data),
                'features': features
            }
            for feature in features:
                stats[f'{feature}_mean'] = float(cluster_data[feature].mean())
            
            cluster_stats.append(stats)
        
        return {
            'status': 'success',
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'clusters': cluster_stats,
            'data_with_clusters': data_with_clusters.to_dict('records')
        }
        
    except Exception as e:
        logger.error(f"Error in DBSCAN clustering: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def apriori_association_rules(transactions: List[List[str]], min_support: float = 0.1, min_confidence: float = 0.5) -> Dict[str, Any]:
    """
    Apriori Algorithm për Association Rule Mining.
    
    Args:
        transactions: Lista e transaksioneve (çdo transaksion është list e items)
        min_support: Support minimal
        min_confidence: Confidence minimal
    
    Returns:
        Dict me frequent itemsets dhe association rules
    """
    try:
        from collections import defaultdict
        
        # Llogarit support për çdo item
        item_counts = defaultdict(int)
        n_transactions = len(transactions)
        
        for transaction in transactions:
            for item in set(transaction):
                item_counts[item] += 1
        
        # Frequent 1-itemsets
        frequent_1_itemsets = {
            item: count / n_transactions
            for item, count in item_counts.items()
            if count / n_transactions >= min_support
        }
        
        # Krijo association rules të thjeshta (A -> B)
        rules = []
        items = list(frequent_1_itemsets.keys())
        
        for i, item_a in enumerate(items):
            for item_b in items[i+1:]:
                # Support për {A, B}
                support_ab = sum(1 for t in transactions if item_a in t and item_b in t) / n_transactions
                
                if support_ab >= min_support:
                    # Confidence: P(B|A) = P(A,B) / P(A)
                    confidence = support_ab / frequent_1_itemsets[item_a]
                    
                    if confidence >= min_confidence:
                        rules.append({
                            'antecedent': [item_a],
                            'consequent': [item_b],
                            'support': float(support_ab),
                            'confidence': float(confidence),
                            'lift': float(confidence / frequent_1_itemsets[item_b])
                        })
        
        return {
            'status': 'success',
            'frequent_itemsets': {
                '1-itemsets': {k: float(v) for k, v in frequent_1_itemsets.items()}
            },
            'association_rules': rules,
            'min_support': min_support,
            'min_confidence': min_confidence
        }
        
    except Exception as e:
        logger.error(f"Error in Apriori algorithm: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def fp_growth_association_rules(transactions: List[List[str]], min_support: float = 0.1) -> Dict[str, Any]:
    """
    FP-Growth Algorithm për Association Rule Mining (më efikas se Apriori).
    
    Note: Për implementim të plotë, duhet përdorur library si mlxtend
    
    Args:
        transactions: Lista e transaksioneve
        min_support: Support minimal
    
    Returns:
        Dict me frequent itemsets
    """
    try:
        # Implementim i thjeshtë - në prodhim përdorni mlxtend.fpgrowth
        from collections import defaultdict
        
        item_counts = defaultdict(int)
        n_transactions = len(transactions)
        
        for transaction in transactions:
            for item in set(transaction):
                item_counts[item] += 1
        
        frequent_itemsets = {
            item: count / n_transactions
            for item, count in item_counts.items()
            if count / n_transactions >= min_support
        }
        
        return {
            'status': 'success',
            'frequent_itemsets': {k: float(v) for k, v in frequent_itemsets.items()},
            'min_support': min_support,
            'note': 'Simplified implementation. For production, use mlxtend.fpgrowth'
        }
        
    except Exception as e:
        logger.error(f"Error in FP-Growth algorithm: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

