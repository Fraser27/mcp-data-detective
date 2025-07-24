#!/usr/bin/env python3
"""
Flask API for MCP Dashboard Chatbot
Provides REST endpoints and SSE streaming for the React frontend to interact with MCP servers.
"""

from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
import asyncio
import json
import logging
from datetime import datetime
import sys
import os
import pathlib

# Import from reorganized modules
from database.database_mcp_clients import MCPClientChatbot
import threading
import queue
import time
# Configure logging
import logging.config
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Get logging level from environment variable or default to ERROR
log_level = os.environ.get('PYTHONLOG', 'ERROR')

# Configure logging with more control
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': log_level,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': log_level,
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'logs/backend.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': log_level,
            'propagate': True
        },
        'socketio': {
            'handlers': ['default', 'file'],
            'level': 'ERROR',  # Always keep socketio at ERROR level
            'propagate': False,
        },
        'engineio': {
            'handlers': ['default', 'file'],
            'level': 'ERROR',  # Always keep engineio at ERROR level
            'propagate': False,
        },
        'werkzeug': {
            'handlers': ['default', 'file'],
            'level': log_level,
            'propagate': False,
        },
    }
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)
# Initialize SocketIO with CORS support
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# Global chatbot instance
chatbot = None
chatbot_lock = threading.Lock()


def start_chatbot():
    """Start the MCP chatbot in a separate thread."""
    global chatbot

    def run_chatbot():
        global chatbot
        sse_urls = []
        try:
            logger.info("Starting MCP chatbot initialization")
            # Load MCP server details from JSON file
            try:
                #config_path = os.path.join(os.path.dirname(__file__), 'mcp_servers.json')
                with open('mcp_servers.json', 'r') as f:
                    config = json.load(f)
                    sse_urls = config.get('servers', [])
                logger.info(f"Loaded {len(sse_urls)} MCP servers from configuration file")
            except Exception as e:
                logger.error(f"Failed to load MCP servers from config file: {e}")
                logger.error("No MCP servers configured, chatbot will not be initialized")
                sys.exit(0)
                
                
            logger.info("Creating MCPClientChatbot instance")
            chatbot = MCPClientChatbot(sse_urls=sse_urls)
            # Start the chatbot (this will run in the background)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start the chatbot with full initialization
            logger.info("Starting chatbot initialization")
            loop.run_until_complete(chatbot.start())
                
        except Exception as e:
            logger.error(f"Failed to start chatbot: {e}")
            logger.error(f"Error details: {str(e)}")
            logger.info("Running in demo mode without MCP servers")
            chatbot = None

    # Start chatbot in a separate thread
    thread = threading.Thread(target=run_chatbot, daemon=True)
    thread.start()
    
    # Give the thread a moment to initialize
    time.sleep(1)
    
    # Check if chatbot was initialized successfully
    with chatbot_lock:
        if chatbot is None:
            logger.error("Chatbot failed to initialize")
        else:
            logger.info("Chatbot thread started successfully")

@app.route("/api/dashboard/<filename>", methods=["GET"])
def serve_dashboard(filename):
    """Serve generated dashboard HTML files."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        dashboard_path = project_root / "generated_dashboards" / filename
        if dashboard_path.exists():
            with open(dashboard_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return html_content, 200, {"Content-Type": "text/html"}
        else:
            return jsonify({"error": "Dashboard not found"}), 404
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return jsonify({"error": "Failed to serve dashboard"}), 500

@app.route("/api/dashboards/history", methods=["GET"])
def get_dashboard_history():
    """Get list of all generated dashboards."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        dashboard_dir = project_root / "generated_dashboards"
        if not dashboard_dir.exists():
            return jsonify({"dashboards": []})

        dashboards = []
        for file_path in dashboard_dir.glob("*.html"):
            stat = file_path.stat()
            dashboards.append(
                {
                    "filename": file_path.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                }
            )

        # Sort by creation date, newest first
        dashboards.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify({"dashboards": dashboards})

    except Exception as e:
        logger.error(f"Error getting dashboard history: {e}")
        return jsonify({"error": "Failed to get dashboard history"}), 500


