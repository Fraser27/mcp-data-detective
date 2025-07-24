from mcp import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
import asyncio
import json
import logging
from datetime import datetime
import re
from typing import Optional, Dict, Any, List, Tuple
import os
import base64
import uuid
from textwrap import dedent
from strands.agent.conversation_manager import SummarizingConversationManager,NullConversationManager,SlidingWindowConversationManager
from strands.session.file_session_manager import FileSessionManager
import time
import pathlib
# Configure logging
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/database_mcp_clients.log")
    ]
)
logger = logging.getLogger(__name__)

import json


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_data)


# Create a file handler with JSON formatting
# file_handler = logging.FileHandler("logs/strands_agents_sdk.log")
# file_handler.setFormatter(JsonFormatter())
# # Enable DEBUG logs for the tool registry only
# logger = logging.getLogger("strands")
# logger.addHandler(file_handler)
# Set logger level to INFO to see all information up to errors
logger.setLevel(logging.INFO)

os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-d4a5e154-f83a-4d39-a0a4-f9ec18efbcc0"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-d1d68d4e-9a55-4006-ae22-5d1882a587d3"
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
# Build Basic Auth header.
LANGFUSE_AUTH = base64.b64encode(
    f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
).decode()
# Configure OpenTelemetry endpoint & headers
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
    os.environ.get("LANGFUSE_HOST") + "/api/public/otel/v1/traces"
)
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Visualization types for dashboard building
VISUALIZATION_TYPES = {
    "line_chart": "Data that changes over time (sales trends, user growth). Line chart for time-series data",
    "bar_chart": "Comparing categories or groups (sales by region, products by category). Bar chart for comparing categories",
    "pie_chart": "Showing composition or proportion (market share, budget allocation). Pie chart for showing proportions",
    "scatter_plot": "Relationship between two variables (price vs. rating, age vs. salary). Scatter plot for correlation analysis",
    "heatmap": "Showing patterns or intensity across multiple dimensions (activity by hour/day)",
    "table": "Detailed individual records or aggregates requiring precise values",
    "gauge": "KPIs with target values (sales goals, customer satisfaction)",
    "funnel": "Sequential process steps with drop-offs (sales funnel, user journey)",
}


