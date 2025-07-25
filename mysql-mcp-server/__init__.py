"""
MySQL MCP Server using Strands Agents SDK

A Model Context Protocol server that provides MySQL database connectivity
and querying capabilities through the Strands Agents framework.
"""

from .server import create_mysql_agent
from .mysql_tools import (
    test_mysql_connection,
    list_mysql_tables,
    describe_mysql_table,
    execute_mysql_query,
    get_mysql_table_sample,
    get_mysql_table_count,
    search_mysql_table,
    get_mysql_database_summary
)

__version__ = "1.0.0"
__all__ = [
    "create_mysql_agent",
    "test_mysql_connection",
    "list_mysql_tables", 
    "describe_mysql_table",
    "execute_mysql_query",
    "get_mysql_table_sample",
    "get_mysql_table_count",
    "search_mysql_table",
    "get_mysql_database_summary"
]
