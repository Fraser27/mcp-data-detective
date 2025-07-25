"""
OpenSearch Connection and Utilities
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from opensearchpy import OpenSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenSearchConnection:
    """OpenSearch connection manager"""
    
    def __init__(self):
        self.config = {
            'hosts': [{
                'host': os.getenv('OPENSEARCH_HOST', 'localhost'),
                'port': int(os.getenv('OPENSEARCH_PORT', 9200))
            }],
            'http_auth': (
                os.getenv('OPENSEARCH_USER', 'admin'),
                os.getenv('OPENSEARCH_PASSWORD', 'admin')
            ),
            'use_ssl': os.getenv('OPENSEARCH_USE_SSL', 'true').lower() == 'true',
            'verify_certs': os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true',
            'ssl_show_warn': False,
            'timeout': 30,
            'max_retries': 3,
            'retry_on_timeout': True
        }
        
        # Initialize OpenSearch client
        self.client = OpenSearch(**self.config)
    
    def test_connection(self) -> bool:
        """Test OpenSearch connection"""
        try:
            info = self.client.info()
            logger.debug(f"Connected to OpenSearch cluster: {info.get('cluster_name', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def list_indices(self) -> List[str]:
        """List all indices in the cluster"""
        try:
            indices = self.client.cat.indices(format='json')
            return [index['index'] for index in indices if not index['index'].startswith('.')]
        except Exception as e:
            logger.error(f"Error listing indices: {e}")
            raise
    
    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """Get detailed information about an index"""
        try:
            # Get index mapping
            mapping = self.client.indices.get_mapping(index=index_name)
            
            # Get index settings
            settings = self.client.indices.get_settings(index=index_name)
            
            # Get index stats
            stats = self.client.indices.stats(index=index_name)
            
            return {
                'index_name': index_name,
                'mapping': mapping[index_name]['mappings'],
                'settings': settings[index_name]['settings'],
                'stats': stats['indices'][index_name]
            }
        except Exception as e:
            logger.error(f"Error getting index info for {index_name}: {e}")
            raise
    
    def search_index(self, index_name: str, query: Dict[str, Any], size: int = 100) -> Dict[str, Any]:
        """Execute a search query on an index"""
        try:
            # Add size limit for safety
            size = min(size, 1000)
            
            response = self.client.search(
                index=index_name,
                body=query,
                size=size
            )
            
            return {
                'total_hits': response['hits']['total']['value'],
                'max_score': response['hits']['max_score'],
                'hits': response['hits']['hits']
            }
        except Exception as e:
            logger.error(f"Error searching index {index_name}: {e}")
            raise
    
    def get_index_sample(self, index_name: str, size: int = 5) -> Dict[str, Any]:
        """Get a sample of documents from an index"""
        try:
            size = min(size, 50)
            
            query = {
                "query": {
                    "match_all": {}
                },
                "size": size
            }
            
            return self.search_index(index_name, query, size)
        except Exception as e:
            logger.error(f"Error getting sample from index {index_name}: {e}")
            raise
    
    def get_index_count(self, index_name: str) -> int:
        """Get the document count for an index"""
        try:
            response = self.client.count(index=index_name)
            return response['count']
        except Exception as e:
            logger.error(f"Error counting documents in index {index_name}: {e}")
            raise
    
    def search_documents(self, index_name: str, field: str, search_term: str, size: int = 20) -> Dict[str, Any]:
        """Search for documents containing a specific term in a field"""
        try:
            size = min(size, 100)
            
            query = {
                "query": {
                    "match": {
                        field: search_term
                    }
                },
                "size": size
            }
            
            return self.search_index(index_name, query, size)
        except Exception as e:
            logger.error(f"Error searching documents in {index_name}: {e}")
            raise
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get comprehensive cluster information"""
        try:
            info = self.client.info()
            health = self.client.cluster.health()
            stats = self.client.cluster.stats()
            
            return {
                'cluster_name': info['cluster_name'],
                'version': info['version']['number'],
                'health': health,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            raise
    
    def get_index_mapping(self, index_name: str) -> Dict[str, Any]:
        """Get the mapping (schema) for an index"""
        try:
            mapping = self.client.indices.get_mapping(index=index_name)
            return mapping[index_name]['mappings']
        except Exception as e:
            logger.error(f"Error getting mapping for index {index_name}: {e}")
            raise
    
    def create_index(self, index_name: str, mapping: Dict[str, Any] = None) -> bool:
        """Create a new index with optional mapping"""
        try:
            body = {}
            if mapping:
                body['mappings'] = mapping
            
            self.client.indices.create(index=index_name, body=body)
            return True
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            raise
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        try:
            self.client.indices.delete(index=index_name)
            return True
        except Exception as e:
            logger.error(f"Error deleting index {index_name}: {e}")
            raise
    
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: str = None) -> str:
        """Index a document into an index"""
        try:
            response = self.client.index(
                index=index_name,
                body=document,
                id=doc_id
            )
            return response['_id']
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

# Global OpenSearch client instance
opensearch_client = OpenSearchConnection() 