class MCPClientChatbot:
    """
    A persistent chatbot that connects to any database MCP server and stays running
    for continuous database interactions.
    """

    def __init__(
        self,
        sse_urls: list[dict] = [],
        stream_callback=None,
    ):
        """
        Initialize the MCP Chatbot.

        Args:
            sse_urls (list[{"name": str, "url": str}]): List of MCP servers with their names and URLs
            stream_callback: Optional callback function for streaming data
        """
        self.sse_urls = sse_urls
        self.is_running = False
        self.stream_callback = stream_callback
        self.mcp_clients = {}
        self.model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
            #model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        self.cheaper_model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
        )
        self.agent = None
        self.orchestrator_agent = None
        self.verifier_agent = None

        # Dashboard-specific agents
        self.schema_analyzer_agent = None
        self.dashboard_designer_agent = None
        self.html_generator_agent = None
        self.conversation_manager = None
        self.session_manager = None
        self.collected_datasets = []
        self.total_datasets=0
        self.custom_summarization_agent = None
        self.html_widget_generator_agent = None

    def verifier_agent_builder(self):
        """Verifier agent to check if the query is resolved."""
        try:
            logger.info("Building verifier agent")
            verifier_prompt = f"""
            You are a Verifier agent, designed to check if the query is resolved.
            You will be given the user query, the list of agents that were called, the agent responses, and the final response.
            You will need to check if the query is resolved.
            You will output a JSON object in the following format:
            {{
                "is_sufficient": True or False,
                "needs_clarification": True or False,
                "clarification_message": If needs_clarification is True, you will need to return the clarification message.
            }}
            - MANDATORY: You will only return a json object and nothing else.
            """
            
            if not self.session_manager:
                logger.warning("Session manager not initialized for verifier agent, creating a default one")
                self.session_manager = FileSessionManager(session_id=f"default_verifier_{int(time.time())}")
                
            if not self.conversation_manager:
                logger.warning("Conversation manager not initialized for verifier agent, creating it now")
                self.conversation_manager_builder()
                
            self.verifier_agent = Agent(
                system_prompt=verifier_prompt, 
                model=self.model, 
                name="Verifier_Agent",
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )
            logger.info("Verifier agent created successfully")
        except Exception as e:
            logger.error(f"Error creating verifier agent: {e}")
            # Set to None to ensure we know it failed
            self.verifier_agent = None
            raise e

    def orchestrate_agent_builder(self):
        """Orchestrate the agent to process the message."""
        # Try not adding tools to the prompt : Agent_Tools: {client['tools']}

        orchestrator_prompt = f"""
        You are a Multi-Agent Orchestrator, designed to coordinate support across multiple agents. Your role is to:
        1. Analyze incoming user queries and determine the most appropriate specialized agent to handle them:
            - {', '.join([f"MCP_SERVER_TYPE: {client['agent_type']}, Agent_name : {client['name']},  Agent_Description: {client['description']} {client['usage']} " for client in self.mcp_clients.values()])}
            - Agent_name: DashboardBuilder: Agent_Description: A specialized agent designed to build dashboards based on the collected data.
        2. Key Responsibilities:
        - Accurately classify user queries by domain area.
        - A user query could be served by multiple agents.
        - If your previous plan failed try a new plan using DIFFERENT agents or approaches.
        - Examples of Databases include MySQL, OpenSearch, Redis etc. 
        - You should only call the specialized agents once you have all necessary data from the user.
        - You will output an execution plan of a list of agents to call based on the user query.
        - You will also act as a Verifier when told to do so. When in the verifier role you will verify if you can answer the users question. If there are repeated issues in calling MCP tools or functions add in a tool_call error in the  output json.
        4. **CRITICAL DECISION MAKING RULES:**
        - **EXHAUST ALL AGENT OPTIONS FIRST**: Before asking the user for clarification, you MUST consider and potentially try ALL available agents that could help with the query.
        - **PROGRESSIVE EXPLORATION**: On subsequent calls, identify which agents you haven't yet utilized and prioritize them.
        - **USER CLARIFICATION AS LAST RESORT**: Only seek user clarification when:
          a) You have exhausted all relevant available agents
          b) Multiple agents have failed to provide sufficient information
          c) The query is genuinely ambiguous and cannot be resolved through agent exploration
          d) You need specific user preferences/parameters that no agent can determine
        - **SYSTEMATIC RETRY STRATEGY**: If an agent fails, try alternative agents before returning to the user.
        4. **Before seeking user clarification, ask yourself:**
        - Have I tried all agents that could potentially help with this query?
        - Are there alternative approaches using different agent combinations?
        - Can I gather more information from unused agents to better understand the request?
        - Is this truly a case where only the user can provide the missing information?
        5. Output the execution plan response in the following format:
             - MANDATORY: An ordered Json List of agent_names and step_number and/or clarification_message
             [
            {{
                "agent_name": "Name of the Agent",
                "step_number": "Sequence number of this step"
            }}
        ]
        - MANDATORY: If you need data from User then agent_name should be "User" and corresponding user question to ask
        Example when you need clarification from user
        [
           {{
              "agent_name": "User",
              "clarification_message":"What kind of dashboard are you looking for"
              "step_number": 1
           }}
        
        ]
        - MANDATORY: Verifier. When in the Verifier role verify if you can answer the user query and reply as below
        [
            {{
              "agent_name": "User",
              "can_answer": "yes" or "no",
              "step_number": 1
           }}
        ]

        - MANDATORY: Verifier. When in the Verifier role if you see repeated tool call errors and you cant answer the user query reply as below
        [
            {{
              "agent_name": "User",
              "can_answer":  "no",
              "tool_error": "yes",
              "tool_name": "Name of tool causing the error"
              "step_number": 1
           }}
        ]

        - MANDATORY: You will only return a json list and nothing else.

        Example for response:
        [
            {{
                "agent_name": "Redis",
                "step_number": 1
            }},
            {{
                "agent_name": "MongoDB",
                "step_number": 2
            }},
            {{
                "agent_name": "DashboardBuilder",
                "step_number": 3
            }}
        ]
        6. **STRATEGIC PLANNING EXAMPLES:**
        - First attempt: Try primary relevant agents
        - Second attempt: Try secondary/alternative agents before user clarification
        - Third attempt: Combine different agents or try specialized approaches
        - Final resort: Seek user clarification only when all agent options are exhausted
        7. **EXECUTION STRATEGY BY ATTEMPT:**
        - **First Call**: Execute primary agents most likely to handle the query
        - **Second Call**: Before seeking user clarification, identify and execute alternative agents that haven't been tried
        - **Third Call**: Try combination approaches or less obvious agent matches
        - **Final Call**: Only then seek user clarification as the last resort
        8. **AGENT EXPLORATION CHECKLIST:**
        Before calling "User" agent, verify:
        - [ ] Have I attempted all database agents that might contain relevant data?
        - [ ] Have I tried agents that might provide context or supporting information?
        - [ ] Are there agents with overlapping capabilities I haven't explored?
        - [ ] Can I combine multiple agents to gather sufficient information?
        - [ ] Have I considered unconventional but potentially relevant agents?
        IMPORTANT: 
        - For dashboard requests, always ensure we have enough data points to call the dashboard builder. Explore ALL available data sources before asking the user.
        - Think systematically about which agents remain unexplored before defaulting to user clarification.
        - Each retry should demonstrate learning from previous attempts by trying different agent combinations.
        - User clarification should be specific and targeted, indicating you've exhausted technical solutions.
        REMEMBER: Your goal is to be resourceful and thorough in exploring all available agents before involving the user. The user should be your last resort, not your second option.
        """
        try:
            logger.info("Building orchestrator agent")
            if not self.session_manager:
                logger.warning("Session manager not initialized, creating a default one")
                self.session_manager = FileSessionManager(session_id=f"default_{int(time.time())}")
                
            if not self.conversation_manager:
                logger.warning("Conversation manager not initialized, creating it now")
                self.conversation_manager_builder()
                
            self.orchestrate_agent = Agent(
                system_prompt=orchestrator_prompt, 
                model=self.model,
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )
            logger.info("Orchestrator agent created successfully")
        except Exception as e:
            logger.error(f"Error creating orchestrator agent: {e}")
            # Set to None to ensure we know it failed
            self.orchestrate_agent = None
            raise e

    async def start(self):
        """Start the chatbot and initialize all components."""
        try:
            print("🤖 Starting MCP Chatbot...")
            print("=" * 50)
            logger.info("Starting MCP Chatbot")
            
            # Initialize MCP clients
            for mcp_name, server_config in self.sse_urls.items():
                mcp_name = server_config["name"] if "name" in server_config else str(mcp_name).capitalize()
                is_streamable_http = False
                is_sse = False
                is_stdio = False
                sse_url = server_config["url"] if "url" in server_config else ""
                mcp_command = server_config["command"] if "command" in server_config else ""
                mcp_args = server_config["args"] if "args" in server_config else ""
                agent_type = server_config["agent_type"] if "agent_type" in server_config else "Others"
                usage = server_config["usage"] if "usage" in server_config else ""
                if "url" in server_config:
                    is_sse = True
                elif "command" in server_config:
                    is_stdio = True
                else:
                    # TODO Streamable HTTP here
                    pass
                specialized_agent_mcp_rules = server_config['rules_prompt'] if 'rules_prompt' in server_config else ""
                server_description = server_config["description"] if "description" in server_config else ""
                try:
                    logger.info(f"Initializing {mcp_name} MCP client at {sse_url}")
                    mcp_client=None
                    if is_sse:
                        mcp_client = MCPClient(lambda: sse_client(sse_url))
                    
                    elif is_stdio:
                        mcp_client = MCPClient(lambda: stdio_client(
                            StdioServerParameters(
                                command=mcp_command, 
                                args=mcp_args)))
                
                    elif is_streamable_http:
                        mcp_client = MCPClient(lambda: streamablehttp_client(sse_url))
                    
                    with mcp_client:
                        tools = mcp_client.list_tools_sync()
                        # Get Available tools
                        tool_config = []
                        for tool in tools:
                            tool_config.append(
                                {
                                    "name": tool.tool_name,
                                    "description": tool.tool_spec["description"],
                                    "inputSchema": tool.tool_spec["inputSchema"],
                                }
                            )
                        self.mcp_clients[mcp_name] = {
                            "agent_type": agent_type,
                            "name": mcp_name,
                            "description": server_description,
                            "is_streamable_http": is_streamable_http,
                            "is_sse": is_sse,
                            "is_stdio": is_stdio,
                            "mcp_url": sse_url,
                            "mcp_command": mcp_command,
                            "mcp_args": mcp_args,
                            "tools": tool_config,
                            "rules_prompt": specialized_agent_mcp_rules,
                            "usage": usage
                        }
                    print(f"🛠️ Initialized {mcp_name} MCP client")
                    logger.info(f"Successfully initialized {mcp_name} MCP client with {len(tools)} tools")
                except Exception as e:
                    logger.error(f"Error initializing {mcp_name} MCP client: {e}")
                    print(f"❌ Failed to initialize {mcp_name} MCP client: {e}")
            
            print("✅ MCP Chatbot started successfully")
            print("🎯 Chatbot is ready to process requests via API!")
            print("📊 Dashboard building capabilities enabled!")
            print("=" * 50)
            
            logger.info("MCP Chatbot started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting chatbot: {e}")
            print(f"❌ Failed to start chatbot: {e}")
            raise e
    
    def conversation_manager_builder(self):
        """Build the conversation manager with summarization capabilities."""
        try:
            logger.info("Building conversation manager")
            
            # Create a cheaper, faster model for summarization tasks
            cheaper_model = BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0")
            logger.info("Created cheaper model for summarization")
            
            # Create session manager if not already created
            if not self.session_manager:
                logger.warning("Session manager not initialized for conversation manager, creating a default one")
                self.session_manager = FileSessionManager(session_id=f"default_conversation_{int(time.time())}")
            
            # Create summarization agent
            self.custom_summarization_agent = Agent(
                session_manager=self.session_manager, 
                model=cheaper_model, 
                agent_id=str(uuid.uuid4())
            )
            logger.info("Created summarization agent")
            
            # Create the summarizing conversation manager with default settings
            # self.conversation_manager = SummarizingConversationManager(
            #     summary_ratio=0.5,  # Summarize 50% of messages when context reduction is needed
            #     preserve_recent_messages=10,  # Always keep 10 most recent messages
            #     summarization_agent=self.custom_summarization_agent
            # )

            self.conversation_manager = NullConversationManager()
            logger.info("Conversation manager created successfully")
        except Exception as e:
            logger.error(f"Error creating conversation manager: {e}")
            # Set to None to ensure we know it failed
            self.conversation_manager = None
            raise e

    def agent_builder(self, mcp_name, specialized_agent_mcp_rules_prompt, tools, tool_config):
        
        SPECIALIZED_AGENTS_PROMPT = """
        1. You are a specialized agent, designed to answer questions about the following tools:
        {placeholder}
        {agent_special_rules}
        3. Output format will be as follows
        - You will always return a structured jsonlist in the below format only
        {{
            "data": [
                {{ "label": "value", "value": "value" }},
                {{ "label": "value", "value": "value" }},
                {{ "label": "value", "value": "value" }},
                ...
            ]
        }}
        - MANDATORY: You will only return a valid JSON LIST object and nothing else.
        
        Example 1:
        {{
            "data": [
                {{ "device_id": 101, "device_name": "Dispenser 1", "site_id": 1001}},
                {{ "device_id": 102, "device_name": "Dispenser 2", "site_id": 1002 }},
                {{ "device_id": 103, "device_name": "Dispenser 3", "site_id": 1003 }},
                ...
            ]
        }}
        Example 2:
        {{
            "data": [
                {{ "devices_online": 101, "devices_offline": 102, "devices_total": 203 }},
                ...
            ]
        }}
        """

        AGENT_SYSTEM_PROMPT = SPECIALIZED_AGENTS_PROMPT.format(
            placeholder=str(tool_config), agent_special_rules=f"2. Rules: {specialized_agent_mcp_rules_prompt}"
        )
        agent = Agent(
            name=mcp_name,
            tools=tools,
            model=self.model,
            system_prompt=AGENT_SYSTEM_PROMPT,
            trace_attributes={
                "session.id": "sample-session-id",  # Example session ID
                "user.id": "leosill@gmail.com",  # Example user ID
                "langfuse.tags": ["MCP-Dashboarding", "Strands-Project-Demo"],
            },
            conversation_manager=self.conversation_manager, session_manager=self.session_manager,agent_id=str(uuid.uuid4())
        )
        return agent
    
    def extract_and_fix_json(self, text: str):
        # Find the first '{' and the last '}'
        start_index = text.find('{')
        end_index = text.rfind('}') + 1  # +1 to include the '}'
        
        if start_index == -1 or end_index == 0:  # if '{' or '}' not found
            logger.warning("No JSON object found in text")
            return None
        
        # Extract the JSON string
        json_str = text[start_index:end_index]
        logger.info(f"Extracted JSON string of length {len(json_str)}")
        
        # Fix common JSON syntax errors
        logger.info("Attempting to fix common JSON syntax errors")
        
        # 1. Fix trailing commas in arrays/objects
        lines = json_str.split('\n')
        for i in range(len(lines)):
            if ']' in lines[i] or '}' in lines[i]:
                lines[i-1] = lines[i-1].rstrip(',')
        json_str = '\n'.join(lines)
        
        # 2. Fix the mismatched brackets (closing array with '}' instead of ']')
        # This is a simple fix for this specific error
        if "}" in json_str and json_str.count('{') > json_str.count('}'):
            logger.info("Fixing mismatched brackets")
            json_str = json_str.replace('}', ']')
        
        # 3. Check for and remove control characters
        cleaned_json = ''
        for char in json_str:
            if ord(char) >= 32 or char in '\n\r\t':
                cleaned_json += char
            else:
                logger.info(f"Removing control character: {ord(char)}")
        
        try:
            # Parse the JSON
            json_data = json.loads(cleaned_json)
            logger.info("Successfully parsed JSON")
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            logger.debug(f"Problematic JSON: {cleaned_json[:200]}...")
            # If there's an error, you might want to try more sophisticated fixes
            return cleaned_json
        

    # Function to extract JSON objects from text
    def extract_and_merge_json(self, text):
        # Find all JSON objects in the text
        json_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
        json_matches = json_pattern.findall(text)
        
        # Parse each JSON object
        parsed_jsons = []
        for json_str in json_matches:
            try:
                parsed_json = json.loads(json_str)
                parsed_jsons.append(parsed_json)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {json_str[:50]}...")
        
        # Merge JSONs with the same keys
        merged_json = {}
        for parsed_json in parsed_jsons:
            for key, value in parsed_json.items():
                if key in merged_json and isinstance(value, list) and isinstance(merged_json[key], list):
                    # If both are lists, extend the existing list
                    merged_json[key].extend(value)
                else:
                    # Otherwise, just set or overwrite the value
                    merged_json[key] = value
        
        return merged_json
        
    
    def get_json_key(self, input_str_or_json, key):
        try:
            if isinstance(input_str_or_json, dict):
                return input_str_or_json[key]
            elif isinstance(input_str_or_json, str):
                # Try to parse as JSON first
                try:
                    json_obj = json.loads(input_str_or_json)
                    return json_obj.get(key)
                except json.JSONDecodeError:
                    # Fall back to string parsing
                    logger.info(f"Attempting to extract key '{key}' from string using split method")
                    return input_str_or_json.split(f"{key}")[1].split(":")[1].split(",")[0].replace('"', '').strip()
            else:
                logger.warning(f"Unable to extract key '{key}' from {type(input_str_or_json)}")
                return None
        except Exception as e:
            logger.error(f"Error extracting key '{key}' from input: {e}")
            logger.debug(f"Input data: {input_str_or_json[:200]}..." if isinstance(input_str_or_json, str) else str(input_str_or_json))
            return None
        

    def build_dashboard_agents(self):
        """Build the specialized dashboard agents."""
        try:
            logger.info("Building dashboard agents")
            
            # Check if required components are initialized
            if not self.session_manager:
                logger.warning("Session manager not initialized for dashboard agents, creating a default one")
                self.session_manager = FileSessionManager(session_id=f"default_dashboard_{int(time.time())}")
                
            if not self.conversation_manager:
                logger.warning("Conversation manager not initialized for dashboard agents, creating it now")
                self.conversation_manager_builder()

            # Schema Analyzer Agent (now focuses on visualization suggestions)
            logger.info("Creating schema analyzer agent")
            schema_analyzer_prompt = dedent(
                f"""
            You are an expert data analyst and visualization specialist. Your role is to:
            
            1. **Analyze Collected Data**: Examine data that has been collected from database sources
            2. **Identify Patterns**: Find meaningful patterns, trends, and insights in the data
            3. **Suggest Visualizations**: Recommend appropriate chart types based on data characteristics.
            4. **Consider User Intent**: Match visualizations to the user's query and goals
            
            **Available Visualization Types:**
            {json.dumps(VISUALIZATION_TYPES, indent=2)}
            
            **Output Format:**
            Return a JSON object with the following structure:
            {{
                "suggested_visualizations": [
                    {{
                        "dataset_index": 0,
                        "visualization_type": "chart_type_from_list_above",
                        "rationale": "Why this chart type is appropriate for this data",
                        "data_requirements": "What data format is needed",
                        "user_preference_hint": "Ask user about this visualization preference",
                        "insights": "What insights this visualization could reveal"
                    }}
                ],
                "questions_for_user": [
                    "What specific aspect would you like to focus on?",
                    "Do you prefer trend analysis or comparison views?",
                    "Are you interested in patterns over time or current snapshots?"
                ],
                "data_summary": "Brief summary of what the data shows"
            }}
            
            **Process:**
            1. Analyze the structure and content of collected datasets
            2. Identify the most meaningful ways to visualize each dataset
            3. Consider data volume, types, and relationships
            4. Suggest visualizations that will provide the most insight
            5. Return only valid JSON - no additional text or explanations
            """
            )

            self.schema_analyzer_agent = Agent(
                system_prompt=schema_analyzer_prompt, 
                model=self.model,
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )
            logger.info("Schema analyzer agent created successfully")
            
            # Dashboard Designer Agent (now focuses on data processing and validation)
            logger.info("Creating dashboard designer agent")
            dashboard_designer_prompt = dedent(
                """
            You are a senior data analyst and dashboard designer. Your role is to:
            
            1. **Process Collected Data**: Transform raw data into appropriate formats for visualization
            2. **Validate Data Quality**: Ensure data is clean, complete, and suitable for visualization. Fix bad or incorrect json in the data
            3. **Prepare Visualization Data**: Structure data according to chart requirements
            4. **Handle Edge Cases**: Manage empty data, outliers, and data type mismatches
            
            **Output Format:**
            Return a JSON object with the following structure:
            {{
                "processed_datasets": [
                    {{
                        "dataset_index": 0,
                        "visualization_type": "chart_type",
                        "data": [
                            {{ "label": "value", "value": "value" }},
                            ...
                        ],
                        "summary": "Brief summary of the processed data",
                        "data_quality": "Assessment of data quality",
                        "recommendations": "Any recommendations for visualization"
                    }}
                ],
                "dashboard_title": "Dashboard Title",
                "dashboard_description": "Brief description of the dashboard",
                "data_insights": "Key insights from the data analysis"
            }}
            
            **Process:**
            1. Examine each collected dataset for structure and content
            2. Transform data into the format required by the suggested visualization
            3. Validate data quality and handle any issues
            4. Provide insights and recommendations for each dataset
            5. Return only valid JSON - no additional text
            """
            )

            self.dashboard_designer_agent = Agent(
                system_prompt=dashboard_designer_prompt, 
                model=self.model,
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )
            logger.info("Dashboard designer agent created successfully")



            # HTML Generator Agent - MVP 1 focused on pie charts and tables
            logger.info("Creating HTML generator agent")
            html_generator_prompt = dedent(
                """
            You are a frontend engineer creating MVP 1 dashboards. Your role is to:
            
            1. **Generate Simple HTML Dashboard**: Create a basic, functional HTML dashboard
            2. **Basic Styling**: Use Tailwind CSS for clean, simple design
            
            **MVP 1 Requirements:**
            - Use Chart.js (via CDN) ONLY for pie charts
            - Use HTML tables for detailed data
            - Use Tailwind CSS (via CDN) for basic styling
            - Simple card layout - one chart/table per card
            - Minimal, clean design
            
            **Output Format:**
            Return only a complete, valid HTML document. Include:
            - HTML5 structure with Chart.js and Tailwind CSS CDN
            - Pie charts for categorical data
            - HTML tables for detailed data
            - Simple card layout
            
            **Important:**
            - Return only HTML - no explanations
            """
            )

            self.html_generator_agent = Agent(
                system_prompt=html_generator_prompt, 
                model=self.model,
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )
            logger.info("HTML generator agent created successfully")
            
            html_widget_generator_prompt = dedent(
                """
            You are a frontend engineer creating widgets. Your role is to:
            
            1. **Generate Simple HTML Widget**: Create a basic, functional HTML Widget
            2. **Basic Styling**: Use Tailwind CSS for clean, simple design
            
            **MVP 1 Requirements:**
            - Use Chart.js or D3.js (via CDN) as a charting library
            - Use HTML tables for detailed data
            - Use Tailwind CSS (via CDN) for basic styling
            - Simple card layout - one chart/table per card
            - Minimal, clean design
            
            **Output Format:**
            Return only a complete, valid HTML document. Include:
            - HTML5 structure with Chart.js and Tailwind CSS CDN
            - Pie charts for categorical data
            - HTML tables for detailed data
            - Simple card layout
            
            **Important:**
            - MANDATORY: Return only HTML - no explanations
            - MANDATORY: You will only create a single widget at a time.
            - MANDATORY: Focus on functionality over fancy features
            """
            )

            self.html_widget_generator_agent= Agent(
                system_prompt=html_widget_generator_prompt, 
                model=self.model,
                conversation_manager=self.conversation_manager, 
                session_manager=self.session_manager,
                agent_id=str(uuid.uuid4())
            )

        except Exception as e:
            logger.error(f"Error building dashboard agents: {e}")
            # Set to None to ensure we know they failed
            self.schema_analyzer_agent = None
            self.dashboard_designer_agent = None
            self.html_generator_agent = None
            raise e

    async def callback_handler(self, chunk):
        """Handle the callback from the agent."""
        full_response = ""
        if "data" in chunk:
            await self._stream_update("thinking", chunk["data"])
            full_response += chunk["data"]
        elif "complete" in chunk:
            await self._stream_update("thinking", chunk["complete"], is_partial=False)
            full_response += chunk["complete"]
        elif "current_tool_use" in chunk:
            await self._stream_update(
                "tool_use",
                chunk["current_tool_use"].get("name"),
                extra={"input": chunk["current_tool_use"].get("input", "")},
            )
        elif "reasoningText" in chunk:
            await self._stream_update("thinking", chunk["reasoningText"])
        return full_response

    async def build_dashboard(
        self, user_query: str, stream_callback=None
    ) -> Dict[str, Any]:
        """
        Build a complete dashboard based on the user query.
        First collects data from database MCP servers, then asks for visualization preferences.

        Args:
            user_query: The user's dashboard request
            stream_callback: Optional callback for streaming progress updates

        Returns:
            Dictionary containing the dashboard HTML and metadata
        """
        try:
            # Step 1: Collect data from database MCP servers
            if stream_callback:
                await self._stream_update(
                    "thinking",
                    "🔍 Collecting data from your databases to understand what's available...",
                )

            # Collect data from all available MCP servers
            collected_data = await self._collect_data_from_mcp_servers(
                user_query, stream_callback
            )

            if not collected_data or not collected_data.get("datasets"):
                if stream_callback:
                    await self._stream_update(
                        "error",
                        "No data found in the databases. Please check your data sources or try a different query.",
                    )
                return {
                    "type": "error",
                    "content": "No data available for dashboard generation",
                }
            else:
                await self._stream_update(
                    "thinking",
                    f"✅ Data collected successfully! {collected_data}",
                    is_partial=True,
                )
            # Step 2: Ask for visualization preferences
            if stream_callback:
                await self._stream_update(
                    "thinking",
                    "📊 Analyzing the collected data and suggesting visualization options...",
                )

            adapted_visualizations = await self._adapt_visualizations_to_data(
                collected_data, stream_callback
            )

            # Step 4: Generate HTML dashboard
            if stream_callback:
                await self._stream_update(
                    "thinking",
                    "🎨 Generating interactive dashboard with optimized charts...",
                )

            html_response = await self._generate_dashboard_html(
                adapted_visualizations, user_query
            )

            if stream_callback:
                await self._stream_update(
                    "content",
                    "✅ Dashboard generated successfully! Here's your interactive dashboard:",
                    is_partial=False,
                )

            # Return the complete dashboard
            return {
                "type": "dashboard",
                "html": html_response,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "user_query": user_query,
                    "data_summary": collected_data.get("summary", ""),
                    "visualization_adaptations": adapted_visualizations.get(
                        "adaptations", []
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error building dashboard: {e}")
            if stream_callback:
                await self._stream_update("error", f"Failed to build dashboard: {str(e)}")
            return {
                "type": "error",
                "content": f"Dashboard generation failed: {str(e)}",
            }

    async def _ask_visualization_preferences(
        self, suggestions: Dict[str, Any], stream_callback
    ) -> Dict[str, Any]:
        """
        Ask user for visualization preferences when multiple options are available.

        Args:
            suggestions: Visualization suggestions from the analyzer
            stream_callback: Callback for streaming updates

        Returns:
            Dictionary containing user preferences or default choices
        """
        questions = suggestions.get("questions_for_user", [])
        suggested_viz = suggestions.get("suggested_visualizations", [])

        if not questions or len(suggested_viz) <= 1:
            # No need to ask questions if there's only one suggestion
            return suggestions

        # For now, we'll use the first suggestion as default
        # In a full implementation, this could be an interactive prompt
        if stream_callback:
            await self._stream_update(
                "thinking",
                f"📊 I found {len(suggested_viz)} potential visualizations. Using the most appropriate ones based on your data...",
                timestamp=datetime.now().isoformat(),
            )

        # Return the suggestions with a note about the choice
        return {
            **suggestions,
            "user_choice_note": "Selected most appropriate visualizations based on data characteristics",
        }

    
    async def _adapt_visualizations_to_data(
        self, collected_data: dict, stream_callback=None
    ) -> dict:
        """
        MVP 1: Default to pie charts for categorical data, tables for detailed data.
        """
        visualizations = []
        for idx, dataset in enumerate(collected_data.get("datasets", [])):
            # Simple logic: if data looks like key-value pairs, use pie chart, otherwise table
            try:
                parsed_data = (
                    json.loads(dataset) if isinstance(dataset, str) else dataset
                )
                data_items = parsed_data.get("data", [])

                # Check if data is suitable for pie chart (has 2-10 items with numeric values)
                if (
                    isinstance(data_items, list)
                    and 2 <= len(data_items) <= 10
                    and all(
                        isinstance(item, dict) and len(item) == 2 for item in data_items
                    )
                ):
                    viz_type = "pie_chart"
                    reason = (
                        "Categorical data with numeric values - suitable for pie chart"
                    )
                else:
                    viz_type = "table"
                    reason = "Detailed data - best displayed as table"
            except:
                viz_type = "table"
                reason = "Default to table for data parsing issues"

            visualizations.append(
                {
                    "dataset_index": idx,
                    "visualization_type": viz_type,
                    "data": dataset,
                    "adaptation_reason": reason,
                }
            )
        return {
            "final_visualizations": visualizations,
            "adaptations": [
                f"MVP 1: Using pie charts and tables based on data characteristics"
            ],
        }

    def _analyze_data_characteristics(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the characteristics of a dataset to determine appropriate visualization.

        Args:
            dataset: Dataset to analyze

        Returns:
            Dictionary containing data characteristics
        """
        characteristics = []

        if dataset.get("type") == "table":
            headers = dataset.get("headers", [])
            rows = dataset.get("rows", [])

            # Count data points
            num_rows = len(rows)
            num_columns = len(headers)

            if num_rows == 0:
                characteristics.append("no_data")
            elif num_rows == 1:
                characteristics.append("single_data_point")
            elif num_rows < 5:
                characteristics.append("few_data_points")
            elif num_rows > 100:
                characteristics.append("many_data_points")

            # Check for time-based data
            time_indicators = ["date", "time", "year", "month", "day", "timestamp"]
            has_time_data = any(
                indicator in str(headers).lower() for indicator in time_indicators
            )
            if has_time_data:
                characteristics.append("time_series")

            # Check for categorical vs numerical data
            if num_columns >= 2:
                # Simple heuristic: if first column looks like categories and second like numbers
                try:
                    first_col_values = [row[0] for row in rows if len(row) > 0]
                    second_col_values = [row[1] for row in rows if len(row) > 1]

                    # Check if second column contains numbers
                    numeric_count = sum(
                        1
                        for val in second_col_values
                        if str(val).replace(".", "").replace("-", "").isdigit()
                    )
                    if numeric_count > len(second_col_values) * 0.8:  # 80% numeric
                        characteristics.append("categorical_numerical")
                except:
                    pass

        elif dataset.get("type") == "text":
            characteristics.append("text_data")

        return {
            "characteristics": characteristics,
            "dataset_type": dataset.get("type"),
            "source": dataset.get("source"),
        }

    def _adapt_chart_type(
        self, original_type: str, data_analysis: Dict[str, Any]
    ) -> str:
        """
        Adapt chart type based on data characteristics.

        Args:
            original_type: Originally suggested chart type
            data_analysis: Analysis of data characteristics

        Returns:
            Adapted chart type
        """
        characteristics = data_analysis.get("characteristics", [])

        # Adaptation rules
        if "no_data" in characteristics:
            return "table"  # Show empty state clearly

        if "single_data_point" in characteristics:
            return "gauge"  # Single value is better as gauge

        if "few_data_points" in characteristics:
            if original_type in ["line_chart", "area_chart"]:
                return "bar_chart"  # Few points better as bars
            elif original_type == "scatter_plot":
                return "table"  # Too few points for scatter

        if "many_data_points" in characteristics:
            if original_type == "pie_chart":
                return "bar_chart"  # Too many slices for pie
            elif original_type == "table":
                return "bar_chart"  # Better visualization for many points

        if "time_series" in characteristics:
            if original_type not in ["line_chart", "area_chart", "bar_chart"]:
                return "line_chart"  # Time data should be line chart

        if "categorical_numerical" in characteristics:
            if original_type in ["line_chart", "area_chart"]:
                return "bar_chart"  # Categories better as bars

        if "text_data" in characteristics:
            return "table"  # Text data as table

        return original_type

    def _apply_adaptations(
        self, suggestions: Dict[str, Any], adaptations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply adaptations to the original suggestions.

        Args:
            suggestions: Original visualization suggestions
            adaptations: List of adaptations to apply

        Returns:
            List of final visualizations with adaptations applied
        """
        final_visualizations = []

        for suggestion in suggestions.get("suggested_visualizations", []):
            dataset_index = suggestion.get("dataset_index", 0)

            # Find matching adaptation
            adaptation = next(
                (a for a in adaptations if a.get("dataset_index") == dataset_index),
                None,
            )

            final_viz = suggestion.copy()
            if adaptation:
                final_viz["visualization_type"] = adaptation["adapted_type"]
                final_viz["adaptation_reason"] = adaptation["reason"]

            final_visualizations.append(final_viz)

        return final_visualizations

    async def _generate_dashboard_html(
        self, visualizations: Dict[str, Any], user_query: str, is_single_widget=False
    ) -> str:
        """
        Generate HTML dashboard with the adapted visualizations and save to file.
        

        Args:
            visualizations: Final visualizations with adaptations
            user_query: Original user query

        Returns:
            HTML string for the dashboard
        """
        html_prompt = f"""
        I need to create a professional, interactive HTML {"widget" if is_single_widget else "dashboard"} based on the user's query and visualization requirements.
        {"Mandatory- You will always generate a single widget. If there are multiple datasets try combining them into a single widget else ignore other datasets" if is_single_widget else ""}
        ## User Query
        {user_query}
        ## Visualization Specifications
        {json.dumps(visualizations, indent=2)}
        ## Requirements

        ### Core Functionality
        - Create a complete, standalone HTML file with all necessary components embedded
        - Make the {"widget" if is_single_widget else "dashboard"} fully responsive across desktop, tablet, and mobile devices
        - Implement proper data visualization based on the specifications.{"And only generate one visualization" if is_single_widget else ""}
        - Ensure all chart elements are properly labeled and accessible. {"And only generate one chart" if is_single_widget else ""}
        {"" if is_single_widget else """ - Add a fixed navigation header with AWS logo.
         - Implement a dark mode toggle
         - Create card-based components with subtle shadows and hover effects
         - Use rounded corners (border-radius: 12px) for containers"""}
        - Below the title write a one-line summary of the generated {"widget" if is_single_widget else "dashboard"}
        - MANDATORY: Use standard HTML syntax with proper quotes (") for attributes, not escaped quotes (\") which would break HTML parsing
        
        ### Visualization Features
        - Use Chart.js or D3.js for creating interactive visualizations
        - For each visualization, implement:
           - Tooltips showing detailed information on hover
           - Legends that can be toggled on/off
        
        ### Design and Layout
        - Use Tailwind CSS for responsive styling and layout
        - Implement a clean, modern UI with appropriate spacing and typography
        - Use Inter or Poppins as the primary font
        - Implement a clear typography hierarchy:
        * Headings: 2.5rem/2rem/1.5rem
        * Body: 1rem
        * Caption: 0.875rem
        - Add export functionality for charts and tables (e.g., PNG, CSV)
        - Use a cohesive color palette that ensures good contrast and readability
        - Include a header with the {"widget" if is_single_widget else "dashboard"} title based on the user query
        - {"Just a title, subtitle and one chart only for this widget" if is_single_widget else "Organize visualizations in a logical grid layout with appropriate sizing"}
        
        ### Additional Features
        {"" if is_single_widget else "- MANDATORY: - Add Export options (PDF, PNG, CSV). Filter and search capabilities for tables"}
        - MANDATORY: Include a timestamp showing when the {"widget" if is_single_widget else "dashboard"} was generated.
        7. Accessibility:
        - High contrast options
        - ARIA labels
        - Keyboard navigation
        - Screen reader compatibility
        8. Animations:
        - Subtle micro-interactions
        - Chart loading animations
        - Smooth page transitions
        - Hover state animations
        ## Output Format
        Provide a complete HTML document with all necessary scripts, styles, and content embedded to ensure it works as a standalone file.
        
        ## Example Structure
        ```html
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <!-- Meta tags, title, and embedded stylesheets -->
        </head>
        <body>
            <!-- {"Widget" if is_single_widget else "Dashboard"} header -->
            <!-- {"Widget Subtitle" if is_single_widget else ""} --> 
            <!-- Chart containers with dropdown selectors -->
            <!-- {"" if is_single_widget else "Download"}  button -->
            <!-- Embedded scripts for Chart.js and interactivity -->
        </body>
        </html>
        """
        response=None
        if is_single_widget:
            response = self.html_widget_generator_agent(html_prompt)
        else:    
            response = self.html_generator_agent(html_prompt)
        html_content = str(response)
       
        file_name = "dashboard"
        # Use pathlib for relative path
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent.parent
        dashboard_dir = project_root / "generated_dashboards"
        if is_single_widget:
            file_name = "widget"
            # Use pathlib for relative path
            current_file = pathlib.Path(__file__)
            project_root = current_file.parent.parent.parent
            dashboard_dir = project_root / "generated_widgets"
        # extract title from html content
        if '<title>' in html_content and '</title>' in html_content:
            file_name = html_content.split('<title>')[1].split('</title>')[0]
        # Create the directory if it doesn't exist        
        dashboard_dir.mkdir(exist_ok=True, parents=True)
        # Generate a unique filename based on timestamp and query
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_name}_{timestamp}.html"
        # Save the dashboard HTML to file
        filepath = dashboard_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return filename, html_content

    def get_mcp_client(self, mcp_name):
        """Get the MCP client."""
        mcp_client = None
        if mcp_name in self.mcp_clients:
            mcp_config = self.mcp_clients[mcp_name]
            if mcp_config["is_sse"]:
                mcp_client = MCPClient(
                    lambda: sse_client(self.mcp_clients[mcp_name]["mcp_url"])
                )
            elif mcp_config["is_stdio"]:
                mcp_client = MCPClient(lambda: stdio_client(
                    StdioServerParameters(
                        command=mcp_config["mcp_command"], 
                        args=mcp_config["mcp_args"])))
            elif mcp_config["is_streamable_http"]:
                mcp_client = MCPClient(lambda: streamablehttp_client(mcp_config['mcp_url']))
                    
        return mcp_client
    
    def create_all_agents(self, user_id="Sample", session_id=None):
        """Create all agents needed for the chatbot."""
        try:
            logger.info(f"Creating all agents for user {user_id}, session {session_id}")
            
            # Create session manager
            if not session_id:
                session_id = f"session_{int(time.time())}"
            self.session_manager = FileSessionManager(session_id=f"{user_id}_{session_id}")
            logger.info(f"Session manager created with ID: {user_id}_{session_id}")
            
            # Create conversation manager
            self.conversation_manager_builder()
            logger.info("Conversation manager created")
            
            # Create orchestrator agent
            self.orchestrate_agent_builder()
            logger.info("Orchestrator agent created")
            
            # Create verifier agent
            self.verifier_agent_builder()
            logger.info("Verifier agent created")
            
            # Create dashboard agents
            self.build_dashboard_agents()
            logger.info("Dashboard agents created")

            self.collected_datasets = []
            self.total_datasets = 0
            
            logger.info("All agents created successfully")
        except Exception as e:
            logger.error(f"Error creating agents: {e}")
            raise e
    
    def destroy_all_agents(self, user_id="Sample", session_id=None):
        self.conversation_manager = None
        self.orchestrate_agent = None
        self.verifier_agent = None
        self.schema_analyzer_agent = None
        self.dashboard_designer_agent = None
        self.html_generator_agent = None

    async def _stream_update(
        self,
        update_type: str,
        content: str = "",
        is_partial: bool = True,
        timestamp: str = None,
        metadata: dict = None,
        extra: dict = None,
        title: str = None,
    ):
        """Send streaming updates via callback."""
        if self.stream_callback:
            clean_content = content
            update_data = {
                "type": update_type,
                "content": clean_content,
                "is_partial": is_partial,
            }
            if update_type == "tool_use":
                del update_data["content"]
                update_data["tool"] = clean_content
                update_data["input"] = extra["input"] if "input" in extra else {}
            if timestamp:
                update_data["timestamp"] = timestamp
            if metadata:
                update_data["metadata"] = metadata
            if title:
                update_data["title"] = title
            if extra:
                update_data.update(extra)
            await self.stream_callback(update_data)
            
    async def _handle_error(self, error_message):
        """Handle errors consistently with proper logging and user feedback."""
        logger.error(error_message)
        await self._stream_update("error", error_message)
        await self._stream_update("end", timestamp=datetime.now().isoformat())
        
    async def _get_orchestrator_response(self, user_query):
        """Get and validate orchestrator response."""
        if not self.orchestrate_agent:
            # Try to recreate the agent if it's not available
            try:
                logger.info("Orchestrator agent not found, attempting to create it")
                self.create_all_agents(user_id="system", session_id=f"session_{int(time.time())}")
                if not self.orchestrate_agent:
                    await self._handle_error("Orchestrator agent not available. Please restart the system.")
                    return None
            except Exception as e:
                await self._handle_error(f"Failed to create orchestrator agent: {str(e)}")
                return None
            
        try:
            orchestrator_response = self.orchestrate_agent(user_query)
            logger.info(f"Orchestrator response received: {orchestrator_response}")
            
            if not orchestrator_response:
                await self._handle_error("Failed to classify the query. Please try rephrasing your question.")
                return None
                
            return orchestrator_response
        except Exception as e:
            await self._handle_error(f"Error getting orchestrator response: {str(e)}")
            return None
            
    async def _execute_agent(self, agent_name, user_query):
        """Execute a specific agent and return its response."""
        try:
            mcp_client = self.get_mcp_client(agent_name)
            with mcp_client:
                tools = mcp_client.list_tools_sync()
                agent = self.agent_builder(
                    agent_name,self.mcp_clients[agent_name]["rules_prompt"], tools, self.mcp_clients[agent_name]["tools"]
                )
                response_stream = agent.stream_async(user_query)
                full_response = ""
                async for chunk in response_stream:
                    full_response += await self.callback_handler(chunk)
                return full_response
        except Exception as e:
            logger.error(f"Error executing agent {agent_name}: {e}")
            await self._handle_error(f"Error executing {agent_name} agent: {str(e)}")
            return None
            
    async def create_dashboard(self, user_query: str, is_single_widget=False) -> Dict[str, Any]:
        """Complete dashboard creation process from user query to final HTML."""
        try:
            # Step 1: Collect data from database MCP servers
            await self._stream_update(
                "thinking",
                f"🔍 Collected data from {self.total_datasets}",
                is_partial=True
            )
            
            if len(self.collected_datasets) <= 0:
                await self._stream_update(
                    "error",
                    "No data found in the databases. Please check your data sources or try a different query."
                )
                return {
                    "type": "error",
                    "content": "No data available for dashboard generation"
                }
            
            # Step 2: Analyze data and suggest visualizations
            await self._stream_update(
                "thinking",
                "📊 Analyzing data and suggesting visualizations...",
                is_partial=True
            )
            
            # Use schema analyzer agent to suggest visualizations
            analyzer_prompt = f"""Analyze this collected data and suggest appropriate visualizations:\n{self.collected_datasets}"""
            visualization_suggestions = self.schema_analyzer_agent(analyzer_prompt)
            
            # Step 3: Process and adapt visualizations to data
            await self._stream_update(
                "thinking",
                "🎨 Adapting visualizations to your data...",
                is_partial=True
            )
            
            # Use dashboard designer agent to process data
            designer_prompt = f"""Process this data for visualization:\n{self.collected_datasets}\n\nWith these visualization suggestions:\n{visualization_suggestions}"""
            processed_data = self.dashboard_designer_agent(designer_prompt)
            
            # Step 4: Generate HTML dashboard
            await self._stream_update(
                "thinking",
                "🖥️ Generating interactive dashboard...",
                is_partial=True
            )
            
            # Generate final HTML
            file_name, html_content = await self._generate_dashboard_html(
                {"final_visualizations": json.loads(str(processed_data)).get("processed_datasets", [])},
                user_query, is_single_widget
            )
            
            await self._stream_update(
                "content",
                f"✅ {"Widget" if is_single_widget else "Dashboard"} generated successfully!",
                is_partial=False
            )
            
            # Return the complete dashboard
            await self._stream_update(
                update_type="dashboard_file",
                content=file_name,
                is_partial=False,
                timestamp=datetime.now().isoformat(),
                metadata= {
                    "generated_at": datetime.now().isoformat(),
                    "user_query": user_query,
                    "data_summary": ','.join(self.collected_datasets)}
            )
            return {
                "type": {"widget_file" if is_single_widget else "dashboard_file"},
                "file_name": file_name,
                "message": f"{"Widget" if is_single_widget else "Dashboard"} generated successfully!",
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            await self._stream_update("error", f"Failed to create dashboard: {str(e)}")
            return {
                "type": "error",
                "content": f"Dashboard generation failed: {str(e)}"
            }

    async def continue_with_confirmed_plan(self, plan: list, original_query: str, stream_callback, user_id: str = "default", session_id: str="None", is_single_widget=False):
        """Continue processing with a confirmed plan from human."""
        try:
            # Initialize agents and setup
            self.stream_callback = stream_callback
            
            user_query = f"Previous Conversations: \n {self.orchestrate_agent.messages} \n current_query: {original_query}"
            # Conversation tracking variables
            conversation_resolved = False
            accumulated_responses = []
            is_clarification_needed = False
            
            logger.info(f"Executing confirmed plan for user {user_id}, session {session_id}")
            
            # Execute the confirmed plan
            await self._stream_update("thinking", f"\n Executing confirmed plan... {plan} \n")
            
            # Execute each identified agent
            agent_responses = []
            try:
                indx = 1
                for agent_config in plan:
                    agent_name = agent_config["agent_name"]
                    step_number = agent_config.get("step_number", 1)
                    
                    if indx != step_number:
                        continue
                    indx += 1
                        
                    # Handle user clarification requests
                    if agent_name.lower() == 'user' and step_number == 1:
                        clarification_msg = agent_config.get('clarification_message', 'Question for User')
                        await self._stream_update('thinking', clarification_msg)
                        agent_responses.append({"agent_name": agent_name, "response": clarification_msg})
                        is_clarification_needed = True
                        break
                    
                    # Execute agent if available
                    if agent_name not in self.mcp_clients and agent_name != 'DashboardBuilder':
                        await self._handle_error(f"Agent {agent_name} not found in available agents.")
                        break
                    
                    if agent_name == 'DashboardBuilder':
                        await self._stream_update('thinking', 'Generating Dashboard...')
                        dashboard_response = await self.create_dashboard(user_query, is_single_widget)
                        if dashboard_response['type'] == 'error':
                            return dashboard_response
                        agent_responses.append({"agent_name": agent_name, "response": dashboard_response})
                    
                    elif agent_name in self.mcp_clients:  # Other MCPs
                        # Get agent response
                        updated_query = user_query
                        if len(agent_responses) > 0:
                            updated_query = f"""
                            You are an agent in a multi-agent system with specific tools and capabilities.
                            1. **PREVIOUS CONTEXT**: Consider these responses from previous agents: {agent_responses}.
                            2. **PRIMARY RESPONSIBILITY**: Try to answer any part of the question not answered by the previous agents using YOUR available tools.                                                
                            3. **TOOL EXPLORATION MANDATE**: 
                               - **ALWAYS attempt to use your available tools first** before determining you cannot help
                               - Your tools may contain relevant data even if not immediately obvious from the question
                               - Example: A question about "online devices" might be answerable using database tools like list_mysql_tables and query_mysql_tables if device status is stored in tables
                               - **Think creatively** about how your tools might provide relevant information
                               - **Explore database schemas** using list tools to understand what data is available
                               - **Query systematically** to find relevant information that might answer the user's question
                            4. **DECISION PROCESS** - Follow this order:
                               a) **EXPLORE**: Use listing/discovery tools to understand what data you have access to
                               b) **INVESTIGATE**: Query relevant data sources that might contain the requested information  
                               c) **ANALYZE**: Examine the data to see if it answers any part of the user's question
                               d) **RESPOND**: Only after genuine exploration, determine if you can provide partial or complete answers
                            **Original User Query**: {user_query}"""
                        else:
                            updated_query = f""" You are an agent in a multi-agent system with specific tools and capabilities.
                            1. **PRIMARY RESPONSIBILITY**: Try to answer any part of the question not answered by the previous agents using YOUR available tools.                                                
                            2. **TOOL EXPLORATION MANDATE**: 
                               - **ALWAYS attempt to use your available tools first** before determining you cannot help
                               - Your tools may contain relevant data even if not immediately obvious from the question
                               - Example: A question about "online devices" might be answerable using database tools like list_mysql_tables and query_mysql_tables if device status is stored in tables
                               - **Think creatively** about how your tools might provide relevant information
                               - **Explore database schemas** using list tools to understand what data is available
                               - **Query systematically** to find relevant information that might answer the user's question
                            3. **DECISION PROCESS** - Follow this order:
                               a) **EXPLORE**: Use listing/discovery tools to understand what data you have access to
                               b) **INVESTIGATE**: Query relevant data sources that might contain the requested information  
                               c) **ANALYZE**: Examine the data to see if it answers any part of the user's question
                               d) **RESPOND**: Only after genuine exploration, determine if you can provide partial or complete answers
                            **Original User Query**: {user_query}
                            """
                        response = await self._execute_agent(agent_name, updated_query)
                        json_resp = self.extract_and_merge_json(response)
                        if json_resp:
                            self.collected_datasets.append(str(json_resp))
                            self.total_datasets += 1
                        agent_responses.append({"agent_name": agent_name, "response": response})
                        logger.info({"agent_name": agent_name, "response": response})
                
                # Process final responses
                if agent_responses:
                    # Combine all agent responses
                    combined_response = "\n\n".join(
                        [
                            f"**{resp['agent_name']} Response:**\n{resp['response']}"
                            for resp in agent_responses
                        ]
                    )

                    if is_clarification_needed:
                        await self._stream_update(
                                "content", combined_response, is_partial=False
                            )
                        return {"type": "clarification", "content": combined_response}

                    accumulated_responses.append(combined_response)
                    
                    # Evaluate if the query is resolved
                    try:
                        # Check if the response contains meaningful content
                        verifier_input = f"User Query: {user_query}. We called the following agents: {plan}. Agent Responses: {combined_response}"
                        verifier_response = self.orchestrate_agent("Assume the verifier role and let us know if this data is sufficient to answer the user query: " + verifier_input)

                        # Parse the verifier response
                        verifier_response_str = self.extract_and_fix_json(str(verifier_response))
                        
                        if 'tool_error' in verifier_response_str:
                            key_val = self.get_json_key(verifier_response_str, "tool_name")
                            conversation_resolved = True
                            await self._stream_update("content", f"Repeated errors when calling tool {key_val}. Please reach out to System Administrator")
                            return {"type": "error", "content": f"Repeated errors when calling tool {key_val}"}
                        
                        can_answer = self.get_json_key(verifier_response_str, "can_answer")
                        if can_answer == 'yes':
                            conversation_resolved = True
                            # ba_summarizer_prompt = f"""You are a business analyst whose role is to provide actionable insights and recommendations based on data analysis.

                            # **YOUR TASK**: Analyze the following data and provide a clear, actionable summary: {combined_response}
                            
                            # **OUTPUT REQUIREMENTS**:
                            # 1. **Executive Summary**: Provide a concise overview of key findings
                            # 2. **Key Insights**: Extract the most important data points and what they mean for the business
                            # 3. **Actionable Recommendations**: Specific steps the business can take based on the data
                            # 4. **Risk Assessment**: Identify any concerning trends or issues that need attention
                            
                            # **OUTPUT FORMAT**:
                            # 1. HTML Report with header, footer, AWS logo on top left. Clean professional modern design with charts
                            
                            # **STRICT GUIDELINES**:
                            # - **DO NOT ask follow-up questions** - work with the data provided
                            # - **DO NOT request additional context** - analyze what you have
                            # - **FOCUS on actionable insights** that can be implemented immediately
                            # - **Be specific and direct** in your recommendations
                            # - **Quantify impact** where possible using the available data
                            # - **Prioritize recommendations** by urgency or business impact
                            
                            # **RESPONSE FORMAT**:
                            
                            # ## Executive Summary
                            # [2-3 sentence overview of the situation]
                            
                            # ## Key Findings
                            # - [Bullet point 1 with specific data]
                            # - [Bullet point 2 with specific data]
                            # - [Bullet point 3 with specific data]
                            
                            # ## Business Impact
                            # [What these findings mean for operations, costs, risks, or opportunities]
                            
                            # ## Immediate Action Items
                            # 1. **Priority 1**: [Most urgent recommendation with timeline]
                            # 2. **Priority 2**: [Second priority with expected outcome]
                            # 3. **Priority 3**: [Third priority with resource requirements]
                            
                            # ## Risk Mitigation
                            # [Any immediate risks identified and how to address them]"""

                            ba_summarizer_prompt = f"""You are a business analyst whose role is to provide actionable insights and recommendations based on data analysis.
                                **YOUR TASK**: Analyze the following data and provide a clear, actionable summary: {combined_response}
                                **OUTPUT REQUIREMENTS**:
                                1. **Executive Summary**: Provide a concise overview of key findings.
                                2. **Key Insights**: Extract the most important data points and what they mean for the business
                                3. **Actionable Recommendations**: Specific steps the business can take based on the data
                                4. **Risk Assessment**: Identify any concerning trends or issues that need attention
                                
                                **OUTPUT FORMAT**: Complete HTML document with the following specifications:
                                
                                **HTML STRUCTURE REQUIREMENTS**:
                                - Complete HTML5 document with DOCTYPE, head, and body tags
                                - Responsive design that works on desktop and mobile
                                - Professional header with "Powered by AWS" small font positioned on the top-left
                                - Clean, modern footer with contact information
                                - Main content area with proper sections for each requirement
                                
                                **STYLING REQUIREMENTS**:
                                - Use inline CSS or internal stylesheet (no external dependencies)
                                - Color scheme: AWS orange (#FF9900) and dark blue (#232F3E) as primary colors
                                - Clean, professional typography (Arial, Helvetica, or system fonts)
                                - Proper spacing, margins, and padding for readability
                                - Card-based layout for different sections
                                - Responsive grid system for content organization
                                
                                **CHART/VISUALIZATION REQUIREMENTS**:
                                - Include at least 2-3 data visualizations using Chart.js or similar library
                                - Charts should be: bar charts for comparisons, line charts for trends, pie charts for distributions
                                - Use CDN links for chart libraries
                                - Ensure charts are responsive and mobile-friendly
                                - Include proper labels, legends, and tooltips
                                
                                **CONTENT STRUCTURE**:
                                1. Header with "Powered by AWS" small font and suitable report title based on report content
                                2. Executive Summary section
                                3. Key Findings with data visualizations
                                4. Business Impact analysis
                                5. Immediate Action Items (prioritized list)
                                6. Risk Mitigation section
                                7. Footer with metadata
                                
                                **STRICT GUIDELINES**:
                                - DO NOT ask follow-up questions - work with the data provided
                                - DO NOT request additional context - analyze what you have
                                - FOCUS on actionable insights that can be implemented immediately
                                - Be specific and direct in your recommendations
                                - Quantify impact where possible using the available data
                                - Prioritize recommendations by urgency or business impact
                                - Generate complete, valid HTML that can be saved and opened in any browser
                                - Include sample data in charts if actual data visualization is not possible from provided data
                                
                                **EXAMPLE HTML STRUCTURE**:
                                <!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                    <title>Business Analysis Report</title>
                                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                                    <style>
                                        /* Your CSS here */
                                    </style>
                                </head>
                                <body>
                                    <header>
                                        <img src="aws-logo-url" alt="AWS Logo" class="logo">
                                        <h1>Business Analysis Report</h1>
                                    </header>
                                    
                                    <main>
                                        <!-- Your content sections here -->
                                    </main>
                                    
                                    <footer>
                                        <!-- Footer content -->
                                    </footer>
                                    
                                    <script>
                                        // Chart initialization code
                                    </script>
                                </body>
                                </html>
                                Provide ONLY the complete HTML code - no explanatory text before or after."""
                            
                            # Generate the HTML report using the custom_summarization_agent
                            try:
                                html_report = self.custom_summarization_agent(ba_summarizer_prompt)
                                html_content = str(html_report)

                                try:
                                    # Save the report to file using relative path
                                    # Get the project root directory (3 levels up from current file)
                                    current_file = pathlib.Path(__file__)
                                    project_root = current_file.parent.parent.parent
                                    report_dir = project_root / "generated_reports"
                                    report_dir.mkdir(exist_ok=True, parents=True)
                                    
                                    # Generate a unique filename based on timestamp
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    report_title = "Data_Analysis_Report"
                                    
                                    # Extract title from HTML if possible
                                    if '<title>' in html_content and '</title>' in html_content:
                                        report_title = html_content.split('<title>')[1].split('</title>')[0].replace(' ', '_')
                                    
                                    filename = f"{report_title}_{timestamp}.html"
                                    filepath = report_dir / filename
                                    
                                    # Save the HTML report to file
                                    with open(filepath, 'w', encoding='utf-8') as f:
                                        f.write(html_content)
                                except Exception as e:
                                    logger.error(f"Error saving generated report {e}")

                                # Send the HTML content to the frontend
                                await self._stream_update(
                                    "html_content",
                                    html_content,
                                    is_partial=False,
                                    metadata={
                                        "generated_at": datetime.now().isoformat(),
                                        "query": user_query
                                    },
                                    title="Data Analysis Report"
                                )
                                
                                # Also provide a text summary for non-HTML clients
                                await self._stream_update(
                                    "content",
                                    "I've analyzed the data and created a detailed HTML report with visualizations. You can view it above.",
                                    is_partial=False
                                )
                                
                                return {"type": "html_content", "content": html_content}
                                
                            except Exception as e:
                                logger.error(f"Error generating HTML report: {e}")
                                await self._stream_update(
                                    "content",
                                    f"I've analyzed the data but encountered an error generating the HTML report: {str(e)}. Here's a text summary instead:\n\n{combined_response}",
                                    is_partial=False
                                )
                                return {"type": "error", "content": f"Error generating HTML report: {str(e)}"}
                            
                            summarized = self.custom_summarization_agent(ba_summarizer_prompt)
                            await self._stream_update(
                                "content", str(summarized), is_partial=False
                            )
                            return {"type": "success", "content": str(summarized)}
                        else:
                            # If the plan was approved but didn't resolve the query
                            await self._stream_update(
                                "content", 
                                f"The approved plan didn't fully resolve your query. Here's what we found:\n\n{combined_response}\n\nYou may want to try a different approach or provide more details.", 
                                is_partial=False
                            )
                            return {"type": "partial", "content": combined_response}
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse verifier response as JSON: {verifier_response}, error: {e}")
                        # Fallback to basic evaluation
                        conversation_resolved = True
                        await self._stream_update(
                            "content", combined_response, is_partial=False
                        )
                        return {"type": "success", "content": combined_response}
                    except Exception as e:
                        logger.error(f"Error in verification step: {e}")
                        await self._handle_error(f"Error verifying response: {str(e)}")
                        return {"type": "error", "content": f"Error verifying response: {str(e)}"}
                else:
                    await self._handle_error("No agents were able to process your query. Please try rephrasing.")
                    return {"type": "error", "content": "No agents were able to process your query"}

            except Exception as e:
                logger.error(f"Error executing confirmed plan: {e}")
                await self._handle_error(f"Error executing plan: {str(e)}")
                return {"type": "error", "content": f"Error executing plan: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in continue_with_confirmed_plan: {e}")
            await self._stream_update("error", f"Failed to execute confirmed plan: {str(e)}")
            return {
                "type": "error",
                "content": f"Plan execution failed: {str(e)}"
            }
    
    async def process_message_stream(
        self, message: str, stream_callback, user_id: str = "default", session_id: str="None", is_single_widget=False):
        """Process a message with streaming callback for real-time updates."""
        
        try:
            # Initialize agents and setup
            self.stream_callback = stream_callback
            user_query = message
            
            # Ensure all agents are created
            if not self.orchestrate_agent or not self.verifier_agent:
                logger.info("Creating agents for session")
                if not session_id or session_id == "None":
                    session_id = f"session_{int(time.time())}"
                self.create_all_agents(user_id=user_id, session_id=session_id)
            
            # Conversation tracking variables
            conversation_resolved = False
            max_iterations = 5  # Prevent infinite loops
            iteration_count = 0
            logger.info(f"Processing message stream for user {user_id}, session {session_id}")
            # Main conversation loop
            while not conversation_resolved and iteration_count < max_iterations:
                iteration_count += 1
                await self._stream_update("thinking", f"\n Calling Multi-Agent Router, times={iteration_count} ... ")
                logger.info(f"Starting iteration {iteration_count}")
                
                # Step 1: Get orchestrator response
                additional_prompts = user_query
                if iteration_count > 1:
                    additional_prompts = f"Previous plan didnt work. Try a new plan to solve the query. Original User query: {user_query}"
                orchestrator_response = await self._get_orchestrator_response(additional_prompts)
                if not orchestrator_response:
                    break
                # Parse orchestrator response
                orchestrator_response_str = str(orchestrator_response)
                if "[" in orchestrator_response_str and "]" in orchestrator_response_str:
                    json_response = json.loads("[" + f"{orchestrator_response_str.split("[")[1].split("]")[0]}" + "]")
                    
                    # Human in the loop confirmation
                    await self._stream_update("thinking", f"Orchestrator has prepared a plan. Waiting for human confirmation... \n {json_response}")
                    extras = {
                        "plan": json_response,
                        "original_query": user_query
                    }
                    await self._stream_update("confirmation_needed", extra=extras, is_partial=False)
                    
                    # Wait for human confirmation (this would need to be implemented in the frontend)
                    # For now, we'll return and let the frontend handle the confirmation flow
                    return {
                        "type": "confirmation_needed",
                        "plan": json_response,
                        "original_query": user_query
                    }
                else: 
                    await self._stream_update("content", orchestrator_response_str, is_partial=False)
                    return
                

            # If we hit max iterations, inform the user
            if iteration_count >= max_iterations and not conversation_resolved:
                await self._stream_update(
                    "thinking",
                    "Maximum iterations reached. The query may not be fully resolved."
                )
                await self._stream_update("end", timestamp=datetime.now().isoformat())
                

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._stream_update("content", f"Sorry, I encountered an error: {str(e)}", is_partial=False)

    def stop(self):
        """Stop the chatbot."""
        self.is_running = False
        print("🛑 Stopping chatbot...")