@app.route("/api/reports/history", methods=["GET"])
def get_report_history():
    """Get list of all generated reports."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        dashboard_dir = project_root / "generated_reports"
        if not dashboard_dir.exists():
            return jsonify({"reports": []})

        dashboards = []
        for file_path in dashboard_dir.glob("*.html"):
            stat = file_path.stat()
            dashboards.append(
                {
                    "filename": file_path.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                }
            )

        # Sort by creation date, newest first
        dashboards.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify({"reports": dashboards})

    except Exception as e:
        logger.error(f"Error getting report history: {e}")
        return jsonify({"error": "Failed to get report history"}), 500


@app.route("/api/report/<filename>", methods=["GET"])
def serve_report(filename):
    """Serve generated report HTML files."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        dashboard_path = project_root / "generated_reports" / filename
        if dashboard_path.exists():
            with open(dashboard_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return html_content, 200, {"Content-Type": "text/html"}
        else:
            return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        logger.error(f"Error serving report: {e}")
        return jsonify({"error": "Failed to serve report"}), 500


@app.route("/api/widget/<filename>", methods=["GET"])
def serve_widget(filename):
    """Serve generated widget HTML files."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        widget_path = project_root / "generated_widgets" / filename
        if widget_path.exists():
            with open(widget_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return html_content, 200, {"Content-Type": "text/html"}
        else:
            return jsonify({"error": "Widget not found"}), 404
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return jsonify({"error": "Failed to serve dashboard"}), 500

@app.route("/api/widget/history", methods=["GET"])
def get_widget_history():
    """Get list of all generated widgets."""
    try:
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent
        widget_dir = project_root / "generated_widgets"
        if not widget_dir.exists():
            return jsonify({"widgets": []})

        widgets = []
        for file_path in widget_dir.glob("*.html"):
            stat = file_path.stat()
            widgets.append(
                {
                    "filename": file_path.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                }
            )

        # Sort by creation date, newest first
        widgets.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify({"widgets": widgets, "dashboards": widgets})

    except Exception as e:
        logger.error(f"Error getting widget history: {e}")
        return jsonify({"error": "Failed to get widget history"}), 500



@app.route("/api/mcp-status", methods=["GET"])
def get_mcp_status():
    """Get MCP server connection status."""
    try:
        servers = {}
        for key, value in chatbot.mcp_clients.items():
            servers[key] = {
                "name": key,
                "status": "connected",
                "mcp_url": value["mcp_url"],
                "mcp_command": value["mcp_command"],
                "mcp_args": value["mcp_args"]
                
            }
        return jsonify({"timestamp": datetime.now().isoformat(), "servers": servers})

    except Exception as e:
        logger.error(f"MCP status check failed: {e}")
        return (
            jsonify({"error": "Failed to check MCP server status", "details": str(e)}),
            500,
        )


# socket event handlers
@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    try:
        # Generate a unique session ID that's different from the Socket.IO SID
        # This allows multiple tabs in the same browser to have different sessions
        session_id = request.sid
        client_session_id = request.args.get('tabId') if request.args.get('tabId') else f"tab_{int(time.time())}_{session_id[-6:]}"
        logger.info(f"Client connecting: Socket ID {session_id}, Client Session ID: {client_session_id}")
        
        # Store the mapping between socket ID and client session ID
        socketio.server.save_session(request.sid, {'client_session_id': client_session_id})
        
        # Check if chatbot exists
        if not chatbot:
            logger.error("Chatbot not initialized when handling connection")
            emit(
                "connected",
                {
                    "status": "error",
                    "error": "Chat system is not available. Please try again later.",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return
            
        # Initialize the conversation manager in a separate thread to avoid blocking
        def initialize_conversation():
            try:
                logger.info(f"Initializing conversation for session {session_id}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Create agents for this session
                try:
                    chatbot.create_all_agents(user_id=client_session_id, session_id=client_session_id)
                    
                    # Verify that the orchestrator agent was created
                    if not chatbot.orchestrate_agent:
                        raise Exception("Orchestrator agent was not created properly")
                        
                    logger.info(f"Agents created successfully for session {session_id}")
                    
                    # Emit connection success with session info
                    socketio.emit(
                        "connected",
                        {
                            "status": "connected",
                            "sid": session_id,
                            "tabId": client_session_id,
                            "timestamp": datetime.now().isoformat()
                        },
                        room=session_id,
                    )
                except Exception as e:
                    logger.error(f"Failed to create agents for session {session_id}: {e}")
                    socketio.emit(
                        "connected",
                        {
                            "status": "error",
                            "sid": session_id,
                            "error": f"Failed to initialize chat system: {str(e)}",
                            "timestamp": datetime.now().isoformat(),
                        },
                        room=session_id,
                    )

            except Exception as e:
                logger.error(
                    f"Error initializing conversation for session {session_id}: {e}"
                )
                socketio.emit(
                    "connected",
                    {
                        "status": "error",
                        "sid": session_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=session_id,
                )
            finally:
                loop.close()

        # Start initialization in background thread
        init_thread = threading.Thread(target=initialize_conversation, daemon=True)
        init_thread.start()

        logger.info(f"Client connection handler started for: {session_id}")

    except Exception as e:
        logger.error(f"Error in WebSocket connect handler: {e}")
        emit(
            "connected",
            {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )

@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection and preserve conversation state."""
    try:
        session_id = request.sid
        session_data = socketio.server.get_session(session_id)
        client_session_id = session_data.get('client_session_id', session_id) if session_data else session_id
        
        emit("disconnected",
            {
                "status": "disconnected",
                "sid": session_id,
                "tabId": client_session_id,
                "timestamp": datetime.now().isoformat(),
            }
            )
        chatbot.destroy_all_agents(session_id=client_session_id)
    except Exception as e:
        logger.error(f"Error in WebSocket disconnect handler: {e}")

@socketio.on("ping")
def handle_ping():
    """Handle ping for connection testing."""
    emit("pong", {"timestamp": datetime.now().isoformat()})

@socketio.on("chat_message")
def handle_chat_message(data):
    """Handle chat messages through WebSocket with conversation state."""
    try:
        # Check if chatbot exists
        if not chatbot:
            logger.error("Chatbot not initialized when handling chat message")
            emit(
                "chat_response",
                {
                    "type": "error",
                    "content": "Chat system is not available. Please try again later.",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return
            
        client_sid = request.sid
        
        # Get the client's tab-specific session ID
        session_data = socketio.server.get_session(client_sid)
        client_session_id = session_data.get('client_session_id', client_sid) if session_data else client_sid
        # Check if orchestrator agent exists and create if needed
        if not chatbot.orchestrate_agent:
            logger.warning("Orchestrator agent not found, creating agents")
            try:
                chatbot.create_all_agents(user_id=client_session_id, session_id=client_session_id)
                if not chatbot.orchestrate_agent:
                    raise Exception("Failed to create orchestrator agent")
            except Exception as e:
                logger.error(f"Failed to create agents: {e}")
                emit(
                    "chat_response",
                    {
                        "type": "error",
                        "content": "Failed to initialize chat system. Please try again later.",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return
                
        message = data.get("message", "").strip()
        

        if not message:
            emit(
                "chat_response",
                {
                    "type": "error",
                    "content": "Message is required",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return

        # Define streaming callback for WebSocket
        async def stream_callback(data):
            """Callback function to stream responses."""
            try:
                socketio.emit(
                    "chat_response",
                    {**data, "timestamp": datetime.now().isoformat()},
                    room=client_sid,
                )
            except Exception as e:
                logger.error(f"Error in stream callback: {e}")

        # Process message in a separate thread
        def process_message():
            try:
                # Create a new event loop for the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Process message with conversation manager
                loop.run_until_complete(
                    chatbot.process_message_stream(message, stream_callback, user_id=client_session_id, session_id=client_session_id)
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                socketio.emit(
                    "chat_response",
                    {
                        "type": "error",
                        "content": f"Processing error: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=client_sid,
                )
            finally:
                loop.close()

        # Start processing in background thread
        process_thread = threading.Thread(target=process_message, daemon=True)
        process_thread.start()

        # Send immediate acknowledgment
        emit(
            "chat_response",
            {
                "type": "status",
                "content": "Processing message...",
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error in chat_message handler: {e}")
        emit(
            "chat_response",
            {
                "type": "error",
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            },
        )

@socketio.on("confirm_plan")
def handle_confirm_plan(data):
    """
    Handle plan confirmation from client.
    
    Args:
        data: Dictionary containing the plan and original query
    """
    try:
        client_sid = request.sid
        
        # Define streaming callback for WebSocket
        async def stream_callback(update_data):
            """Callback function to stream responses."""
            try:
                socketio.emit(
                    "chat_response",
                    {**update_data, "timestamp": datetime.now().isoformat()},
                    room=client_sid,
                )
            except Exception as e:
                logger.error(f"Error in stream callback: {e}")
        
        def handle_confirmation():
            try:
                # Create a new event loop for the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                is_single_widget = data.get("is_single_widget", False)
                # Process message with conversation manager
                loop.run_until_complete(
                    chatbot.continue_with_confirmed_plan(
                        plan=data.get('plan', []),
                        original_query=data.get('original_query', ''),
                        is_single_widget=is_single_widget,
                        stream_callback=stream_callback,
                        user_id=client_sid,
                        session_id=client_sid
                    )
                )
            except Exception as e:
                logger.error(f"Error processing plan confirmation: {e}")
                socketio.emit(
                    'chat_response',
                    {
                        'type': 'error',
                        'content': f"An error occurred while executing the plan: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    },
                    room=client_sid
                )
            finally:
                loop.close()
        
        # Start processing in background thread
        process_thread = threading.Thread(target=handle_confirmation, daemon=True)
        process_thread.start()
        
        # Send immediate acknowledgment
        emit(
            "chat_response",
            {
                "type": "status",
                "content": "Processing plan confirmation...",
                "timestamp": datetime.now().isoformat(),
            },
        )
        
    except Exception as e:
        logger.error(f"Error processing plan confirmation: {e}")
        emit('chat_response', {
            'type': 'error',
            'content': f"An error occurred while executing the plan: {str(e)}",
            'timestamp': datetime.now().isoformat()
        })

@socketio.on("build_widget")
def handle_build_widget(data):
    """
    Handle widget building requests from the client.
    
    Args:
        data: Dictionary containing widget specifications
    """
    try:
        client_sid = request.sid
        # Check if chatbot exists
        if not chatbot:
            logger.error("Chatbot not initialized when handling widget build request")
            emit(
                "widget_response",
                {
                    "status": "error",
                    "message": "Dashboard system is not available. Please try again later.",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return
        user_query = data.get("message", "").strip()
        
        # Define streaming callback for WebSocket
        async def stream_callback(update_data):
            """Callback function to stream responses."""
            try:
                socketio.emit(
                    "widget_update",
                    {**update_data, "timestamp": datetime.now().isoformat()},
                    room=client_sid,
                )
            except Exception as e:
                logger.error(f"Error in widget stream callback: {e}")
        
        def generate_widget():
            try:
                # Create a new event loop for the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Generate the widget
                loop.run_until_complete(
                    chatbot.process_message_stream(user_query, stream_callback, client_sid, client_sid, is_single_widget=True)
                )
                
                # Send success response
                socketio.emit(
                    "widget_response",
                    {
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=client_sid,
                )
                
            except Exception as e:
                logger.error(f"Error generating widget: {e}")
                socketio.emit(
                    "widget_response",
                    {
                        "status": "error",
                        "message": f"Failed to generate widget: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=client_sid,
                )
            finally:
                loop.close()
        
        # Start widget generation in background thread
        widget_thread = threading.Thread(target=generate_widget, daemon=True)
        widget_thread.start()
        
        # Send immediate acknowledgment
        emit(
            "widget_update",
            {
                "status": "processing",
                "message": "Generating widget...",
                "timestamp": datetime.now().isoformat(),
            },
        )
        
    except Exception as e:
        logger.error(f"Error handling widget build request: {e}")
        emit("widget_response", {
            "status": "error",
            "message": f"An error occurred while building the widget: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })



if __name__ == "__main__":
    # Start the chatbot in a separate thread
    start_chatbot()
    
    print(f"Starting Flask-SocketIO server with logging level: {log_level}")
    print(f"Logs will be written to: {os.path.abspath('logs/backend.log')}")
    
    # Run the Flask-SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
