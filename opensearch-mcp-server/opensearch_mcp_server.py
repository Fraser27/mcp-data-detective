"""
OpenSearch Tools for Strands Agents MCP Server
"""
import json
import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from database import opensearch_client

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "opensearch-mcp-server",
    instructions="""
    # OpenSearch MCP Server
    This server provides tools to interact with OpenSearch clusters, including searching, indexing, and managing indices.
    """, host="0.0.0.0", port=8000
)

@mcp.tool()
async def test_opensearch_connection() -> str:
    """
    Test the OpenSearch cluster connection.
    
    Returns:
        str: Connection status message
    """
    print("🔌 TEST_OPENSEARCH_CONNECTION called")
    logger.info("TEST_OPENSEARCH_CONNECTION called")
    try:
        if opensearch_client.test_connection():
            print("✅ OpenSearch connection successful")
            return "✅ OpenSearch connection successful"
        else:
            print("❌ OpenSearch connection failed")
            return "❌ OpenSearch connection failed"
    except Exception as e:
        print(f"❌ OpenSearch connection error: {str(e)}")
        return f"❌ OpenSearch connection error: {str(e)}"

@mcp.tool()
async def list_opensearch_indices() -> str:
    """
    List all indices in the OpenSearch cluster.
    
    Returns:
        str: JSON formatted list of index names
    """
    print("📋 LIST_OPENSEARCH_INDICES called")
    logger.info("LIST_OPENSEARCH_INDICES called")
    try:
        indices = opensearch_client.list_indices()
        print(f"✅ Found {len(indices)} indices")
        return json.dumps({
            "indices": indices,
            "count": len(indices)
        }, indent=2)
    except Exception as e:
        logger.error(f"Error listing indices: {e}")
        print(f"❌ Error listing indices: {str(e)}")
        return f"❌ Error listing indices: {str(e)}"

