"""
AiSyster - Rotas de Devocional
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.ai_service import AIService

router = APIRouter(prefix="/devotional", tags=["Devocional"])


# ============================================
# MODELOS
# ============================================

class DevotionalResponse(BaseModel):
    date: str
    versiculo: str
    referencia: str
    meditacao: str
    oracao: str


class DevotionalInteraction(BaseModel):
    salvo: Optional[bool] = None
    nota_pessoal: Optional[str] = None


# ============================================
# DEVOCIONAIS PRÉ-DEFINIDOS (para MVP)
# ============================================

DEVOTIONALS = [
    {
        "versiculo": "O Senhor é o meu pastor; nada me faltará.",
        "referencia": "Salmo 23:1",
        "meditacao": """Davi foi pastor antes de ser rei. Quando diz que o Senhor é seu pastor,
está falando de experiência própria. Ele sabia o que um bom pastor faz: guia, protege, alimenta,
cuida. E é exatamente isso que Deus faz por nós.

Quando você diz "nada me faltará", não significa que terá tudo que quer, mas que terá tudo que precisa.
O pastor não dá luxos às ovelhas, mas garante o essencial: pasto, água, segurança.

Hoje, descanse nessa verdade: você tem um Pastor que conhece suas necessidades e cuida de você.""",
        "oracao": "Senhor, obrigado por ser meu Pastor. Ajuda-me a confiar que em Ti nada me faltará. Amém."
    },
    {
        "versiculo": "Não andem ansiosos por coisa alguma, mas em tudo, pela oração e súplicas, e com ação de graças, apresentem seus pedidos a Deus.",
        "referencia": "Filipenses 4:6",
        "meditacao": """Paulo escreveu isso da prisão. Não de um retiro confortável, mas acorrentado.
E ainda assim, disse: não fiquem ansiosos.

A solução que ele dá não é "pare de se preocupar" (isso não funciona), mas "transforme preocupação em oração".
Cada vez que a ansiedade apertar, use isso como lembrete para conversar com Deus.

E note: "com ação de graças". Mesmo no meio da angústia, há sempre algo pelo que agradecer.
A gratidão muda a perspectiva.""",
        "oracao": "Pai, entrego minha ansiedade a Ti agora. Transforma minha preocupação em confiança. Obrigado por me ouvir. Amém."
    },
    {
        "versiculo": "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.",
        "referencia": "Mateus 11:28",
        "meditacao": """Jesus não disse "resolva seus problemas primeiro e depois venha".
Ele disse: venha CANSADO. Venha SOBRECARREGADO. Venha como você está.

Muitas vezes achamos que precisamos estar bem para nos aproximar de Deus.
Mas é justamente quando não estamos bem que Ele nos convida a vir.

O alívio não vem por magia — vem pelo relacionamento. Quando descansamos Nele,
os problemas podem continuar, mas não precisamos mais carregá-los sozinhos.""",
        "oracao": "Jesus, estou cansado(a). Venho a Ti como estou. Alivia meu coração. Amém."
    },
    {
        "versiculo": "Porque sou eu que conheço os planos que tenho para vocês, diz o Senhor, planos de fazê-los prosperar e não de causar dano, planos de dar a vocês esperança e um futuro.",
        "referencia": "Jeremias 29:11",
        "meditacao": """Esse versículo foi escrito para um povo em exílio. Eles tinham perdido tudo:
terra, templo, liberdade. E Deus disse: eu tenho planos para vocês.

Às vezes parece que nossa vida saiu do controle. Que não há esperança.
Mas Deus vê além do momento presente.

O futuro que Ele promete não é necessariamente fácil, mas é BOM.
Porque vem Dele. E Ele não erra.""",
        "oracao": "Senhor, quando eu não entender o presente, ajuda-me a confiar que Tu tens um futuro bom para mim. Amém."
    },
    {
        "versiculo": "Tudo posso naquele que me fortalece.",
        "referencia": "Filipenses 4:13",
        "meditacao": """Esse versículo não é sobre conseguir qualquer coisa que você quiser.
Leia o contexto: Paulo está falando de contentamento em qualquer situação — abundância ou escassez.

