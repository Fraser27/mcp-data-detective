# MCP Dashboarding System

A comprehensive system for managing and monitoring MCP (Model Context Protocol) servers.

## 🏗️ Architecture

The system consists of two independent MCP servers:

1. **MySQL MCP Server** (`mysql-mcp-server/`) - Database operations and queries
2. **OpenSearch MCP Server** (`opensearch-mcp-server/`) - Search and analytics operations

## 🚀 Quick Start

### Option 1: Start All Services
```bash
# Start the entire system
./start_system.sh
```

### Option 2: Start Individual Services

#### MySQL MCP Server
```bash
cd mysql-mcp-server
python mysql_mcp_server.py
```

#### OpenSearch MCP Server
```bash
cd opensearch-mcp-server
python opensearch_mcp_server.py
```

## 📊 Monitoring Dashboards

- **Frontend Dashboard**: http://localhost:3000 - Main application dashboard

## 📁 Project Structure

```
mcp-dashboarding/
├── mysql-mcp-server/          # MySQL database operations
├── opensearch-mcp-server/     # Search and analytics
├── frontend/                  # React dashboard
├── backend/                   # Flask backend
└── start_system.sh           # System startup script
```

## 🐳 Docker Deployment

```bash
# Build and run all services
docker-compose -f docker-compose.yml up -d
```

## 🧪 Testing

### Test MySQL Server
```bash
cd mysql-mcp-server
python -c "from mysql_mcp_server import *; print('MySQL MCP Server ready')"
```

## 📝 Configuration

### Environment Variables
Each server has its own configuration:
- `mysql-mcp-server/.env` - Database connection settings
- `opensearch-mcp-server/.env` - OpenSearch connection settings

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**
   - MySQL MCP Server: 8000
   - OpenSearch MCP Server: 8002

2. **Connection Issues**
   - Verify all services are running
   - Check firewall settings
   - Review environment variables

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the individual server READMEs
2. Review the example usage scripts
3. Open an issue on GitHub

---

**Happy Monitoring! 🚀**