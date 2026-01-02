"""
SoulHaven - Serviço de Pesquisa Web
Integra pesquisa na internet via Claude Web Search Tool
"""

import re
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import anthropic

from app.config import (
    ANTHROPIC_API_KEY,
    AI_MODEL_PRIMARY,
    WEB_SEARCH_ENABLED,
    WEB_SEARCH_MAX_RESULTS
)


class WebSearchService:
    """
    Serviço de pesquisa web usando Claude com ferramenta de busca integrada
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.enabled = WEB_SEARCH_ENABLED

    def should_search(self, message: str) -> Tuple[bool, str]:
        """
        Detecta se a mensagem precisa de pesquisa na internet.

        Returns:
            Tuple[bool, str]: (precisa_pesquisar, motivo)
        """
        if not self.enabled:
            return False, "Pesquisa desabilitada"

        message_lower = message.lower()

        # Padrões que indicam necessidade de informação atual
        current_info_patterns = [
            # Perguntas sobre atualidade
            r'\b(atual|atualmente|hoje|agora|2024|2025|2026)\b',
            r'\b(últim[oa]s?|recente|novo|nova)\b',
            r'\b(notícia|noticia|acontec|acontess)\b',

            # Perguntas sobre eventos
            r'\b(conferência|conferencia|evento|congresso)\b',
            r'\b(copa|olimpíada|olimpiada|eleição|eleicao)\b',

            # Perguntas sobre produtos/preços
            r'\b(preço|preco|custo|quanto custa|onde comprar|compra[r]?)\b',
            r'\b(loja|amazon|mercado livre|shopee)\b',

            # Perguntas sobre lugares
            r'\b(endereço|endereco|localização|localizacao|onde fica)\b',
            r'\b(horário|horario|funciona|abre|fecha)\b',
            r'\b(igreja|templo|comunidade|denominação|denominacao)\s+(em|no|na|perto)\b',

            # Perguntas sobre pessoas públicas
            r'\b(pastor|pregador|teólogo|teologo|autor|escritor)\s+\w+\b',
            r'\b(quem é|quem e)\s+\w+\b',

            # Perguntas sobre livros/recursos
            r'\b(livro|podcast|canal|vídeo|video)\s+(sobre|de|do|da)\b',
            r'\b(recomend|sugest|indica)\w*\s+(livro|podcast|canal)\b',

            # Perguntas sobre clima/tempo
            r'\b(tempo|clima|previsão|previsao|temperatura)\b',

            # Perguntas sobre estatísticas/dados
            r'\b(estatística|estatistica|dados|pesquisa|estudo)\s+(sobre|recente|atual)\b',

            # Verbos que indicam busca de informação atual
            r'\b(pesquisa|busca|procura|encontra)\w*\s+(sobre|para|de)\b',
        ]

        for pattern in current_info_patterns:
            if re.search(pattern, message_lower):
                return True, f"Padrão detectado: {pattern}"

        # Perguntas que NÃO precisam de pesquisa (já sabemos)
        no_search_patterns = [
            r'\b(como você está|tudo bem|oi|olá|bom dia|boa tarde|boa noite)\b',
            r'\b(obrigad[oa]|amém|valeu|legal)\b',
            r'\b(ora por mim|ore por mim|preciso de oração)\b',
            r'\b(me sinto|estou sentindo|estou triste|estou ansios)\b',
            r'\b(o que a bíblia|o que a biblia|versículo|versiculo)\b',
            r'\b(significado de|o que significa)\s+\w+\s+(na bíblia|bíblico)\b',
        ]

        for pattern in no_search_patterns:
            if re.search(pattern, message_lower):
                return False, "Tema não requer pesquisa"

        return False, "Nenhum padrão de pesquisa detectado"

    async def search(
        self,
        query: str,
        context: str = "",
        user_location: Optional[str] = None
    ) -> Dict:
        """
        Realiza pesquisa web usando Claude com ferramenta de busca.

        Args:
            query: Termo de busca
            context: Contexto adicional para refinar a busca
            user_location: Localização do usuário (se disponível)

        Returns:
            Dict com resultados da pesquisa
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Pesquisa web desabilitada",
                "results": []
            }

        try:
            # Construir prompt para a pesquisa
            search_prompt = f"""Pesquise na internet sobre: {query}

{f"Contexto adicional: {context}" if context else ""}
{f"Localização do usuário: {user_location}" if user_location else ""}

Retorne informações relevantes, atuais e confiáveis.
Priorize fontes cristãs confiáveis quando o tema for religioso.
Para outros temas, use fontes gerais confiáveis.

IMPORTANTE:
- Seja objetivo e factual
- Cite as fontes quando possível
- Indique a data das informações quando relevante
- Se não encontrar informações confiáveis, diga claramente"""

            # Chamar Claude com ferramenta de web search
            response = self.client.messages.create(
                model=AI_MODEL_PRIMARY,
                max_tokens=1024,
                tools=[{
                    "type": "web_search",
                    "name": "web_search",
                    "max_uses": WEB_SEARCH_MAX_RESULTS
                }],
                messages=[{
                    "role": "user",
                    "content": search_prompt
                }]
            )

            # Processar resposta
            search_results = []
            final_text = ""

            for block in response.content:
                if block.type == "text":
                    final_text = block.text
                elif block.type == "tool_use" and block.name == "web_search":
                    # Capturar resultados da busca se disponíveis
                    if hasattr(block, 'input'):
                        search_results.append(block.input)

            return {
                "success": True,
                "query": query,
                "summary": final_text,
                "results": search_results,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "timestamp": datetime.now().isoformat()
            }

        except anthropic.APIError as e:
            print(f"[WEB_SEARCH] API Error: {e}")
            return {
                "success": False,
                "error": f"Erro na API: {str(e)}",
                "results": []
            }
        except Exception as e:
            print(f"[WEB_SEARCH] Error: {e}")
            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}",
                "results": []
            }

    async def search_and_summarize(
        self,
        message: str,
        user_context: str = "",
        user_location: Optional[str] = None
    ) -> Optional[str]:
        """
        Pesquisa e retorna um resumo para ser incluído no contexto.

        Retorna None se não precisar pesquisar ou se falhar.
        """
        should_search, reason = self.should_search(message)

        if not should_search:
            return None

        print(f"[WEB_SEARCH] Pesquisando: {message[:50]}... Motivo: {reason}")

        result = await self.search(
            query=message,
            context=user_context,
            user_location=user_location
        )

        if result["success"] and result.get("summary"):
            return f"""[INFORMAÇÃO ATUAL DA INTERNET]
{result["summary"]}
[FIM DA PESQUISA]"""

        return None


# Instância global para reutilização
web_search_service = WebSearchService()
