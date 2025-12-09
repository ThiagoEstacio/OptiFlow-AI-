"""
Ollama LLM Client
=================

Provides async functions for communicating with Ollama LLM:
- call_ollama: Non-streaming completion with circuit breaker
- call_ollama_stream: Streaming completion (SSE)
- OllamaConfig: Configuration dataclass
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import httpx
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client"""
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model_name: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    timeout: float = 120.0
    stream_timeout: float = 60.0
    keep_alive: str = "30m"

    # Generation options
    temperature: float = 0.05
    top_p: float = 0.8
    top_k: int = 20
    num_predict: int = 1000
    num_predict_stream: int = 800
    num_ctx: int = 4096
    num_gpu: int = 99
    num_thread: int = 4
    repeat_penalty: float = 1.1
    stop_sequences: List[str] = None

    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = ["</response>", "\n\n\n"]


# Default configuration
DEFAULT_CONFIG = OllamaConfig()


class OllamaError(Exception):
    """Base exception for Ollama errors"""
    pass


class OllamaConnectionError(OllamaError):
    """Cannot connect to Ollama server"""
    pass


class OllamaAPIError(OllamaError):
    """Ollama API returned an error"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Ollama API error ({status_code}): {message}")


async def call_ollama(
    messages: List[Dict[str, str]],
    config: Optional[OllamaConfig] = None,
    circuit_breaker=None
) -> str:
    """
    Call Ollama API for chat completion.
    Optimized for MAXIMUM SPEED with GPU - Target: 3-8 seconds.

    Args:
        messages: List of chat messages with 'role' and 'content'
        config: Optional OllamaConfig, uses DEFAULT_CONFIG if not provided
        circuit_breaker: Optional circuit breaker instance for fault tolerance

    Returns:
        Generated text response

    Raises:
        OllamaConnectionError: Cannot connect to Ollama
        OllamaAPIError: API returned an error
    """
    cfg = config or DEFAULT_CONFIG

    async def _ollama_request():
        """Inner function for circuit breaker wrapping"""
        logger.debug(f"Calling Ollama at {cfg.base_url}")

        async with httpx.AsyncClient(timeout=cfg.timeout) as client:
            response = await client.post(
                f"{cfg.base_url}/api/chat",
                json={
                    "model": cfg.model_name,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": cfg.keep_alive,
                    "options": {
                        "temperature": cfg.temperature,
                        "top_p": cfg.top_p,
                        "top_k": cfg.top_k,
                        "num_predict": cfg.num_predict,
                        "num_ctx": cfg.num_ctx,
                        "num_gpu": cfg.num_gpu,
                        "num_thread": cfg.num_thread,
                        "repeat_penalty": cfg.repeat_penalty,
                        "stop": cfg.stop_sequences,
                    }
                }
            )

            logger.debug(f"Ollama response - Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                raise OllamaAPIError(response.status_code, response.text)

    try:
        if circuit_breaker:
            # Execute through circuit breaker
            result = await circuit_breaker.call_async(_ollama_request)
        else:
            result = await _ollama_request()
        return result

    except httpx.ConnectError:
        raise OllamaConnectionError("Cannot connect to Ollama. Make sure Ollama is running")


async def call_ollama_stream(
    messages: List[Dict[str, str]],
    config: Optional[OllamaConfig] = None
) -> AsyncGenerator[str, None]:
    """
    Call Ollama API with streaming enabled.
    Yields chunks of text as they are generated (SSE - Server-Sent Events).

    This provides real-time feedback to users, making 8s queries feel instant!

    Args:
        messages: List of chat messages with 'role' and 'content'
        config: Optional OllamaConfig, uses DEFAULT_CONFIG if not provided

    Yields:
        Text chunks as they are generated

    Raises:
        OllamaConnectionError: Cannot connect to Ollama
        OllamaAPIError: API returned an error
    """
    cfg = config or DEFAULT_CONFIG

    try:
        async with httpx.AsyncClient(timeout=cfg.stream_timeout) as client:
            async with client.stream(
                "POST",
                f"{cfg.base_url}/api/chat",
                json={
                    "model": cfg.model_name,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": cfg.keep_alive,
                    "options": {
                        "temperature": cfg.temperature,
                        "top_p": cfg.top_p,
                        "top_k": cfg.top_k,
                        "num_predict": cfg.num_predict_stream,
                        "num_ctx": cfg.num_ctx,
                        "num_gpu": cfg.num_gpu,
                        "num_thread": cfg.num_thread,
                        "repeat_penalty": cfg.repeat_penalty,
                        "stop": cfg.stop_sequences,
                    }
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise OllamaAPIError(
                        response.status_code,
                        error_text.decode()
                    )

                # Stream chunks from Ollama
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:
                                    yield content

                            # Check if done
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON chunk: {line}")
                            continue

    except httpx.ConnectError:
        raise OllamaConnectionError("Cannot connect to Ollama. Make sure Ollama is running")
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        raise


def extract_json_from_response(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract JSON widget configurations from LLM response.

    Args:
        text: Raw LLM response text

    Returns:
        List of parsed JSON objects or None if not found
    """
    import re

    # Find JSON code blocks
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)

    if not matches:
        return None

    try:
        # Parse the first JSON block found
        json_str = matches[0].strip()
        parsed = json.loads(json_str)

        # Ensure it's a list
        if isinstance(parsed, dict):
            return [parsed]
        return parsed
    except json.JSONDecodeError:
        return None
