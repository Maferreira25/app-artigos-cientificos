import httpx
from typing import Optional, Dict, Any, List

class JurisprudenciaMcpClient:
    """Cliente assíncrono padrão MCP (Model Context Protocol) para pesquisa jurídica."""
    
    def __init__(
        self,
        mcp_url: str = "http://localhost:8787",
        bearer_token: Optional[str] = None,
        timeout: float = 120.0,
        transport: Optional[httpx.AsyncBaseTransport] = None
    ):
        self.endpoint = mcp_url.rstrip("/") + "/mcp"
        self.timeout = timeout
        self.transport = transport
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Doutorado-Pipeline-Client/1.2"
        }
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executa ferramenta remota via JSON-RPC 2.0 com fallback automático resiliente."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await client.post(self.endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

        # Tratamento de erro JSON-RPC e fallback automático
        if "error" in data and data["error"]:
            err = data["error"]
            err_code = err.get("code")
            err_msg = err.get("message", "Erro MCP")
            
            # Fallback resiliente caso ferramenta específica falhe ou não seja reconhecida
            if err_code == -32602 or "Unknown tool" in err_msg or "not found" in err_msg.lower():
                fallback_query = (
                    arguments.get("query")
                    or arguments.get("tema")
                    or arguments.get("tese")
                    or arguments.get("norma")
                )
                if fallback_query and tool_name != "pesquisar_jurisprudencia":
                    return await self.call_tool("pesquisar_jurisprudencia", {"query": str(fallback_query)})
            
            raise RuntimeError(f"Erro MCP [{err_code}]: {err_msg}")

        result = data.get("result", {})
        if result.get("isError"):
            raise RuntimeError(f"Falha de execução na Tool MCP: {result}")

        contents = result.get("content", [])
        texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
        return "\n".join(texts)

    # Métodos de Conveniência Acadêmica e Jurisprudencial
    async def buscar_teses_vinculantes(self, tema: str) -> str:
        """Mapeia teses de Repercussão Geral (STF) e Recursos Repetitivos (STJ)."""
        return await self.call_tool("buscar_precedentes_qualificados", {"tema": tema, "max_wait_seconds": 60})

    async def obter_linha_do_tempo(self, tema: str) -> str:
        """Constrói a evolução histórica da jurisprudência em linha do tempo."""
        return await self.call_tool("linha_do_tempo_precedentes", {"tema": tema, "max_wait_seconds": 90})

    async def mapear_overruling(self, tema: str) -> str:
        """Identifica viragens jurisprudenciais (overruling) e mutações constitucionais."""
        return await self.call_tool("listar_overruling_tema", {"tema": tema, "max_wait_seconds": 90})

    async def extrair_jurimetria(self, tema: str, tribunal: str = "STJ") -> str:
        """Extrai distribuição quantitativa de decisões por órgão fracionário e relator."""
        return await self.call_tool("analisar_jurimetria", {"tema": tema, "tribunal": tribunal, "max_wait_seconds": 60})

    async def pesquisar_ementas(self, query: str, tribunal: Optional[str] = None) -> str:
        """Busca ementas e fundamentações oficiais de julgados."""
        args: Dict[str, Any] = {"query": query}
        if tribunal:
            args["tribunal"] = tribunal
        return await self.call_tool("pesquisar_jurisprudencia", args)

    async def buscar_citacoes_dispositivo(self, norma: str, artigo: str) -> str:
        """Verifica a interpretação jurisprudencial de um dispositivo legal controvertido."""
        return await self.call_tool("buscar_citacoes_dispositivo", {"norma": norma, "artigo": artigo})

    async def analisar_tese_juridica(self, tese: str, tribunal: str = "STJ") -> str:
        """Testa pontos de vulnerabilidade da tese contra a jurisprudência dominante."""
        return await self.call_tool("analisar_tese_juridica", {"tese": tese, "tribunal": tribunal})

    async def comparar_teses(self, tese_a: str, tese_b: str) -> str:
        """Compara teses antagônicas para subsidiar tópicos dialéticos."""
        return await self.call_tool("comparar_teses_juridicas", {"tese_a": tese_a, "tese_b": tese_b})
