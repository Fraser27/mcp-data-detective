import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  BarChart3, 
  Settings, 
  Database, 
  Zap,
  Menu,
  X,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  History
} from 'lucide-react';
import axios from 'axios';

function Sidebar({ sidebarOpen, setSidebarOpen, windowWidth }) {
  const location = useLocation();
  const [mcpServers, setMcpServers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const sidebarRef = useRef(null);
  
  // Prevent sidebar position from changing when sending messages
  useEffect(() => {
    // Only apply fixed positioning on mobile
    if (windowWidth < 1024) { // lg breakpoint in Tailwind is 1024px
      if (sidebarOpen) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [sidebarOpen, windowWidth]);

  const navigation = [
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Dashboard History', href: '/dashboard-history', icon: History },
  ];

  // Fetch MCP server status
  const fetchMcpStatus = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/mcp-status');
      const servers = response.data.servers;
      
      // Dynamically create server list from API response
      const serverList = Object.entries(servers).map(([serverId, serverData]) => {
        // Map server types to icons (you can extend this mapping as needed)
        const iconMap = {
          mysql: Database,
          opensearch: Zap,
          // Add more mappings as needed
          default: Database // fallback icon
        };
        
        return {
          id: serverId,
          name: serverData.name,
          status: serverData.status,
          icon: iconMap[serverId] || iconMap.default,
          port: serverData.port
        };
      });
      
      setMcpServers(serverList);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch MCP status:', error);
      // Set empty array as fallback when API fails
      setMcpServers([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch status on component mount and every 30 seconds
  useEffect(() => {
    fetchMcpStatus();
    const interval = setInterval(fetchMcpStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div 
        ref={sidebarRef}
        className={`
        fixed inset-y-0 left-0 z-50 bg-white shadow-lg transform transition-all duration-300 ease-in-out
        ${sidebarOpen ? 'w-64 translate-x-0' : 'w-16 -translate-x-48 lg:translate-x-0'}
        lg:static lg:inset-0 lg:translate-y-0
      `}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className={`text-xl font-bold text-gray-900 transition-opacity duration-300 ${
                sidebarOpen ? 'opacity-100' : 'opacity-0'
              }`}>
                MCP Data Detective
              </h1>

              <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={sidebarOpen ? "hidden" : "flex p-2 rounded-md text-gray-400 hover:bg-gray-100"}
              title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              >
               {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
              </button>
              

            </div>
          </div>
          <div className="flex items-center space-x-2">
            {/* Desktop toggle button */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={!sidebarOpen ? "hidden" : "flex p-2 rounded-md text-gray-400 hover:bg-gray-100"}
              title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </button>
            {/* Mobile close button */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-y-auto">
          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors
                    ${isActive 
                      ? 'bg-primary-100 text-primary-700' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSidebarOpen(false);
                  }}
                  title={!sidebarOpen ? item.name : ''}
                >
                  <item.icon className={`
                    h-5 w-5 flex-shrink-0
                    ${sidebarOpen ? 'mr-3' : 'mx-auto'}
                    ${isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}
                  `} />
                  <span className={`transition-opacity duration-300 ${
                    sidebarOpen ? 'opacity-100' : 'opacity-0'
                  }`}>
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </nav>

          {/* MCP Server Status */}
          <div className={`border-t border-gray-200 transition-all duration-300 ${
            sidebarOpen ? 'p-4' : 'p-2'
          }`}>
            <div className={`flex items-center justify-between mb-3 ${
              !sidebarOpen ? 'justify-center' : ''
            }`}>
              <h3 className={`text-xs font-semibold text-gray-500 uppercase tracking-wider transition-opacity duration-300 ${
                sidebarOpen ? 'opacity-100' : 'opacity-0'
              }`}>
                MCP Servers
              </h3>
              <button
                onClick={fetchMcpStatus}
                disabled={isLoading}
                className={`p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 disabled:opacity-50 ${
                  !sidebarOpen ? 'mx-auto' : ''
                }`}
                title="Refresh status"
              >
                <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="space-y-2">
              {mcpServers.map((server) => (
                <div key={server.id} className={`flex items-center justify-between ${
                  !sidebarOpen ? 'justify-center' : ''
                }`}>
                  <div className="flex items-center">
                    <server.icon className={`h-4 w-4 text-gray-400 ${
                      sidebarOpen ? 'mr-2' : 'mx-auto'
                    }`} />
                    <div className={`transition-opacity duration-300 ${
                      sidebarOpen ? 'opacity-100' : 'opacity-0'
                    }`}>
                      <span className="text-sm text-gray-700">{server.name}</span>
                      <div className="text-xs text-gray-500">Port {server.port}</div>
                    </div>
                  </div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium transition-opacity duration-300 ${
                    server.status === 'connected' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  } ${sidebarOpen ? 'opacity-100' : 'opacity-0'}`}>
                    {server.status === 'connected' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              ))}
            </div>
            {lastUpdated && (
              <div className={`mt-2 text-xs text-gray-400 transition-opacity duration-300 ${
                sidebarOpen ? 'opacity-100' : 'opacity-0'
              }`}>
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>

          {/* Settings */}
          <div className={`border-t border-gray-200 transition-all duration-300 ${
            sidebarOpen ? 'p-4' : 'p-2'
          }`}>
            <Link
              to="/settings"
              className="group flex items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
              title={!sidebarOpen ? 'Settings' : ''}
            >
              <Settings className={`h-5 w-5 text-gray-400 group-hover:text-gray-500 ${
                sidebarOpen ? 'mr-3' : 'mx-auto'
              }`} />
              <span className={`transition-opacity duration-300 ${
                sidebarOpen ? 'opacity-100' : 'opacity-0'
              }`}>
                Settings
              </span>
            </Link>
          </div>
        </div>
      </div>

      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 bg-white shadow-lg"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>


    </>
  );
}

export default Sidebar; 