"Tudo posso" significa: consigo enfrentar qualquer circunstância.
Não com minhas forças, mas com as Dele.

Quando você se sentir incapaz, lembre: não é sobre sua capacidade.
É sobre a força Dele em você.""",
        "oracao": "Senhor, reconheço que sozinho(a) não consigo. Mas em Ti, tudo posso. Fortalece-me hoje. Amém."
    },
    {
        "versiculo": "O Senhor é a minha luz e a minha salvação; de quem terei medo?",
        "referencia": "Salmo 27:1",
        "meditacao": """O medo é uma das emoções mais paralisantes que existem.
Medo do futuro, medo do fracasso, medo da rejeição.

Davi conhecia o medo. Fugiu de Saul, enfrentou gigantes, liderou exércitos.
Mas sua resposta ao medo era sempre a mesma: voltar-se para Deus.

Quando Deus é sua luz, as trevas não têm poder.
Quando Ele é sua salvação, nenhum inimigo é grande demais.""",
        "oracao": "Senhor, Tu és minha luz. Dissipa as trevas do medo no meu coração. Em Ti estou seguro(a). Amém."
    },
    {
        "versiculo": "Confia no Senhor de todo o teu coração e não te estribes no teu próprio entendimento.",
        "referencia": "Provérbios 3:5",
        "meditacao": """Confiar "de todo o coração" é difícil. Gostamos de entender, controlar, planejar.
Mas Deus nos convida a soltar — não o bom senso, mas a ilusão de que sabemos tudo.

Há situações que não fazem sentido. Dores que parecem inúteis. Esperas intermináveis.
Nesses momentos, a confiança não é cega — é baseada em quem Deus é, não no que entendemos.

Ele vê o quadro completo. Nós vemos um fragmento.""",
        "oracao": "Pai, escolho confiar em Ti mesmo quando não entendo. Tu és fiel. Amém."
    }
]


# ============================================
# ROTAS
# ============================================

@router.get("/today", response_model=DevotionalResponse)
async def get_today_devotional(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Retorna o devocional do dia
    """
    today = date.today()

    # Usa o dia do ano para selecionar devocional (rotaciona)
    day_of_year = today.timetuple().tm_yday
    devotional_index = day_of_year % len(DEVOTIONALS)
    devotional = DEVOTIONALS[devotional_index]

    # Registra que o usuário viu o devocional
    await db.log_audit(
        user_id=current_user["user_id"],
        action="devotional_viewed",
        details={"date": today.isoformat()}
    )

    return DevotionalResponse(
        date=today.isoformat(),
        versiculo=devotional["versiculo"],
        referencia=devotional["referencia"],
        meditacao=devotional["meditacao"],
        oracao=devotional["oracao"]
    )


@router.post("/today/save")
async def save_devotional(
    interaction: DevotionalInteraction,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Salva o devocional do dia na coleção do usuário
    """
    today = date.today()
    day_of_year = today.timetuple().tm_yday
    devotional_index = day_of_year % len(DEVOTIONALS)
    devotional = DEVOTIONALS[devotional_index]

    # Salva como conteúdo salvo
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO saved_content (user_id, tipo, conteudo, referencia, nota_pessoal, is_favorite)
            VALUES ($1, 'devocional', $2, $3, $4, $5)
            """,
            current_user["user_id"],
            f"{devotional['versiculo']}\n\n{devotional['meditacao']}",
            devotional["referencia"],
            interaction.nota_pessoal,
            interaction.salvo or False
        )

    return {"message": "Devocional salvo na sua coleção"}


@router.get("/generate")
async def generate_devotional(
    tema: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Gera um devocional personalizado (premium)
    """
    user = await db.get_user_by_id(current_user["user_id"])

    if not user.get("is_premium", False):
        return {
            "error": "Recurso premium",
            "message": "Devocionais personalizados estão disponíveis para assinantes."
        }

    ai_service = AIService(db)
    devotional = await ai_service.generate_devotional(tema)

    return DevotionalResponse(
        date=date.today().isoformat(),
        **devotional
    )
