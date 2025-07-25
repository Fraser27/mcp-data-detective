"""
Sample data script for OpenSearch MCP Server
This script creates sample indices and documents for testing the MCP server.
"""
import json
import time
from database import opensearch_client

def create_sample_data():
    """Create sample indices and documents for testing"""
    
    # Test connection first
    if not opensearch_client.test_connection():
        print("❌ Cannot connect to OpenSearch. Please ensure OpenSearch is running.")
        return
    
    print("✅ Connected to OpenSearch cluster")
    
    # Create sample indices
    sample_indices = {
        "logs": {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "service": {"type": "keyword"},
                    "user_id": {"type": "keyword"}
                }
            }
        },
        "products": {
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "category": {"type": "keyword"},
                    "price": {"type": "float"},
                    "description": {"type": "text"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        },
        "orders": {
            "mappings": {
                "properties": {
                    "order_id": {"type": "keyword"},
                    "customer_id": {"type": "keyword"},
                    "total_amount": {"type": "float"},
                    "status": {"type": "keyword"},
                    "items": {"type": "nested"},
                    "created_at": {"type": "date"}
                }
            }
        },
        "fuel_transactions": {
            "mappings": {
                "properties": {
                    "transaction_id": {"type": "text"},
                    "timestamp": {"type": "timestamp"},
                    "device_id": {"type": "text"},
                    "nozzle_id": {"type": "text"},
                    "site_id": {"type": "text"},
                    "payment_method": {"type": "text"},
                    "amount": {"type": "float"},
                    "volume_dispensed": {"type": "float"},
                    "fuel_type": {"type": "text"},
                    "status": {"type": "text"}
                }
            }
        },
        "device_status": {
            "mappings": {
                "properties": {
                    "event_id": {"type": "text"},
                    "timestamp": {"type": "timestamp"},
                    "device_id": {"type": "text"},
                    "site_id": {"type": "text"},
                    "status": {"type": "text"},
                    "last_heartbeat": {"type": "timestamp"},
                    "maintenance_required": {"type": "boolean"}
                }
            }
        }
    }
    
    # Create indices
    for index_name, mapping in sample_indices.items():
        try:
            if opensearch_client.create_index(index_name, mapping):
                print(f"✅ Created index: {index_name}")
            else:
                print(f"❌ Failed to create index: {index_name}")
        except Exception as e:
            print(f"⚠️  Index {index_name} might already exist: {e}")
    
    # Sample documents for logs index
    log_documents = [
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "message": "User login successful",
            "service": "auth-service",
            "user_id": "user123"
        },
        {
            "timestamp": "2024-01-15T10:31:00Z",
            "level": "ERROR",
            "message": "Database connection failed",
            "service": "db-service",
            "user_id": "system"
        },
        {
            "timestamp": "2024-01-15T10:32:00Z",
            "level": "WARN",
            "message": "High memory usage detected",
            "service": "monitoring",
            "user_id": "system"
        },
        {
            "timestamp": "2024-01-15T10:33:00Z",
            "level": "INFO",
            "message": "Payment processed successfully",
            "service": "payment-service",
            "user_id": "user456"
        },
        {
            "timestamp": "2024-01-15T10:34:00Z",
            "level": "ERROR",
            "message": "API rate limit exceeded",
            "service": "api-gateway",
            "user_id": "user789"
        }
    ]
    
    # Sample documents for products index
    product_documents = [
        {
            "name": "Laptop Pro X1",
            "category": "electronics",
            "price": 1299.99,
            "description": "High-performance laptop with 16GB RAM and 512GB SSD",
            "tags": ["laptop", "computer", "electronics"],
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "name": "Wireless Headphones",
            "category": "audio",
            "price": 199.99,
            "description": "Noise-cancelling wireless headphones with 30-hour battery life",
            "tags": ["headphones", "audio", "wireless"],
            "created_at": "2024-01-02T00:00:00Z"
        },
        {
            "name": "Smartphone Galaxy S24",
            "category": "mobile",
            "price": 899.99,
            "description": "Latest smartphone with advanced camera system",
            "tags": ["phone", "mobile", "smartphone"],
            "created_at": "2024-01-03T00:00:00Z"
        },
        {
            "name": "Coffee Maker Deluxe",
            "category": "home",
            "price": 89.99,
            "description": "Programmable coffee maker with built-in grinder",
            "tags": ["coffee", "kitchen", "appliance"],
            "created_at": "2024-01-04T00:00:00Z"
        },
        {
            "name": "Fitness Tracker Pro",
            "category": "health",
            "price": 149.99,
            "description": "Water-resistant fitness tracker with heart rate monitor",
            "tags": ["fitness", "health", "tracker"],
            "created_at": "2024-01-05T00:00:00Z"
        }
    ]
    
    # Sample documents for orders index
    order_documents = [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "total_amount": 1499.98,
            "status": "completed",
            "items": [
                {"product_id": "PROD-001", "quantity": 1, "price": 1299.99},
                {"product_id": "PROD-002", "quantity": 1, "price": 199.99}
            ],
            "created_at": "2024-01-10T14:30:00Z"
        },
        {
            "order_id": "ORD-002",
            "customer_id": "CUST-002",
            "total_amount": 899.99,
            "status": "processing",
            "items": [
                {"product_id": "PROD-003", "quantity": 1, "price": 899.99}
            ],
            "created_at": "2024-01-11T09:15:00Z"
        },
        {
            "order_id": "ORD-003",
            "customer_id": "CUST-003",
            "total_amount": 239.98,
            "status": "shipped",
            "items": [
                {"product_id": "PROD-004", "quantity": 1, "price": 89.99},
                {"product_id": "PROD-005", "quantity": 1, "price": 149.99}
            ],
            "created_at": "2024-01-12T16:45:00Z"
        }
    ]

    # Sample documents for fuel_transactions index
    fuel_transaction_documents = [
        {
            "transaction_id": "TXN-001",
            "timestamp": "2024-01-15T10:30:00Z",
            "device_id": "DEV_001",
            "nozzle_id": "NOZ_001",
            "site_id": "SITE_001",
            "payment_method": "credit_card",
            "amount": 45.67,
            "volume_dispensed": 12.5,
            "fuel_type": "regular",
            "status": "completed"
        },
        {
            "transaction_id": "TXN-002",
            "timestamp": "2024-01-15T10:31:00Z",
            "device_id": "DEV_001",
            "nozzle_id": "NOZ_002",
            "site_id": "SITE_001",
            "payment_method": "cash",
            "amount": 30.00,
            "volume_dispensed": 10.0,
            "fuel_type": "diesel",
            "status": "completed"
        },
        {
            "transaction_id": "TXN-003",    
            "timestamp": "2024-01-15T10:32:00Z",
            "device_id": "DEV_002",
            "nozzle_id": "NOZ_003",
            "site_id": "SITE_002",
            "payment_method": "credit_card",
            "amount": 25.00,
            "volume_dispensed": 8.0,
            "fuel_type": "premium",
            "status": "completed"
        },
        {
            "transaction_id": "TXN-004",
            "timestamp": "2024-01-15T10:33:00Z",
            "device_id": "DEV_003",
            "nozzle_id": "NOZ_004",
            "site_id": "SITE_003",
            "payment_method": "cash",
            "amount": 15.00,
            "volume_dispensed": 5.0,
            "fuel_type": "regular",
            "status": "completed"
        }
    ]

    # Sample documents for device_status index
    device_status_documents = [
        {
            "event_id": "EVENT-001",
            "timestamp": "2024-01-15T10:30:00Z",
            "device_id": "DEV_001",
            "site_id": "SITE_001",
            "status": "online",
            "last_heartbeat": "2025-07-09T10:30:00Z",
            "maintenance_required": False
        },
        {
            "event_id": "EVENT-002",
            "timestamp": "2024-01-15T10:31:00Z",
            "device_id": "DEV_002",
            "site_id": "SITE_002",
            "status": "offline",    
            "last_heartbeat": "2025-07-10T10:31:00Z",
            "maintenance_required": True
        }
    ]
    
    # Index documents
    print("\n📝 Indexing sample documents...")
    
    # Index documents
    print("\n📝 Indexing sample documents...")
    
    # Index log documents
    for doc in log_documents:
        try:
            doc_id = opensearch_client.index_document("logs", doc)
            print(f"✅ Indexed log document: {doc_id}")
        except Exception as e:
            print(f"❌ Failed to index log document: {e}")
    
    # Index product documents
    for doc in product_documents:
        try:
            doc_id = opensearch_client.index_document("products", doc)
            print(f"✅ Indexed product document: {doc_id}")
        except Exception as e:
            print(f"❌ Failed to index product document: {e}")
    
    # Index order documents
    for doc in order_documents:
        try:
            doc_id = opensearch_client.index_document("orders", doc)
            print(f"✅ Indexed order document: {doc_id}")
        except Exception as e:
            print(f"❌ Failed to index order document: {e}")

    for doc in fuel_transaction_documents:
        try:
            doc_id = opensearch_client.index_document("fuel_transactions", doc)
            print(f"✅ Indexed fuel transaction document: {doc_id}")
        except Exception as e:
            print(f"❌ Failed to index fuel transaction document: {e}")

    for doc in device_status_documents:
        try:
            doc_id = opensearch_client.index_document("device_status", doc)
            print(f"✅ Indexed device status document: {doc_id}")
        except Exception as e:
            print(f"❌ Failed to index device status document: {e}")

    
    # Wait a moment for indexing to complete
    time.sleep(2)
    
    # Show summary
    print("\n📊 Sample data summary:")
    try:
        indices = opensearch_client.list_indices()
        for index_name in ["logs", "products", "orders"]:
            if index_name in indices:
                count = opensearch_client.get_index_count(index_name)
                print(f"  - {index_name}: {count} documents")
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
    
    print("\n✅ Sample data creation completed!")

if __name__ == "__main__":
    create_sample_data() 