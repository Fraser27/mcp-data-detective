import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../contexts/ChatContext';
import { Send, Trash2, Bot, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ChatMessage from './ChatMessage';
import ConnectionStatus from './ConnectionStatus';
import TabSessionIndicator from './TabSessionIndicator';

function ChatInterface() {
  const { 
    messages, 
    isLoading, 
    isConnected, 
    sendMessage, 
    clearMessages,
    availableTools,
    checkConnection,
    socketRef 
  } = useChat();
  
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const message = inputValue.trim();
    setInputValue('');
    setIsTyping(true);

    try {
      await sendMessage(message);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleClearChat = () => {
    // Clear messages in the state
    clearMessages();
    
    // Access the socket reference directly from the destructured props
    const { current: socket } = socketRef;
    
    // Disconnect the websocket if it exists
    if (socket) {
      socket.disconnect();
      
      // Reconnect after a short delay
      setTimeout(() => {
        socket.connect();
        checkConnection();
      }, 500);
    }
  };

  const exampleQueries = [
    "List all tables in the MySQL database",
    "Show me a sample of data from the users table",
    "How many rows are in the products table in MySQL?",
    "Go to google and search for latest news",
    "Get a summary of the MySQL database",
    "Create a chart showing user registration trends",
    "What are the top 10 products by sales?",
    "Tell me about serverless-rag-demo repo in aws-samples org on Github"
  ];

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MCP Data Detective</h1>
            <p className="text-sm text-gray-600">
              Analyze multiple data sources. Find hidden insights.
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <TabSessionIndicator />
            <ConnectionStatus isConnected={isConnected} />
            <button
              onClick={handleClearChat}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Chat
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <Bot className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome to Data Detective!
            </h3>
            <p className="text-gray-600 mb-6 max-w-md">
              All you need is English. I can help you query all your databases, analyze data, and create dashboards. 
              Try asking me a question about your data.
            </p>
            
            {/* Example Queries */}
            <div className="w-full max-w-2xl">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Try these examples:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {exampleQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(query)}
                    className="text-left p-3 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {Array.isArray(messages) && messages.length > 0 ? (
              messages.map((message, index) => (
                <ChatMessage key={message.id || `message-${index}`} message={message} />
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                <p>No messages to display</p>
              </div>
            )}
            
            {/* Typing indicator */}
            {isTyping && (
              <div className="flex items-center space-x-2 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
                <Loader2 className="h-5 w-5 text-primary-500 animate-spin" />
                <span className="text-gray-600">Processing your request...</span>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about your database, create dashboards, or analyze data..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
              rows="1"
              disabled={isLoading || !isConnected}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading || !isConnected}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </form>
        
        {!isConnected && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              ⚠️ Not connected to MCP servers. Please ensure your servers are running.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatInterface; 