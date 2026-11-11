import re
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from src.config import config

class LlmClient:
    """Cliente unificado para comunicação com modelos de LLM via OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 120.0,
        transport: Optional[httpx.AsyncBaseTransport] = None
    ):
        self.api_key = api_key if api_key is not None else config.openrouter_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport
        # Headers HTTP devem ser estritamente ASCII
        self.headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://app-artigos-cientificos.local",
            "X-Title": "Pipeline Autonomo de Teses e Artigos - Stricto Sensu"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        fallback_model: Optional[str] = None
    ) -> str:
        """Gera texto acadêmico via OpenRouter com fallback automático e tratamento resiliente."""
        if not self.api_key:
            # Modo offline / mock quando chave não estiver configurada
            return f"[Modo Offline Heurístico] Síntese gerada para o modelo {model}:\n{prompt[:300]}..."

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        endpoint = f"{self.base_url}/chat/completions"

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                    response = await client.post(endpoint, json=payload, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()

                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        # Remove blocos de raciocínio interno (<think>...</think>) do texto final se presentes
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                        return content
            except Exception as e:
                if attempt == 0 and fallback_model and fallback_model != model:
                    payload["model"] = fallback_model
                    await asyncio.sleep(1.0)
                    continue
                # Se falhar após retry, levanta ou retorna mensagem descritiva
                raise RuntimeError(f"Falha na chamada LLM para o modelo {model}: {e}")

        return ""