@mcp.tool()
async def describe_opensearch_index(index_name: str) -> str:
    """
    Get detailed information about a specific OpenSearch index including mapping, settings, and stats.
    
    Args:
        index_name (str): Name of the index to describe
        
    Returns:
        str: JSON formatted index information
    """
    print(f"📊 DESCRIBE_OPENSEARCH_INDEX called for index: {index_name}")
    logger.info(f"DESCRIBE_OPENSEARCH_INDEX called for index: {index_name}")
    try:
        index_info = opensearch_client.get_index_info(index_name)
        print(f"✅ Retrieved index info for {index_name}")
        return json.dumps(index_info, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error describing index {index_name}: {e}")
        print(f"❌ Error describing index '{index_name}': {str(e)}")
        return f"❌ Error describing index '{index_name}': {str(e)}"

@mcp.tool()
async def search_opensearch_index(index_name: str, query) -> str:
    """
    Execute a search query against an OpenSearch index.
    
    Args:
        index_name (str): Name of the index to search
        query: A JSON string of a well formed OpenSearch Query
        
    Returns:
        str: JSON formatted search results
    """
    print(f"🔍 SEARCH_OPENSEARCH_INDEX called for index: {index_name}, query: {query}")
    logger.info(f"SEARCH_OPENSEARCH_INDEX called for index: {index_name}, query length: {len(query)}")
    try:
        if isinstance(query, dict):
            search_body = query
        else:
            # Parse the query JSON
            search_body = json.loads(query)
        
        results = opensearch_client.search_index(index_name, query=search_body)
        print(f"✅ Search executed successfully, found {results['total_hits']} total hits, returned {len(results['hits'])} results")
        
        return json.dumps({
            "index": index_name,
            "query": search_body,
            "total_hits": results['total_hits'],
            "max_score": results['max_score'],
            "hits": results['hits']
        }, indent=2, default=str)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON query: {str(e)}")
        return f"❌ Invalid JSON query: {str(e)}"
    except Exception as e:
        logger.error(f"Error executing search: {e}")
        print(f"❌ Search execution error: {str(e)}")
        return f"❌ Search execution error: {str(e)}"


@mcp.tool()
async def get_opensearch_index_count(index_name: str) -> str:
    """
    Get the document count for an OpenSearch index.
    
    Args:
        index_name (str): Name of the index to count
        
    Returns:
        str: JSON formatted count result
    """
    print(f"🔢 GET_OPENSEARCH_INDEX_COUNT called for index: {index_name}")
    logger.info(f"GET_OPENSEARCH_INDEX_COUNT called for index: {index_name}")
    try:
        count = opensearch_client.get_index_count(index_name)
        print(f"✅ Index {index_name} has {count} documents")
        
        return json.dumps({
            "index": index_name,
            "document_count": count
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error counting index documents: {e}")
        print(f"❌ Error counting documents in index '{index_name}': {str(e)}")
        return f"❌ Error counting documents in index '{index_name}': {str(e)}"


@mcp.tool()
async def get_opensearch_cluster_summary() -> str:
    """
    Get a summary of the OpenSearch cluster including all indices and their basic information.
    
    Returns:
        str: JSON formatted cluster summary
    """
    print("📋 GET_OPENSEARCH_CLUSTER_SUMMARY called")
    logger.info("GET_OPENSEARCH_CLUSTER_SUMMARY called")
    try:
        cluster_info = opensearch_client.get_cluster_info()
        indices = opensearch_client.list_indices()
        
        summary = {
            "cluster_name": cluster_info['cluster_name'],
            "version": cluster_info['version'],
            "health": cluster_info['health'],
            "index_count": len(indices),
            "indices": []
        }
        
        for index_name in indices:
            try:
                # Get basic index info
                count = opensearch_client.get_index_count(index_name)
                mapping = opensearch_client.get_index_mapping(index_name)
                
                # Count fields in mapping
                field_count = 0
                if 'properties' in mapping:
                    field_count = len(mapping['properties'])
                
                summary["indices"].append({
                    "name": index_name,
                    "document_count": count,
                    "field_count": field_count
                })
            except Exception as index_error:
                logger.warning(f"Error getting info for index {index_name}: {index_error}")
                summary["indices"].append({
                    "name": index_name,
                    "error": str(index_error)
                })
        
        print(f"✅ Generated cluster summary with {len(indices)} indices")
        return json.dumps(summary, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting cluster summary: {e}")
        print(f"❌ Error getting cluster summary: {str(e)}")
        return f"❌ Error getting cluster summary: {str(e)}"

# @mcp.tool()
# async def create_opensearch_index(index_name: str, mapping: Optional[str] = None) -> str:
#     """
#     Create a new OpenSearch index with optional mapping.
    
#     Args:
#         index_name (str): Name of the index to create
#         mapping (str, optional): JSON formatted mapping for the index
        
#     Returns:
#         str: JSON formatted creation result
#     """
#     print(f"🏗️ CREATE_OPENSEARCH_INDEX called for index: {index_name}")
#     logger.info(f"CREATE_OPENSEARCH_INDEX called for index: {index_name}, has_mapping: {mapping is not None}")
#     try:
#         mapping_dict = None
#         if mapping:
#             mapping_dict = json.loads(mapping)
        
#         success = opensearch_client.create_index(index_name, mapping_dict)
#         print(f"✅ Index '{index_name}' created successfully: {success}")
        
#         return json.dumps({
#             "index": index_name,
#             "created": success,
#             "message": f"Index '{index_name}' created successfully"
#         }, indent=2)
        
#     except json.JSONDecodeError as e:
#         print(f"❌ Invalid JSON mapping: {str(e)}")
#         return f"❌ Invalid JSON mapping: {str(e)}"
#     except Exception as e:
#         logger.error(f"Error creating index: {e}")
#         print(f"❌ Error creating index '{index_name}': {str(e)}")
#         return f"❌ Error creating index '{index_name}': {str(e)}"

# @mcp.tool()
# async def delete_opensearch_index(index_name: str) -> str:
#     """
#     Delete an OpenSearch index.
    
#     Args:
#         index_name (str): Name of the index to delete
        
#     Returns:
#         str: JSON formatted deletion result
#     """
#     print(f"🗑️ DELETE_OPENSEARCH_INDEX called for index: {index_name}")
#     logger.info(f"DELETE_OPENSEARCH_INDEX called for index: {index_name}")
#     try:
#         success = opensearch_client.delete_index(index_name)
#         print(f"✅ Index '{index_name}' deleted successfully: {success}")
        
#         return json.dumps({
#             "index": index_name,
#             "deleted": success,
#             "message": f"Index '{index_name}' deleted successfully"
#         }, indent=2)
        
#     except Exception as e:
#         logger.error(f"Error deleting index: {e}")
#         print(f"❌ Error deleting index '{index_name}': {str(e)}")
#         return f"❌ Error deleting index '{index_name}': {str(e)}"

@mcp.tool()
async def get_opensearch_index_mapping(index_name: str) -> str:
    """
    Get the mapping structure for a specific OpenSearch index.
    
    Args:
        index_name (str): Name of the index to get mappings for
        
    Returns:
        str: JSON formatted mapping structure
    """
    print(f"🗺️ GET_OPENSEARCH_INDEX_MAPPING called for index: {index_name}")
    logger.info(f"GET_OPENSEARCH_INDEX_MAPPING called for index: {index_name}")
    try:
        mapping = opensearch_client.get_index_mapping(index_name)
        print(f"✅ Retrieved mapping for index {index_name}")
        
        return json.dumps({
            "index": index_name,
            "mapping": mapping
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting index mapping: {e}")
        print(f"❌ Error getting mapping for index '{index_name}': {str(e)}")
        return f"❌ Error getting mapping for index '{index_name}': {str(e)}"

@mcp.tool()
async def index_opensearch_document(index_name: str, document: str, doc_id: Optional[str] = None) -> str:
    """
    Index a document into an OpenSearch index.
    
    Args:
        index_name (str): Name of the index to index into
        document (str): JSON formatted document to index
        doc_id (str, optional): Document ID (auto-generated if not provided)
        
    Returns:
        str: JSON formatted indexing result
    """
    print(f"📝 INDEX_OPENSEARCH_DOCUMENT called for index: {index_name}, doc_id: {doc_id}")
    logger.info(f"INDEX_OPENSEARCH_DOCUMENT called for index: {index_name}, doc_id: {doc_id}, document length: {len(document)}")
    try:
        document_dict = json.loads(document)
        
        doc_id_result = opensearch_client.index_document(index_name, document_dict, doc_id)
        print(f"✅ Document indexed successfully with ID: {doc_id_result}")
        
        return json.dumps({
            "index": index_name,
            "document_id": doc_id_result,
            "indexed": True,
            "message": f"Document indexed successfully with ID: {doc_id_result}"
        }, indent=2)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON document: {str(e)}")
        return f"❌ Invalid JSON document: {str(e)}"
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        print(f"❌ Error indexing document: {str(e)}")
        return f"❌ Error indexing document: {str(e)}"

def main():
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()