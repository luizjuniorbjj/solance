"""
AiSyster - Servico de Pesquisa Web Inteligente
Usa Claude para decidir quando pesquisar, gerar queries otimizadas e sintetizar resultados
"""

import json
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import anthropic

from app.config import (
    ANTHROPIC_API_KEY,
    AI_MODEL_FALLBACK,  # Haiku para decisoes rapidas
    WEB_SEARCH_ENABLED,
    WEB_SEARCH_MAX_RESULTS
)


# Prompt para Claude decidir se precisa pesquisar
SEARCH_DECISION_PROMPT = """Analise a mensagem do usuario e decida se precisa de pesquisa na internet.

PESQUISAR quando a pergunta requer:
- Informacoes atuais (precos, horarios, eventos, noticias)
- Dados que mudam com o tempo (clima, cotacoes, resultados)
- Informacoes sobre lugares especificos (enderecos, funcionamento)
- Fatos verificaveis sobre pessoas, empresas, produtos
- Estatisticas ou estudos recentes

NAO PESQUISAR quando:
- Conversa casual (oi, tudo bem, obrigado)
- Pedidos de oracao ou apoio emocional
- Perguntas biblicas/espirituais (voce ja sabe)
- Reflexoes pessoais do usuario
- Perguntas sobre voce mesma (AiSyster)

Mensagem do usuario: "{message}"
{location_context}

IMPORTANTE para queries:
- Se a pergunta envolve precos, lojas, servicos locais, eventos - INCLUA a localizacao nas queries
- Exemplo: "preco iPhone" com localizacao "Brasil" -> query: "preco iPhone 15 Brasil 2024"
- Exemplo: "restaurante japones" com localizacao "Sao Paulo" -> query: "melhores restaurantes japoneses Sao Paulo"

Responda APENAS em JSON:
{{
    "needs_search": true/false,
    "reason": "motivo breve",
    "search_queries": ["query1", "query2"] // apenas se needs_search=true, max 2 queries otimizadas COM localizacao quando relevante
}}"""


# Prompt para sintetizar resultados com fontes
SYNTHESIS_PROMPT = """Voce recebeu resultados de pesquisa na internet. Sintetize as informacoes relevantes.

REGRAS:
1. Seja conciso e direto
2. Cite as fontes com links quando disponivel
3. Indique se a informacao pode estar desatualizada
4. Se nao encontrou o que precisava, diga claramente
5. Formate de forma legivel

Pergunta original: {query}
Resultados da pesquisa:
{results}

Sintetize as informacoes mais relevantes:"""


class SmartWebSearchService:
    """
    Servico de pesquisa web inteligente
    - Claude decide se precisa pesquisar
    - Gera queries otimizadas
    - Sintetiza resultados com fontes
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.enabled = WEB_SEARCH_ENABLED

    async def analyze_search_need(self, message: str, user_location: Optional[str] = None) -> Dict:
        """
        Usa Claude (Haiku) para decidir se precisa pesquisar e gerar queries.
        Rapido e barato (~50 tokens).
        Considera a localizacao do usuario para queries mais precisas.
        """
        if not self.enabled:
            return {"needs_search": False, "reason": "Pesquisa desabilitada"}

        # Construir contexto de localizacao
        location_context = ""
        if user_location:
            location_context = f"Localizacao do usuario: {user_location}"

        try:
            response = self.client.messages.create(
                model=AI_MODEL_FALLBACK,  # Haiku = rapido e barato
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": SEARCH_DECISION_PROMPT.format(
                        message=message,
                        location_context=location_context
                    )
                }]
            )

            # Extrair JSON da resposta
            text = response.content[0].text.strip()

            # Limpar possíveis marcadores de código
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())

            return {
                "needs_search": result.get("needs_search", False),
                "reason": result.get("reason", ""),
                "queries": result.get("search_queries", []),
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except json.JSONDecodeError as e:
            print(f"[SEARCH] JSON parse error: {e}")
            return {"needs_search": False, "reason": "Erro ao analisar"}
        except Exception as e:
            print(f"[SEARCH] Analysis error: {e}")
            return {"needs_search": False, "reason": f"Erro: {str(e)}"}

    async def execute_search(
        self,
        queries: List[str],
        user_location: Optional[str] = None
    ) -> Dict:
        """
        Executa pesquisa na web usando Claude com web_search tool.
        """
        if not queries:
            return {"success": False, "results": [], "sources": []}

        try:
            # Construir prompt com todas as queries
            search_prompt = f"""Pesquise na internet para responder estas perguntas:

{chr(10).join(f"- {q}" for q in queries)}

{f"Localizacao do usuario: {user_location}" if user_location else ""}

