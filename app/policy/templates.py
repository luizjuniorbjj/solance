"""
AiSyster - Safe Response Templates
Templates de respostas seguras para situacoes de risco

Conforme CLAUDE_PLAYBOOK.md Secao 3.1:
- Respostas com limites claros
- Nao validar praticas abusivas
- Orientar com prudencia
- Encaminhar ajuda humana quando necessario
"""

from typing import Optional
from .types import RiskCategory, RiskLevel


class SafeResponseTemplates:
    """
    Templates de respostas seguras para cada categoria de risco.

    Principios (Playbook 2.2):
    - Ser pastoral, acolhedora, pratica e biblica
    - Confrontar exploracao religiosa com firmeza e amor
    - Incentivar comunhao, igreja local e responsabilidade pessoal
    """

    # ==========================================
    # CRISE - Encaminhamento urgente
    # ==========================================

    CRISIS_RESPONSE = """Eu percebo que voce esta passando por um momento muito dificil, e quero que saiba que sua vida tem valor imenso.

Por favor, busque ajuda agora:
- **CVV (Centro de Valorizacao da Vida)**: Ligue 188 ou acesse cvv.org.br - 24 horas, gratuito
- **SAMU**: 192 (emergencia)
- **UBS ou CAPS** mais proximo

Voce nao precisa enfrentar isso sozinho(a). Deus te ama, e ha pessoas preparadas para te ajudar neste momento.

Se puder, procure tambem um pastor ou lider de confianca da sua igreja. Estou aqui para conversar, mas este momento pede ajuda humana especializada."""

    ABUSE_RESPONSE = """O que voce esta descrevendo e serio e voce merece estar em seguranca.

Recursos importantes:
- **Ligue 180** - Central de Atendimento a Mulher (24h, gratuito)
- **Ligue 190** - Policia (emergencia)
- **Delegacia da Mulher** mais proxima

Voce nao e culpado(a) pelo que esta acontecendo. Buscar ajuda e um ato de coragem, nao de fraqueza. Deus deseja sua protecao e bem-estar."""

    # ==========================================
    # MANIPULACAO FINANCEIRA
    # ==========================================

    FINANCIAL_MANIPULATION_RESPONSE = """Entendo que questoes de fe e finan[c]as podem se misturar, mas preciso ser honesta com voce.

A Biblia nos ensina generosidade, mas nunca como "moeda de troca" com Deus. Textos como Malaquias 3:10 falam de confian[c]a em Deus, nao de transacao comercial.

Alguns pontos importantes:
- Deus nao "vende" bencaos por ofertas
- Nenhum pastor ou igreja deve prometer cura, prosperidade ou milagres em troca de dinheiro
- Contribuicoes devem ser voluntarias, alegres, dentro das suas possibilidades

Se alguem esta pressionando voce a dar dinheiro com promessas espirituais, isso e manipulacao - nao e o evangelho.

Posso conversar mais sobre o que a Biblia realmente ensina sobre generosidade?"""

    # ==========================================
    # REVELACAO DIVINA / PROFECIAS
    # ==========================================

    REVELATION_RESPONSE = """Eu entendo que experiencias espirituais podem parecer muito reais e significativas.

Porem, preciso ser prudente com voce: a Biblia nos ensina a testar todas as coisas (1 Tessalonicenses 5:21) e que devemos ter discernimento.

Algumas orientacoes:
- Revela[c]oes verdadeiras NUNCA contradizem a Escritura
- Cuidado com "profetas" que pedem dinheiro ou obediencia absoluta
- Nenhum numero, CPF ou dado pessoal e "revelado" por Deus - isso e golpe

Se alguem afirmou ter uma "revelacao" sobre voce pedindo algo em troca, isso e manipulacao espiritual.

Recomendo conversar com um pastor de confian[c]a sobre essas experiencias. Posso ajudar de outra forma?"""

    DOCUMENT_REVELATION_RESPONSE = """Preciso ser muito direta: ninguem recebe "revelacao divina" de numeros de documentos como CPF, RG, contas bancarias ou senhas.

Isso e caracteristica de golpe, nao de acao de Deus.

A Biblia nao promete esse tipo de informacao sobrenatural. Se alguem disse ter recebido seus dados pessoais "de Deus", essa pessoa esta:
- Cometendo fraude
- Usando engenharia social
- Explorando sua fe

Por favor, nao compartilhe dados pessoais com base nisso. Se ja compartilhou, procure se proteger (troque senhas, monitore contas).

Posso ajudar a pensar em passos de protecao?"""

    # ==========================================
    # DIAGNOSTICO MEDICO
    # ==========================================

    MEDICAL_ADVICE_RESPONSE = """Eu me preocupo com voce e entendo que questoes de saude podem ser angustiantes.

Porem, nao posso dar orientacoes medicas - isso seria irresponsavel da minha parte. Voce merece atendimento profissional adequado.

O que posso fazer:
- Orar com voce por saude e sabedoria
- Conversar sobre como lidar emocionalmente com a situacao
- Encorajar que procure um medico

O que nao posso fazer:
- Diagnosticar doencas
- Recomendar remedios ou tratamentos
- Substituir atendimento medico

Fe e medicina nao sao opostas. Deus trabalha atraves de medicos tambem. Cuide-se!"""

    # ==========================================
    # MANIPULACAO ESPIRITUAL
    # ==========================================

    SPIRITUAL_MANIPULATION_RESPONSE = """O que voce descreve me preocupa. A fe genuina traz liberdade, nao medo ou controle.

Sinais de manipulacao espiritual incluem:
- Ameacas de inferno ou maldi[c]ao se desobedecer
- "So eu/nos podemos te salvar/libertar"
- Isolamento de familia e amigos
- Controle financeiro em nome de Deus

Jesus disse que a verdade liberta (Joao 8:32). Se sua experiencia religiosa traz medo, culpa paralisante ou dependencia de uma pessoa especifica, algo esta errado.

Voce tem valor aos olhos de Deus independente de qualquer lider humano. Recomendo conversar com alguem de confian[c]a fora desse grupo.

Quer conversar mais sobre isso?"""

    # ==========================================
    # AUTO-SABOTAGEM DA IA (bloqueio de tentativa)
    # ==========================================

    AI_IDENTITY_RESPONSE = """Eu sou a AiSyster, sua companheira de fe nesta jornada.

Prefiro focar no que importa: como posso te ajudar hoje? Ha algo no seu cora[c]ao que gostaria de compartilhar?

Estou aqui para conversar sobre sua vida, sua fe, seus desafios. Vamos la?"""

    # ==========================================
    # GUARDRAILS (instrucoes adicionais ao LLM)
    # ==========================================

    GUARDRAILS = {
        RiskCategory.FINANCIAL_MANIPULATION: """
[GUARDRAIL ATIVO - FINANCEIRO]
O usuario pode estar em contexto de exploracao financeira religiosa.
NAO legitime "teologia da prosperidade" ou "semeadura com retorno".
Seja pastoral mas firme sobre manipulacao.
""",

        RiskCategory.DIVINE_REVELATION: """
[GUARDRAIL ATIVO - REVELACAO]
O usuario pode estar em contexto de manipulacao por "profetas/revelacoes".
NAO valide revelacoes pessoais, profecias ou "palavras de Deus" nao-biblicas.
Incentive discernimento biblico e consulta a lideres de confianca.
""",

        RiskCategory.MEDICAL_ADVICE: """
[GUARDRAIL ATIVO - SAUDE]
O usuario pode estar buscando orientacao medica.
NAO de diagnosticos ou recomende tratamentos.
Incentive busca por profissional de saude.
Fe e medicina sao complementares.
""",

        RiskCategory.SPIRITUAL_MANIPULATION: """
[GUARDRAIL ATIVO - MANIPULACAO]
O usuario pode estar em contexto de controle espiritual abusivo.
NAO legitime ameacas espirituais ou dependencia de lideres.
Enfatize liberdade em Cristo e valor proprio diante de Deus.
""",

        RiskCategory.AI_SELF_SABOTAGE: """
[GUARDRAIL ATIVO - IDENTIDADE]
O usuario pode estar tentando fazer a IA se desacreditar.
NAO fale sobre ser IA, modelo, treinamento ou limitacoes tecnicas.
Mantenha persona pastoral e redirecione para conversa util.
""",
    }

    @classmethod
    def get_safe_response(cls, category: RiskCategory, level: RiskLevel) -> Optional[str]:
        """
        Retorna resposta segura para uma categoria de risco.

        Args:
            category: Categoria do risco detectado
            level: Nivel do risco

        Returns:
            String com resposta segura, ou None se nao precisar bloquear
        """
        if level == RiskLevel.CRITICAL:
            if category == RiskCategory.CRISIS:
                return cls.CRISIS_RESPONSE
            if category == RiskCategory.DOCUMENT_REVELATION:
                return cls.DOCUMENT_REVELATION_RESPONSE

        if level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            responses = {
                RiskCategory.FINANCIAL_MANIPULATION: cls.FINANCIAL_MANIPULATION_RESPONSE,
                RiskCategory.DIVINE_REVELATION: cls.REVELATION_RESPONSE,
                RiskCategory.MEDICAL_ADVICE: cls.MEDICAL_ADVICE_RESPONSE,
                RiskCategory.SPIRITUAL_MANIPULATION: cls.SPIRITUAL_MANIPULATION_RESPONSE,
                RiskCategory.AI_SELF_SABOTAGE: cls.AI_IDENTITY_RESPONSE,
                RiskCategory.CRISIS: cls.CRISIS_RESPONSE,
            }
            return responses.get(category)

        return None

    @classmethod
    def get_guardrail(cls, category: RiskCategory) -> Optional[str]:
        """
        Retorna instrucao de guardrail para adicionar ao prompt.

        Args:
            category: Categoria do risco detectado

        Returns:
            String com instrucao de guardrail, ou None
        """
        return cls.GUARDRAILS.get(category)

    @classmethod
    def get_all_guardrails(cls, categories: list) -> str:
        """
        Retorna todas as instrucoes de guardrail para multiplas categorias.

        Args:
            categories: Lista de RiskCategory detectadas

        Returns:
            String concatenada com todos os guardrails
        """
        guardrails = []
        for cat in categories:
            g = cls.get_guardrail(cat)
            if g:
                guardrails.append(g)

        return "\n".join(guardrails) if guardrails else ""
