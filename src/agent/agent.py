import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
            You are an English Learning Assistant. You help users study vocabulary.
            You have access to the following tools:
            Available tools:. 
            {tool_descriptions}

            Use the following format:
            Thought: your line of reasoning.
            Action: tool_name(arguments)
            Observation: result of the tool call.
            ... (repeat Thought/Action/Observation if needed)
            Final Answer: your final response.

            Rules:
            1. Always start with 'Thought:'.
            2. Format actions exactly as 'tool_name(args)'.
            3. Only use the tools provided above.
            4. If you have the answer or no tool is needed, provide 'Final Answer:' immediately.
            """


    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = user_input
        steps = 0
        
        # save conversation history for better context in future steps
        history = f"User: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            steps += 1
            # call LLM to get Thought + Action
            response = self.llm.generate(history, system_prompt=self.get_system_prompt())
            content = response["content"]
            
            # logging for telemetry
            tracker.track_request(
                provider=response["provider"],
                model=self.llm.model_name,
                usage=response["usage"],
                latency_ms=response["latency_ms"]
            )
            
            logger.info(f"--- Step {steps} ---\n{content}")
            history += content + "\n"

            # 1. final answer check
            if "Final Answer:" in content:
                final_answer = content.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps, "status": "success"})
                return final_answer

            # 2. parse action
            action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", content)
            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2).strip("'\"") # Làm sạch đối số
                
                # execute tool and get observation
                observation = self._execute_tool(tool_name, tool_args)
                logger.info(f"Observation: {observation}")
                
                history += f"Observation: {observation}\n"
            else:
                # format error - no action found, log and break to avoid infinite loop
                logger.log_event("AGENT_ERROR", {"msg": "Format error: No Action or Final Answer found"})
                break

        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        return "Xin lỗi, tôi không thể hoàn thành yêu cầu trong số bước cho phép."


    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                # TODO: Implement dynamic function calling or simple if/else
                try:
                    return tool['func'](args)
                except Exception as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    return f"Error executing {tool_name}: {str(e)}"
                return f"Result of {tool_name}"
        
        return f"Error: Tool '{tool_name}' not found."
