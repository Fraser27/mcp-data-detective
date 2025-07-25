# MySQL MCP Server with Strands Agents SDK

A Model Context Protocol (MCP) server that provides MySQL database connectivity and querying capabilities using the Strands Agents framework. This server allows AI agents to safely interact with MySQL databases through a comprehensive set of tools.

## Features

- **Safe Database Access**: Only SELECT queries allowed for security
- **Comprehensive Database Tools**: List tables, describe schemas, execute queries, and more
- **Built with Strands SDK**: Leverages the powerful Strands Agents framework
- **Environment-based Configuration**: Secure credential management
- **Interactive Mode**: Test and interact with your database directly
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

## Available Tools

- `test_mysql_connection`: Test database connectivity
- `list_mysql_tables`: List all tables in the database
- `describe_mysql_table`: Get detailed table schema and metadata
- `execute_mysql_query`: Execute SELECT queries with safety restrictions
- `get_mysql_table_sample`: Get sample data from tables
- `get_mysql_table_count`: Get row counts for tables
- `search_mysql_table`: Search for specific terms within table columns
- `get_mysql_database_summary`: Get comprehensive database overview

## Run the MySQL DB
    docker build -t mysql-image .
- Start the docker from the docker desktop once its built

## OR to replace the username password
    docker run -d -p 3306:3306 \
      -e MYSQL_ROOT_PASSWORD=your_root_password \
      -e MYSQL_DATABASE=your_database_name \
      -e MYSQL_USER=your_user \
      -e MYSQL_PASSWORD=your_user_password \
      --name mysql-container \
      mysql-image


## Installation

1. **Clone or create the project directory:**
   ```bash
   mkdir mysql-mcp-server && cd mysql-mcp-server
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your MySQL connection details
   ```

## Configuration

Create a `.env` file with your MySQL connection details:

```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# Optional SSL Configuration
MYSQL_SSL_DISABLED=false
MYSQL_SSL_CA_PATH=
MYSQL_SSL_CERT_PATH=
MYSQL_SSL_KEY_PATH=
```


## Usage


### Interactive Mode

Run the server in interactive mode to test and explore your database:

```bash
python server.py
```

This will start an interactive session where you can ask questions about your MySQL database:

```
🔗 MySQL MCP Server (Strands Agents)
==================================================
Type your questions about the MySQL database.
Type 'quit' or 'exit' to stop the server.
==================================================

💬 Ask about your MySQL database: What tables are in my database?

🤖 Processing your request...
------------------------------

📊 Response:
I'll check what tables are available in your MySQL database.

[Tool usage and results will be displayed here]
```

### Programmatic Usage

You can also use the MySQL agent programmatically:

```python
from mysql_mcp_server import create_mysql_agent

# Create the MySQL agent
agent = create_mysql_agent()

# Ask questions about your database
response = agent("What tables are in my database?")
print(response.message)

# Execute specific queries
response = agent("Show me a sample of data from the users table")
print(response.message)

# Get database summary
response = agent("Give me an overview of my entire database")
print(response.message)
```

### Example Queries

Here are some example questions you can ask the MySQL agent:

- "What tables are in my database?"
- "Describe the structure of the users table"
- "Show me a sample of data from the products table"
- "How many rows are in the orders table?"
- "Search for customers with 'gmail' in their email"
- "Give me an overview of my entire database"
- "Execute this query: SELECT * FROM users WHERE created_at > '2024-01-01'"

## Security Features

- **Query Restrictions**: Only SELECT queries are allowed
- **Result Limits**: Query results are automatically limited to prevent overwhelming responses
- **Parameter Validation**: All inputs are validated before execution
- **Connection Management**: Secure connection handling with proper cleanup
- **SSL Support**: Optional SSL/TLS encryption for database connections

## Architecture

The MCP server is built using several key components:

- **`server.py`**: Main server application and agent configuration
- **`mysql_tools.py`**: Strands SDK tools for MySQL operations
- **`database.py`**: Database connection management and utilities
- **Environment Configuration**: Secure credential management

## Development

### Project Structure

```
mysql-mcp-server/
├── __init__.py              # Package initialization
├── server.py                # Main server application
├── mysql_tools.py           # MySQL tools for Strands agents
├── database.py              # Database connection utilities
├── requirements.txt         # Python dependencies
├── .env.example            # Environment configuration template
├── setup.py                # Package setup script
└── README.md               # This file
```

### Adding New Tools

To add new MySQL tools, create functions in `mysql_tools.py` using the `@tool` decorator:

```python
from strands import tool
from database import db

@tool
def your_custom_tool(param: str) -> str:
    """
    Description of your custom tool.
    
    Args:
        param (str): Description of parameter
        
    Returns:
        str: Description of return value
    """
    try:
        # Your implementation here
        result = db.execute_query("SELECT * FROM your_table WHERE column = %s", (param,))
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

Then add your tool to the `mysql_tools` list in `server.py`.

## Troubleshooting

### Connection Issues

1. **Check your `.env` file**: Ensure all MySQL connection details are correct
2. **Test connectivity**: Use the `test_mysql_connection` tool to verify connection
3. **Check MySQL server**: Ensure MySQL server is running and accessible
4. **Firewall settings**: Verify that the MySQL port (default 3306) is accessible

### Common Errors

- **"Access denied"**: Check username and password in `.env`
- **"Unknown database"**: Verify the database name exists
- **"Connection refused"**: Check if MySQL server is running and host/port are correct
- **SSL errors**: Try setting `MYSQL_SSL_DISABLED=true` in `.env`

### Logging

Enable debug logging for more detailed information:

```python
import logging
logging.getLogger("mysql_mcp_server").setLevel(logging.DEBUG)
```

## Requirements

- Python 3.8+
- MySQL 5.7+ or 8.0+
- Strands Agents SDK
- mysql-connector-python

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error details
3. Open an issue on the project repository
