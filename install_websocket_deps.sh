#!/bin/bash

echo "Installing WebSocket dependencies..."

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install flask-socketio==5.3.6

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ../frontend
npm install socket.io-client@4.7.2

echo "WebSocket dependencies installed successfully!"
echo ""
echo "To start the system:"
echo "1. Backend: cd backend && python app.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "The system now uses WebSocket connections for real-time streaming!" 