INSTRUCOES:
1. Busque informacoes atuais e confiaveis
2. Para cada informacao, anote a fonte (site/URL)
3. Priorize fontes oficiais e confiaveis
4. Se for tema religioso, priorize fontes cristas respeitadas
5. Seja objetivo e factual"""

            # Mapear localização para código de país (API usa country codes)
            location_config = {}
            if user_location:
                if user_location in ["Estados Unidos", "USA", "EUA"]:
                    location_config = {
                        "type": "approximate",
                        "country": "US"
                    }
                elif user_location == "Brasil":
                    location_config = {
                        "type": "approximate",
                        "country": "BR"
                    }

            # Construir tool config
            web_search_tool = {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": WEB_SEARCH_MAX_RESULTS
            }
            if location_config:
                web_search_tool["user_location"] = location_config
                print(f"[SEARCH] Usando localização: {location_config}")

            response = self.client.messages.create(
                model=AI_MODEL_FALLBACK,  # Haiku com web search
                max_tokens=1500,
                tools=[web_search_tool],
                messages=[{
                    "role": "user",
                    "content": search_prompt
                }]
            )

            # Processar resposta e extrair fontes
            text_content = ""
            sources = []

            print(f"[SEARCH] Response blocks: {len(response.content)}")

            for block in response.content:
                print(f"[SEARCH] Block type: {block.type}")

                if block.type == "text":
                    text_content += block.text
                    # Extrair fontes do atributo citations (web_search_result_location)
                    if hasattr(block, 'citations') and block.citations:
                        print(f"[SEARCH] Found {len(block.citations)} citations in text block")
                        for citation in block.citations:
                            # citation tem type="web_search_result_location", url, title, cited_text
                            url = getattr(citation, 'url', None)
                            title = getattr(citation, 'title', None)

                            if url:
                                # Evitar duplicatas
                                if not any(s['url'] == url for s in sources):
                                    sources.append({
                                        "title": title or url.split('/')[2] if '/' in url else "Link",
                                        "url": url
                                    })
                                    print(f"[SEARCH] Source: {title[:50] if title else url[:30]}")
                elif block.type == "web_search_tool_result":
                    # Formato alternativo - resultados em bloco separado
                    print(f"[SEARCH] web_search_tool_result found!")
                    if hasattr(block, 'content') and block.content:
                        for item in block.content:
                            url = getattr(item, 'url', None)
                            title = getattr(item, 'title', None)
                            if url and title and not any(s['url'] == url for s in sources):
                                sources.append({"title": title, "url": url})
                                print(f"[SEARCH] Source from result: {title[:50] if len(title) > 50 else title}")

            print(f"[SEARCH] Total sources found: {len(sources)}")
            print(f"[SEARCH] Content length: {len(text_content)}")

            return {
                "success": True,
                "content": text_content,
                "sources": sources[:5],  # Max 5 fontes
                "queries": queries,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except anthropic.APIError as e:
            print(f"[SEARCH] API Error: {e}")
            return {"success": False, "error": str(e), "results": [], "sources": []}
        except Exception as e:
            print(f"[SEARCH] Error: {e}")
            return {"success": False, "error": str(e), "results": [], "sources": []}

    async def smart_search(
        self,
        message: str,
        user_context: str = "",
        user_location: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Pipeline completo de pesquisa inteligente:
        1. Claude analisa se precisa pesquisar
        2. Se sim, gera queries otimizadas
        3. Executa pesquisa
        4. Retorna resultado formatado com fontes

        Returns:
            Dict com:
            - needs_search: bool
            - searching_for: str (o que esta buscando, para UI)
            - content: str (resultado da pesquisa)
            - sources: List[Dict] (fontes com titulo e URL)
            Ou None se nao precisar pesquisar
        """
        # 1. Analisar necessidade (passa localizacao para queries mais precisas)
        analysis = await self.analyze_search_need(message, user_location)

        if not analysis.get("needs_search"):
            return None

        queries = analysis.get("queries", [])
        if not queries:
            # Fallback: usar a mensagem como query
            queries = [message[:100]]

        print(f"[SEARCH] Pesquisando: {queries}")

        # 2. Executar pesquisa
        search_result = await self.execute_search(queries, user_location)

        if not search_result.get("success"):
            print(f"[SEARCH] Falha: {search_result.get('error')}")
            return None

        # 3. Formatar resultado
        return {
            "needs_search": True,
            "searching_for": analysis.get("reason", queries[0]),
            "content": search_result.get("content", ""),
            "sources": search_result.get("sources", []),
            "queries": queries,
            "tokens_used": analysis.get("tokens_used", 0) + search_result.get("tokens_used", 0)
        }

    def format_for_context(self, search_result: Dict) -> str:
        """
        Formata resultado da pesquisa para incluir no contexto do chat.
        """
        if not search_result:
            return ""

        content = search_result.get("content", "")
        sources = search_result.get("sources", [])

        # Formatar fontes
        sources_text = ""
        if sources:
            sources_text = "\n\nFontes:\n" + "\n".join(
                f"- [{s.get('title', 'Link')}]({s.get('url', '')})"
                for s in sources[:3]
            )

        return f"""[INFORMACAO DA INTERNET - Use para responder]
{content}
{sources_text}
[FIM DA PESQUISA]"""

    def format_search_indicator(self, search_result: Dict) -> str:
        """
        Retorna texto para mostrar ao usuario que esta pesquisando.
        Ex: "Buscando informacoes sobre precos de iPhone..."
        """
        if not search_result:
            return ""

        searching_for = search_result.get("searching_for", "")
        queries = search_result.get("queries", [])

        if searching_for:
            return f"Buscando: {searching_for}"
        elif queries:
            return f"Pesquisando: {queries[0][:50]}..."
        return "Pesquisando na internet..."


# Manter compatibilidade com nome antigo
class WebSearchService(SmartWebSearchService):
    """Alias para compatibilidade"""

    async def search_and_summarize(
        self,
        message: str,
        user_context: str = "",
        user_location: Optional[str] = None
    ) -> Optional[str]:
        """
        Metodo legado para compatibilidade.
        Retorna string formatada ou None.
        """
        result = await self.smart_search(message, user_context, user_location)
        if result:
            return self.format_for_context(result)
        return None

    def should_search(self, message: str) -> Tuple[bool, str]:
        """
        Metodo legado - agora e sincrono e simples.
        Para decisao real, use analyze_search_need (async).
        """
        # Fallback simples para compatibilidade
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Nao podemos rodar async aqui, retorna True para analisar depois
                return True, "Analise pendente"
            result = loop.run_until_complete(self.analyze_search_need(message))
            return result.get("needs_search", False), result.get("reason", "")
        except:
            return True, "Analise pendente"


# Instancia global
web_search_service = WebSearchService()
