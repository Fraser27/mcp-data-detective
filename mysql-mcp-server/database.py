"""
MySQL Database Connection and Utilities
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MySQLConnection:
    """MySQL database connection manager"""

    def __init__(self):
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
            "database": os.getenv("MYSQL_DATABASE"),
            "autocommit": True,
            "charset": "utf8mb4",
            "use_unicode": True,
        }

        # SSL Configuration
        if os.getenv("MYSQL_SSL_DISABLED", "false").lower() != "true":
            ssl_config = {}
            if os.getenv("MYSQL_SSL_CA_PATH"):
                ssl_config["ca"] = os.getenv("MYSQL_SSL_CA_PATH")
            if os.getenv("MYSQL_SSL_CERT_PATH"):
                ssl_config["cert"] = os.getenv("MYSQL_SSL_CERT_PATH")
            if os.getenv("MYSQL_SSL_KEY_PATH"):
                ssl_config["key"] = os.getenv("MYSQL_SSL_KEY_PATH")

            if ssl_config:
                self.config["ssl"] = ssl_config

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            print("Successfully connected to MySQL database")
            yield connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
                logger.debug("MySQL connection closed")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def execute_query(
        self, query: str, params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                return results
        except Error as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount
                cursor.close()
                return affected_rows
        except Error as e:
            logger.error(f"Update execution failed: {e}")
            raise

    def get_table_schema(
        self, table_name: str, schema_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get schema information for a specific table"""
        target_schema = schema_name or self.config["database"]
        
        try:
            # Try INFORMATION_SCHEMA first
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY,
                EXTRA,
                COLUMN_COMMENT,
                ORDINAL_POSITION,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            results = self.execute_query(query, (target_schema, table_name))
            if results:
                return results
        except Exception as e:
            print(f"INFORMATION_SCHEMA columns query failed: {e}")
        
        # Fallback to DESCRIBE/SHOW COLUMNS
        try:
            print(f"Falling back to DESCRIBE for table: {target_schema}.{table_name}")
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Switch to target schema if needed
                if target_schema != self.config["database"]:
                    cursor.execute(f"USE `{target_schema}`")
                
                cursor.execute(f"DESCRIBE `{table_name}`")
                raw_results = cursor.fetchall()
                cursor.close()
                
                # Convert DESCRIBE output to INFORMATION_SCHEMA-like format
                results = []
                for i, row in enumerate(raw_results):
                    results.append({
                        'COLUMN_NAME': row['Field'],
                        'DATA_TYPE': row['Type'].split('(')[0],  # Extract base type
                        'COLUMN_TYPE': row['Type'],
                        'IS_NULLABLE': 'YES' if row['Null'] == 'YES' else 'NO',
                        'COLUMN_DEFAULT': row['Default'],
                        'COLUMN_KEY': row['Key'],
                        'EXTRA': row['Extra'],
                        'COLUMN_COMMENT': '',  # Not available in DESCRIBE
                        'ORDINAL_POSITION': i + 1,
                        'CHARACTER_MAXIMUM_LENGTH': None,  # Not available in DESCRIBE
                        'NUMERIC_PRECISION': None,  # Not available in DESCRIBE
                        'NUMERIC_SCALE': None  # Not available in DESCRIBE
                    })
                return results
        except Exception as e:
            print(f"DESCRIBE also failed: {e}")
            return []

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all schemas/databases in the MySQL instance"""
        try:
            # Try INFORMATION_SCHEMA first (works with full privileges)
            query = """
            SELECT 
                SCHEMA_NAME as schema_name,
                DEFAULT_CHARACTER_SET_NAME as charset,
                DEFAULT_COLLATION_NAME as collation
            FROM INFORMATION_SCHEMA.SCHEMATA 
            WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            ORDER BY SCHEMA_NAME
            """
            results = self.execute_query(query)
            if results:  # If we got results, return them
                return results
        except Exception as e:
            print(f"INFORMATION_SCHEMA query failed: {e}")
        
        # Fallback to SHOW DATABASES (works with limited privileges)
        try:
            print("Falling back to SHOW DATABASES")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW DATABASES")
                raw_results = cursor.fetchall()
                cursor.close()
                
                # Filter out system databases and format results
                results = []
                for (db_name,) in raw_results:
                    if db_name not in ('information_schema', 'performance_schema', 'mysql', 'sys'):
                        results.append({
                            'schema_name': db_name,
                            'charset': 'unknown',  # Can't get this with SHOW DATABASES
                            'collation': 'unknown'
                        })
                return results
        except Exception as e:
            print(f"SHOW DATABASES also failed: {e}")
            # Return at least the current database
            return [{
                'schema_name': self.config['database'],
                'charset': 'unknown',
                'collation': 'unknown'
            }]

    def list_tables(self, schema_name: Optional[str] = None) -> List[str]:
        """List all tables in the database or specific schema"""
        target_schema = schema_name or self.config["database"]
        
        try:
            # Try INFORMATION_SCHEMA first
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """
            results = self.execute_query(query, (target_schema,))
            if results:  # If we got results, return them
                return [row["TABLE_NAME"] for row in results]
        except Exception as e:
            print(f"INFORMATION_SCHEMA query failed for tables: {e}")
        
        # Fallback to SHOW TABLES
        try:
            print(f"Falling back to SHOW TABLES for schema: {target_schema}")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Switch to the target database if different from current
                if target_schema != self.config["database"]:
                    cursor.execute(f"USE `{target_schema}`")
                
                cursor.execute("SHOW TABLES")
                raw_results = cursor.fetchall()
                cursor.close()
                
                return [table[0] for table in raw_results]
        except Exception as e:
            print(f"SHOW TABLES also failed: {e}")
            return []

    def list_tables_by_schema(self) -> Dict[str, List[str]]:
        """List all tables grouped by schema"""
        print("Starting list_tables_by_schema with privilege-aware approach")
        
        try:
            # Try INFORMATION_SCHEMA approach first
            query = """
            SELECT 
                TABLE_SCHEMA as schema_name,
                TABLE_NAME as table_name
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            results = self.execute_query(query)
            print(f"INFORMATION_SCHEMA query returned {len(results)} results")
            
            if results:  # If we got results, use them
                schemas = {}
                for row in results:
                    schema_name = row["schema_name"]
                    table_name = row["table_name"]
                    if schema_name not in schemas:
                        schemas[schema_name] = []
                    schemas[schema_name].append(table_name)
                print(f"SUCCESS: Found schemas via INFORMATION_SCHEMA: {list(schemas.keys())}")
                return schemas
        except Exception as e:
            print(f"INFORMATION_SCHEMA approach failed: {e}")
        
        # Fallback approach: Use SHOW commands
        print("Falling back to SHOW commands approach")
        schemas = {}
        
        try:
            # Get list of accessible databases
            available_schemas = self.list_schemas()
            print(f"Available schemas from list_schemas(): {[s['schema_name'] for s in available_schemas]}")
            
            # For each schema, try to get its tables
            for schema_info in available_schemas:
                schema_name = schema_info['schema_name']
                try:
                    tables = self.list_tables(schema_name)
                    if tables:  # Only include schemas that have tables
                        schemas[schema_name] = tables
                        print(f"Found {len(tables)} tables in schema '{schema_name}': {tables}")
                except Exception as schema_error:
                    print(f"Could not access tables in schema '{schema_name}': {schema_error}")
                    continue
            
            print(f"FALLBACK SUCCESS: Final schemas dict: {schemas}")
            return schemas
            
        except Exception as e:
            print(f"Fallback approach also failed: {e}")
            # Last resort: return current database only
            current_db = self.config["database"]
            try:
                tables = self.list_tables(current_db)
                return {current_db: tables} if tables else {}
            except:
                return {}

    def get_table_info(
        self, table_name: str, schema_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive information about a table"""
        target_schema = schema_name or self.config["database"]

        # Get basic table info
        table_info_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            ENGINE,
            TABLE_ROWS,
            DATA_LENGTH,
            INDEX_LENGTH,
            TABLE_COMMENT,
            CREATE_TIME,
            UPDATE_TIME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """

        table_info = self.execute_query(table_info_query, (target_schema, table_name))
        if not table_info:
            return {}

        # Get column information
        columns = self.get_table_schema(table_name, target_schema)

        # Get indexes
        index_query = """
        SELECT 
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE,
            INDEX_TYPE,
            CARDINALITY
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """
        indexes = self.execute_query(index_query, (target_schema, table_name))

        # Get foreign key constraints
        fk_query = """
        SELECT 
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_SCHEMA,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
        """
        foreign_keys = self.execute_query(fk_query, (target_schema, table_name))

        return {
            "table_info": table_info[0],
            "columns": columns,
            "indexes": indexes,
            "foreign_keys": foreign_keys,
        }


# Global database instance
db = MySQLConnection()