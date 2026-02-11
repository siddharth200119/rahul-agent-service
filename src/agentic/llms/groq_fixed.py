import re
from typing import Dict, List, Optional
from RAW.llms import GroqLLM
from RAW.modals import Tool

class FixedGroqLLM(GroqLLM):
    """
    Subclass of GroqLLM to fix tool conversion issues without modifying the RAW package.
    """
    def _convert_tool_to_groq_format(self, tool: Tool) -> Dict:
        """Convert Tool to Groq (OpenAI) format with improved schema handling"""
        name = tool.name
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
             name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: param.to_property()
                        for param in tool.parameters
                    },
                    "required": [
                        param.name for param in tool.parameters if param.required
                    ],
                    "additionalProperties": False # Required for some Groq models to trigger native tool use
                }
            }
        }
