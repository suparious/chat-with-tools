import json
import yaml
from openai import OpenAI
from .tools import discover_tools
from .config_manager import ConfigManager, get_openai_client
from .utils import DebugLogger

class OpenRouterAgent:
    def __init__(self, config_path="config.yaml", silent=False):
        # Use centralized config manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Silent mode for orchestrator (suppresses debug output)
        self.silent = silent
        
        # Initialize debug logger
        self.debug_logger = DebugLogger(self.config)
        self.debug_logger.log_separator("Agent Initialization")
        self.debug_logger.info("Initializing OpenRouterAgent", config_path=config_path, silent=silent)
        
        # Initialize OpenAI client using centralized function
        self.client = get_openai_client()
        self.debug_logger.info(f"OpenAI client initialized", 
                               model=self.config_manager.get_model(),
                               base_url=self.config_manager.get_base_url())
        
        # Discover tools dynamically
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        self.debug_logger.info(f"Discovered {len(self.discovered_tools)} tools", 
                               tools=list(self.discovered_tools.keys()))
        
        # Build OpenRouter tools array
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        
        # Build tool mapping
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
        self.debug_logger.info("Agent initialization complete")
    
    
    def call_llm(self, messages):
        """Make OpenRouter API call with tools"""
        try:
            model = self.config_manager.get_model()
            self.debug_logger.log_llm_call(model, messages)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.tools
            )
            
            self.debug_logger.log_llm_call(model, messages, response=response)
            return response
        except Exception as e:
            self.debug_logger.log_llm_call(model, messages, error=str(e))
            raise Exception(f"LLM call failed: {str(e)}")
    
    def handle_tool_call(self, tool_call):
        """Handle a tool call and return the result message"""
        tool_name = None
        try:
            # Extract tool name and arguments
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            self.debug_logger.log_tool_call(tool_name, tool_args)
            
            # Call appropriate tool from tool_mapping
            if tool_name in self.tool_mapping:
                tool_result = self.tool_mapping[tool_name](**tool_args)
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
            
            self.debug_logger.log_tool_call(tool_name, tool_args, result=tool_result)
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.debug_logger.log_tool_call(tool_name or "unknown", 
                                           tool_args if 'tool_args' in locals() else {},
                                           error=error_msg)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name or "unknown",
                "content": json.dumps({"error": error_msg})
            }
    
    def run(self, user_input: str):
        """Run the agent with user input and return FULL conversation content"""
        self.debug_logger.log_separator(f"Agent Run Started")
        self.debug_logger.info("User input received", input=user_input)
        
        # Initialize messages with system prompt and user input
        messages = [
            {
                "role": "system",
                "content": self.config['system_prompt']
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        # Track all assistant responses for full content capture
        full_response_content = []
        
        # Implement agentic loop from OpenRouter docs
        max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            self.debug_logger.log_agent_iteration(iteration, max_iterations)
            
            if not self.silent:
                print(f"🔄 Agent iteration {iteration}/{max_iterations}")
            
            # Call LLM
            response = self.call_llm(messages)
            
            # Add the response to messages
            assistant_message = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })
            
            # Capture assistant content for full response
            if assistant_message.content:
                full_response_content.append(assistant_message.content)
            
            # Check if there are tool calls
            if assistant_message.tool_calls:
                if not self.silent:
                    print(f"🔧 Agent making {len(assistant_message.tool_calls)} tool call(s)")
                # Handle each tool call
                task_completed = False
                for tool_call in assistant_message.tool_calls:
                    if not self.silent:
                        print(f"   📞 Calling tool: {tool_call.function.name}")
                    tool_result = self.handle_tool_call(tool_call)
                    messages.append(tool_result)
                    
                    # Check if this was the task completion tool
                    if tool_call.function.name == "mark_task_complete":
                        task_completed = True
                        self.debug_logger.info("Task completion tool called - ending agent loop")
                        if not self.silent:
                            print("✅ Task completion tool called - exiting loop")
                        # Return FULL conversation content, not just completion message
                        final_response = "\n\n".join(full_response_content)
                        self.debug_logger.info("Agent run completed", final_response_length=len(final_response))
                        self.debug_logger.log_separator("Agent Run Completed")
                        return final_response
                
                # If task was completed, we already returned above
                if task_completed:
                    return "\n\n".join(full_response_content)
            else:
                if not self.silent:
                    print("💭 Agent responded without tool calls - continuing loop")
            
            # Continue the loop regardless of whether there were tool calls or not
        
        # If max iterations reached, return whatever content we gathered
        return "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached. The agent may be stuck in a loop."