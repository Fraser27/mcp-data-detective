# MCP Data Detective System 

This platform serves as a bridge between AI and the data universe.
<img width="2870" height="1768" alt="image" src="https://github.com/user-attachments/assets/d1dc9145-3c0d-4197-96bc-4d983640eaaf" />

## Connected MCPs
<img width="1433" height="898" alt="Screenshot 2025-07-24 at 5 13 45 pm" src="https://github.com/user-attachments/assets/efe4a3a1-5714-461b-a839-6e42edf35ef9" />

## MCP Orchestration
<img width="1433" height="897" alt="Screenshot 2025-07-25 at 3 13 23 pm" src="https://github.com/user-attachments/assets/e407aae3-9cd2-4a8b-8867-b5ea7353e007" />


## 🏗️ Architecture


The system consists of two independent MCP servers:

1. **MySQL MCP Server** (`mysql-mcp-server/`) - Database operations and queries
2. **OpenSearch MCP Server** (`opensearch-mcp-server/`) - Search and analytics operations
3. **Github MCP Server** (`https://smithery.ai/server/@smithery-ai/github`) - Search for public github repositories
4. **Browser MCP Server** (`https://docs.browsermcp.io/setup-server`) - Control your Browser


## 🚀 Configuring MCP Servers
This application currently demonstrates integration with 4 MCP servers : 
* MySQL MCP Server (Locally built and deployed with Sample DB)
* OpenSearch MCP Server (Locally built and deployed with Sample DB)
* Browser MCP Server (External MCP)
* Github MCP Server (External via Smithery)
#### Configurations for these MCP servers can be found in mcp_servers.json in backend folder


##  🐳 Docker Deployment for Local MCP servers,

#### MySQL MCP Server
```bash
cd mysql-mcp-server
docker build -t "mysql-mcp-server" 
docker run -p 8000:8000 -p 3306:3306 mysql-mcp-server
```

#### OpenSearch MCP Server
```bash
cd opensearch-mcp-server
docker build -t "opensearch-mcp-server" .
docker run -p 8001:8000 -p 9200:9200 opensearch-mcp-server
```

## ⚡ Quickstart

### Prerequisites
- Docker and Docker Compose
- Node.js (v16+)
- Python (v3.8+)

### Quick Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/Fraser27/mcp-data-detective.git
   cd mcp-data-detective
   ```

2. **Start the MCP Client frontend and Backend**
   ```bash
   chmod +x start_system.sh
   ./start_system.sh
   ```

3. **Access the MCP application on port 3000**
   - Open http://localhost:3000 in your browser
   - The system will automatically connect to all configured MCP servers


## 📊 Frontend MCP Client application

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

## 📝 Configuration

### Environment Variables
Each server has its own configuration:
- `mysql-mcp-server/.env` - Database connection settings
- `opensearch-mcp-server/.env` - OpenSearch connection settings

## 🔧 Troubleshooting


## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the individual server READMEs
2. Review the example usage scripts
3. Open an issue on GitHub

---

**Happy investigating! 🚀**
