import httpx
import json
import logging
import asyncio
from typing import Any, Dict, Optional, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.LLM_API_KEY
        self.base_url = self.settings.LLM_API_BASE
        self.model = self.settings.LLM_MODEL
        
        if not self.api_key:
            logger.warning("LLM_API_KEY is not set. LLM features will not work.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout))
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Union[Dict[str, Any], str]:
        """
        Generate content using the configured LLM.
        
        Args:
            system_prompt: The system instruction.
            user_prompt: The user's input/request.
            json_schema: Optional JSON schema to enforce structured output.
            temperature: Creativity parameter (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            
        Returns:
            Dict if json_schema is provided, otherwise str.
        """
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.FRONTEND_URL, # Required by OpenRouter
            "X-Title": self.settings.PROJECT_NAME,      # Required by OpenRouter
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_schema:
            # For OpenRouter/OpenAI compatible APIs that support response_format
            payload["response_format"] = {"type": "json_object"}
            # Append schema instruction to system prompt if not already present
            if "JSON" not in system_prompt and "json" not in system_prompt:
                messages[0]["content"] += f"\n\nYou must output valid JSON matching this schema:\n{json.dumps(json_schema, indent=2)}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                if json_schema:
                    try:
                        # Find the first '{' and last '}' to extract JSON if there's markdown code blocks
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start != -1 and end != -1:
                            json_str = content[start:end]
                            return json.loads(json_str)
                        else:
                            # Fallback: try parsing the whole string
                            return json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM JSON output: {content}")
                        raise ValueError(f"LLM output was not valid JSON: {e}")
                
                return content

            except httpx.HTTPStatusError as e:
                logger.error(f"LLM API Error: {e.response.text}")
                raise

# Singleton instance
llm_service = LLMService()
