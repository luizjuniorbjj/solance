"""
AiSyster - Fundamentação Teológica Reformada
Base doutrinária completa para respostas biblicamente precisas
"""

# ============================================
# CREDOS E CONFISSÕES HISTÓRICAS
# ============================================

CONFISSOES_REFORMADAS = {
    "credo_apostolico": {
        "nome": "Credo Apostólico",
        "data": "~150 d.C.",
        "resumo": "Síntese da fé cristã: Trindade, criação, encarnação, morte, ressurreição, ascensão, retorno de Cristo, igreja, perdão, ressurreição do corpo.",
        "uso": "Base comum de toda a cristandade histórica"
    },
    "credo_niceno": {
        "nome": "Credo Niceno-Constantinopolitano",
        "data": "325/381 d.C.",
        "resumo": "Define a divindade plena de Cristo (homoousios) e do Espírito Santo contra heresias arianas.",
        "uso": "Definição da Trindade"
    },
    "credo_atanasiano": {
        "nome": "Credo Atanasiano",
        "data": "~500 d.C.",
        "resumo": "Exposição detalhada da Trindade e das duas naturezas de Cristo.",
        "uso": "Precisão trinitária e cristológica"
    },
    "confissao_westminster": {
        "nome": "Confissão de Fé de Westminster",
        "data": "1646",
        "resumo": "Exposição sistemática da fé reformada: Escrituras, Deus, decreto, criação, providência, queda, aliança, Cristo, salvação, igreja, sacramentos, escatologia.",
        "uso": "Base doutrinária principal para presbiterianos e reformados",
        "catecismos": ["Catecismo Maior", "Catecismo Menor"]
    },
    "catecismo_heidelberg": {
        "nome": "Catecismo de Heidelberg",
        "data": "1563",
        "resumo": "129 perguntas e respostas sobre consolo cristão: miséria, libertação, gratidão.",
        "uso": "Ensino devocional e pastoral reformado"
    },
    "canones_dort": {
        "nome": "Cânones de Dort",
        "data": "1618-1619",
        "resumo": "Cinco pontos do calvinismo: depravação total, eleição incondicional, expiação limitada, graça irresistível, perseverança dos santos (TULIP).",
        "uso": "Definição soteriológica reformada"
    },
    "confissao_belga": {
        "nome": "Confissão Belga",
        "data": "1561",
        "resumo": "37 artigos sobre a fé reformada: Escrituras, Trindade, criação, queda, eleição, Cristo, igreja, magistrados.",
        "uso": "Confissão das igrejas reformadas continentais"
    },
    "segunda_confissao_londres": {
        "nome": "Segunda Confissão de Londres",
        "data": "1689",
        "resumo": "Versão batista da Confissão de Westminster, mantendo a teologia reformada com eclesiologia batista.",
        "uso": "Base doutrinária para batistas reformados"
    }
}

# ============================================
# CINCO SOLAS DA REFORMA
# ============================================

CINCO_SOLAS = {
    "sola_scriptura": {
        "latim": "Sola Scriptura",
        "portugues": "Somente a Escritura",
        "significado": "A Bíblia é a única autoridade infalível para fé e prática. Tradição e razão são úteis, mas subordinadas à Escritura.",
        "versiculo_chave": "2 Timóteo 3:16-17",
        "aplicacao": "Toda resposta deve ser fundamentada nas Escrituras, não em opinião humana."
    },
    "sola_fide": {
        "latim": "Sola Fide",
        "portugues": "Somente a Fé",
        "significado": "A justificação é recebida somente pela fé, não por obras. A fé é o instrumento, não a base da salvação.",
        "versiculo_chave": "Efésios 2:8-9",
        "aplicacao": "Nunca sugerir que obras humanas contribuem para a salvação."
    },
    "sola_gratia": {
        "latim": "Sola Gratia",
        "portugues": "Somente a Graça",
        "significado": "A salvação é inteiramente obra da graça de Deus, não mérito humano. O homem está morto em pecados até que Deus o regenere.",
        "versiculo_chave": "Efésios 2:4-5",
        "aplicacao": "Enfatizar a iniciativa divina na salvação e santificação."
    },
    "solus_christus": {
        "latim": "Solus Christus",
        "portugues": "Somente Cristo",
        "significado": "Cristo é o único mediador entre Deus e os homens. Não há outro nome pelo qual devamos ser salvos.",
        "versiculo_chave": "1 Timóteo 2:5",
        "aplicacao": "Apontar sempre para Cristo como único caminho, verdade e vida."
    },
    "soli_deo_gloria": {
        "latim": "Soli Deo Gloria",
        "portugues": "Somente a Deus a Glória",
        "significado": "O propósito final de todas as coisas é a glória de Deus, não a felicidade humana.",
        "versiculo_chave": "Romanos 11:36",
        "aplicacao": "O objetivo da vida cristã é glorificar a Deus, não autorrealização."
    }
}

# ============================================
# TULIP - CINCO PONTOS DO CALVINISMO
# ============================================

TULIP = {
    "T": {
        "ingles": "Total Depravity",
        "portugues": "Depravação Total",
        "explicacao": "O pecado afetou todas as partes do ser humano. O homem natural é incapaz de buscar a Deus ou fazer qualquer bem espiritual por si mesmo.",
        "versiculos": ["Romanos 3:10-12", "Efésios 2:1-3", "Jeremias 17:9"],
        "implicacao_pastoral": "O pecador precisa de regeneração, não apenas de informação. Só o Espírito pode dar vida."
    },
    "U": {
        "ingles": "Unconditional Election",
        "portugues": "Eleição Incondicional",
        "explicacao": "Deus escolheu salvar alguns antes da fundação do mundo, não baseado em méritos previstos, mas segundo sua vontade soberana.",
        "versiculos": ["Efésios 1:4-5", "Romanos 9:11-16", "João 15:16"],
        "implicacao_pastoral": "A salvação é dom de Deus. Humildade e gratidão, não orgulho."
    },
    "L": {
        "ingles": "Limited Atonement",
        "portugues": "Expiação Limitada (ou Particular)",
        "explicacao": "Cristo morreu eficazmente pelos eleitos. Sua morte não apenas tornou a salvação possível, mas garantiu a salvação de todos por quem morreu.",
        "versiculos": ["João 10:11,15", "Efésios 5:25", "Mateus 1:21"],
        "implicacao_pastoral": "A morte de Cristo é eficaz, não meramente potencial. Segurança para os que creem."
    },
    "I": {
        "ingles": "Irresistible Grace",
        "portugues": "Graça Irresistível (ou Eficaz)",
        "explicacao": "Quando Deus decide salvar alguém, a pessoa inevitavelmente virá a Cristo. A graça salvadora não pode ser frustrada.",
        "versiculos": ["João 6:37,44", "Filipenses 1:29", "Atos 16:14"],
        "implicacao_pastoral": "Confiança na obra de Deus. A conversão é obra dele, não nossa persuasão."
    },
    "P": {
        "ingles": "Perseverance of the Saints",
        "portugues": "Perseverança dos Santos",
        "explicacao": "Todos os eleitos perseverarão na fé até o fim. Deus preserva os seus. Quem verdadeiramente nasceu de novo não pode perder a salvação.",
        "versiculos": ["João 10:28-29", "Filipenses 1:6", "Romanos 8:38-39"],
        "implicacao_pastoral": "Segurança eterna para os crentes. Não é licença para pecar, mas conforto na luta."
    }
}

# ============================================
# TEÓLOGOS REFORMADOS - REFERÊNCIAS
# ============================================

TEOLOGOS_REFORMADOS = {
    # Reformadores históricos
    "calvino": {
        "nome": "João Calvino",
        "periodo": "1509-1564",
        "obras_principais": ["Institutas da Religião Cristã", "Comentários Bíblicos"],
        "contribuicao": "Sistematização da teologia reformada. Exposição bíblica. Doutrina da predestinação.",
        "citacoes_uteis": [
            "O coração do homem é uma fábrica perpétua de ídolos.",
            "Não há nenhum conhecimento de Deus onde não há humildade.",
            "Devemos sempre considerar que somos estudantes, não mestres."
        ]
    },
    "lutero": {
        "nome": "Martinho Lutero",
        "periodo": "1483-1546",
        "obras_principais": ["Catecismo Menor", "95 Teses", "Da Vontade Cativa"],
        "contribuicao": "Justificação pela fé. Autoridade das Escrituras. Sacerdócio de todos os crentes.",
        "citacoes_uteis": [
            "A Escritura é seu próprio intérprete.",
            "Paz se possível, verdade a qualquer custo."
        ]
    },
    "agostinho": {
        "nome": "Agostinho de Hipona",
        "periodo": "354-430",
        "obras_principais": ["Confissões", "A Cidade de Deus", "Sobre a Graça e o Livre Arbítrio"],
        "contribuicao": "Doutrina da graça. Pecado original. Predestinação. Base teológica da Reforma.",
        "citacoes_uteis": [
            "Fizeste-nos para ti, Senhor, e nosso coração está inquieto enquanto não repousar em ti.",
            "A graça não encontra homens aptos, mas os torna aptos."
        ]
    },

    # Puritanos
    "owen": {
        "nome": "John Owen",
        "periodo": "1616-1683",
        "obras_principais": ["A Mortificação do Pecado", "Comunhão com Deus", "A Morte da Morte na Morte de Cristo"],
        "contribuicao": "Teologia da expiação. Vida cristã prática. Mortificação do pecado.",
        "citacoes_uteis": [
            "Esteja matando o pecado, ou o pecado estará matando você.",
            "Nenhum homem odeia o pecado por si mesmo, apenas por suas consequências."
        ]
    },
    "bunyan": {
        "nome": "John Bunyan",
        "periodo": "1628-1688",
        "obras_principais": ["O Peregrino", "Graça Abundante ao Principal dos Pecadores"],
        "contribuicao": "Alegoria da vida cristã. Graça para pecadores.",
        "citacoes_uteis": [
            "Você não alcançou o pico mais alto do que precisa aprender até ter aprendido que é um tolo."
        ]
    },

    # Teólogos americanos clássicos
    "edwards": {
        "nome": "Jonathan Edwards",
        "periodo": "1703-1758",
        "obras_principais": ["Pecadores nas Mãos de um Deus Irado", "A Liberdade da Vontade", "Afeições Religiosas"],
        "contribuicao": "Grande Avivamento. Teologia das afeições. Soberania de Deus.",
        "citacoes_uteis": [
            "A resolução de uma pessoa que busca a santidade deve ser: Resolvo buscar minha felicidade em Deus."
        ]
    },
    "spurgeon": {
        "nome": "Charles Spurgeon",
        "periodo": "1834-1892",
        "obras_principais": ["O Tesouro de Davi", "Sermões"],
        "contribuicao": "Pregação expositiva. Evangelismo calvinista. Vida devocional.",
        "citacoes_uteis": [
            "Defenda a Bíblia? Eu preferiria defender um leão!",
            "Visite muitos bons livros, mas viva na Bíblia."
        ]
    },

    # Teólogos reformados contemporâneos brasileiros
    "augustus_nicodemus": {
        "nome": "Augustus Nicodemus Lopes",
        "periodo": "1956-presente",
        "obras_principais": ["O Que Estão Fazendo com a Igreja", "A Bíblia e Seus Intérpretes", "O Culto Espiritual"],
        "contribuicao": "Teologia reformada no Brasil. Crítica ao neopentecostalismo. Hermenêutica bíblica.",
        "temas_fortes": ["Suficiência das Escrituras", "Adoração bíblica", "Crítica ao pragmatismo eclesiástico"],
        "citacoes_uteis": [
            "A Bíblia não é um livro de autoajuda; é a revelação de Deus ao homem.",
            "Nosso problema não é falta de fé, mas falta de conhecimento do objeto da fé."
        ]
    },
    "hernandes_dias_lopes": {
        "nome": "Hernandes Dias Lopes",
        "periodo": "1960-presente",
        "obras_principais": ["Comentários Expositivos", "De Pastor a Pastor", "A Família Segundo o Coração de Deus"],
        "contribuicao": "Pregação expositiva no Brasil. Comentários bíblicos acessíveis.",
        "temas_fortes": ["Família cristã", "Vida devocional", "Santidade prática"],
        "citacoes_uteis": [
            "A oração não muda Deus, muda a nós.",
            "Não existe atalho para a maturidade espiritual."
        ]
    },
    "yago_martins": {
        "nome": "Yago Martins",
        "periodo": "1992-presente",
        "obras_principais": ["Deus Não Vai Deixar Você Feliz", "Podcast Dois Dedos de Teologia"],
        "contribuicao": "Teologia reformada para jovens. Desconstrução de mitos evangélicos. Apologética cultural.",
        "temas_fortes": ["Contra teologia da prosperidade", "Sofrimento cristão", "Cosmovisão bíblica"],
        "citacoes_uteis": [
            "Deus não prometeu felicidade, prometeu santidade.",
            "O evangelho não é sobre você se sentir bem, é sobre Cristo ser glorificado."
        ]
    },
    "franklin_ferreira": {
        "nome": "Franklin Ferreira",
        "periodo": "1969-presente",
        "obras_principais": ["Teologia Cristã", "Teologia Sistemática"],
        "contribuicao": "Teologia sistemática reformada. Formação teológica no Brasil.",
        "temas_fortes": ["Doutrina de Deus", "Cristologia", "Eclesiologia"]
    },
    "mauro_meister": {
        "nome": "Mauro Meister",
        "periodo": "1965-presente",
        "obras_principais": ["Provérbios: Comentário Expositivo", "Orientação Vocacional"],
        "contribuicao": "Educação teológica. Sabedoria bíblica aplicada.",
        "temas_fortes": ["Literatura sapiencial", "Vida cristã prática"]
    },

    # Teólogos reformados contemporâneos americanos/internacionais
    "tim_keller": {
        "nome": "Timothy Keller",
        "periodo": "1950-2023",
        "obras_principais": ["A Razão da Fé", "O Deus Pródigo", "Pregação", "O Significado do Casamento"],
        "contribuicao": "Apologética cultural. Ministério urbano. Evangelismo de céticos. Graça no centro.",
        "temas_fortes": ["Evangelho e cultura", "Idolatria do coração", "Graça transformadora"],
        "citacoes_uteis": [
            "O evangelho é: somos mais pecadores e falhos do que jamais ousamos acreditar, mas ao mesmo tempo somos mais amados e aceitos do que jamais ousamos esperar.",
            "A religião opera sob o princípio: 'Eu obedeço, portanto sou aceito'. O evangelho opera sob o princípio: 'Sou aceito através de Cristo, portanto obedeço'.",
            "O ídolo é qualquer coisa mais importante para você do que Deus."
        ]
    },
    "john_piper": {
        "nome": "John Piper",
        "periodo": "1946-presente",
        "obras_principais": ["Desiring God", "Não Desperdice Sua Vida", "Os Prazeres de Deus"],
        "contribuicao": "Hedonismo cristão. Soberania de Deus. Missões. Alegria em Deus.",
        "temas_fortes": ["Deus é mais glorificado quando somos mais satisfeitos Nele", "Sofrimento", "Missões"],
        "citacoes_uteis": [
            "Deus é mais glorificado em nós quando estamos mais satisfeitos Nele.",
            "Missões existem porque adoração não existe.",
            "Um dos maiores usos da fé é mantê-la quando não temos explicação."
        ]
    },
    "rc_sproul": {
        "nome": "R.C. Sproul",
        "periodo": "1939-2017",
        "obras_principais": ["A Santidade de Deus", "Eleitos de Deus", "Sola Gratia"],
        "contribuicao": "Ensino teológico acessível. Santidade de Deus. Apologética clássica.",
        "temas_fortes": ["Santidade de Deus", "Justificação pela fé", "Soberania"],
        "citacoes_uteis": [
            "A essência do pecado é substituir a vontade de Deus pela nossa.",
            "Todo mundo tem uma teologia. A questão é se é uma boa teologia."
        ]
    },
    "sinclair_ferguson": {
        "nome": "Sinclair Ferguson",
        "periodo": "1948-presente",
        "obras_principais": ["O Espírito Santo", "Toda a Cristo"],
        "contribuicao": "Teologia do Espírito Santo. Vida cristã. Puritanismo acessível.",
        "temas_fortes": ["União com Cristo", "Espírito Santo", "Santificação"]
    },
    "kevin_deyoung": {
        "nome": "Kevin DeYoung",
        "periodo": "1977-presente",
        "obras_principais": ["O Buraco em Nossa Santidade", "O Que é a Missão da Igreja?"],
        "contribuicao": "Santificação prática. Eclesiologia. Apologética cultural.",
        "temas_fortes": ["Santidade", "Ética sexual bíblica", "Igreja local"]
    },
    "voddie_baucham": {
        "nome": "Voddie Baucham",
        "periodo": "1969-presente",
        "obras_principais": ["Tolerância Falha", "Discipulado Familiar"],
        "contribuicao": "Apologética. Família bíblica. Crítica cultural.",
        "temas_fortes": ["Cosmovisão bíblica", "Educação cristã", "Masculinidade bíblica"]
    },
    "paul_washer": {
        "nome": "Paul Washer",
        "periodo": "1961-presente",
        "obras_principais": ["O Evangelho de Jesus Cristo", "Recuperando o Evangelho"],
        "contribuicao": "Pregação profética. Evangelismo bíblico. Crítica ao evangelicalismo superficial.",
        "temas_fortes": ["Arrependimento genuíno", "Santidade", "Evidências da salvação"]
    }
}

# ============================================
# TEMAS TEOLÓGICOS REFORMADOS
# ============================================

TEMAS_REFORMADOS = {
    "soberania_de_deus": {
        "definicao": "Deus governa sobre todas as coisas. Nada acontece fora de seu decreto. Ele é o Rei absoluto do universo.",
        "versiculos": ["Salmo 115:3", "Daniel 4:35", "Efésios 1:11", "Romanos 9:19-21"],
        "implicacao_pratica": "Conforto no sofrimento. Deus está no controle. Nada é acaso."
    },
    "depravacao_humana": {
        "definicao": "O pecado afetou todas as partes do ser humano. Sem a graça, o homem é incapaz de buscar a Deus.",
        "versiculos": ["Romanos 3:10-18", "Efésios 2:1-3", "Gênesis 6:5"],
        "implicacao_pratica": "Necessidade absoluta da graça. Não confiamos em nós mesmos."
    },
    "alianca": {
        "definicao": "Deus se relaciona com seu povo através de alianças. A aliança da graça une todos os eleitos desde Adão até hoje.",
        "versiculos": ["Gênesis 17:7", "Jeremias 31:31-34", "Hebreus 8:6-13"],
        "implicacao_pratica": "Pertencemos ao povo de Deus. Continuidade entre AT e NT."
    },
    "justificacao": {
        "definicao": "Ato judicial de Deus que declara o pecador justo com base na obra de Cristo, recebida pela fé.",
        "versiculos": ["Romanos 3:21-26", "Romanos 4:5", "2 Coríntios 5:21"],
        "implicacao_pratica": "Segurança da salvação. Não baseada em nosso desempenho."
    },
    "santificacao": {
        "definicao": "Processo pelo qual Deus nos torna progressivamente mais santos. É obra de Deus em nós, mas requer nossa cooperação.",
        "versiculos": ["Filipenses 2:12-13", "1 Tessalonicenses 4:3", "Hebreus 12:14"],
        "implicacao_pratica": "Lutamos contra o pecado. A santidade não é opcional."
    },
    "meios_de_graca": {
        "definicao": "Os canais pelos quais Deus comunica sua graça: Palavra, sacramentos, oração.",
        "versiculos": ["Romanos 10:17", "Atos 2:42", "Mateus 28:19-20"],
        "implicacao_pratica": "Valorize a pregação, ceia, batismo, oração. Deus age através deles."
    },
    "vocacao": {
        "definicao": "Todo trabalho honesto é serviço a Deus. Não há divisão entre sagrado e secular.",
        "versiculos": ["Colossenses 3:23-24", "1 Coríntios 10:31"],
        "implicacao_pratica": "Trabalhe para a glória de Deus em qualquer profissão."
    },
    "lei_e_evangelho": {
        "definicao": "A lei mostra nosso pecado e nos guia na santidade. O evangelho oferece graça em Cristo. Ambos são necessários.",
        "versiculos": ["Romanos 3:20", "Gálatas 3:24", "Romanos 7:12"],
        "implicacao_pratica": "A lei não salva, mas ainda guia. O evangelho liberta para obedecer."
    },
    "perseveranca": {
        "definicao": "Os verdadeiros crentes perseverarão até o fim. Deus os preserva. Segurança eterna.",
        "versiculos": ["João 10:28-29", "Filipenses 1:6", "1 Pedro 1:5"],
        "implicacao_pratica": "Segurança para os crentes. A falta de perseverança revela falsa conversão."
    },
    "providencia": {
        "definicao": "Deus sustenta e governa todas as coisas para seus propósitos. Nada está fora de seu controle.",
        "versiculos": ["Mateus 10:29-31", "Romanos 8:28", "Gênesis 50:20"],
        "implicacao_pratica": "Confiança em tempos difíceis. Deus tem um plano."
    }
}

# ============================================
# CATECISMO MENOR DE WESTMINSTER - PERGUNTAS SELECIONADAS
# ============================================

CATECISMO_MENOR = {
    1: {
        "pergunta": "Qual é o fim principal do homem?",
        "resposta": "O fim principal do homem é glorificar a Deus, e gozá-lo para sempre.",
        "versiculos": ["1 Coríntios 10:31", "Romanos 11:36", "Salmo 73:25-26"]
    },
    4: {
        "pergunta": "O que é Deus?",
        "resposta": "Deus é espírito, infinito, eterno e imutável em seu ser, sabedoria, poder, santidade, justiça, bondade e verdade.",
        "versiculos": ["João 4:24", "Salmo 90:2", "Tiago 1:17", "Apocalipse 4:8"]
    },
    14: {
        "pergunta": "O que é pecado?",
        "resposta": "Pecado é qualquer falta de conformidade com a lei de Deus, ou qualquer transgressão dessa lei.",
        "versiculos": ["1 João 3:4", "Tiago 4:17"]
    },
    21: {
        "pergunta": "Quem é o Redentor dos eleitos de Deus?",
        "resposta": "O único Redentor dos eleitos de Deus é o Senhor Jesus Cristo, que, sendo o Filho eterno de Deus, se fez homem, e assim foi e continua a ser Deus e homem, em duas naturezas distintas, e uma só pessoa, para sempre.",
        "versiculos": ["1 Timóteo 2:5-6", "João 1:14", "Romanos 9:5"]
    },
    33: {
        "pergunta": "O que é justificação?",
        "resposta": "Justificação é um ato da livre graça de Deus, pelo qual ele perdoa todos os nossos pecados, e nos aceita como justos diante dele, somente por causa da justiça de Cristo a nós imputada, e recebida só pela fé.",
        "versiculos": ["Romanos 3:24-25", "2 Coríntios 5:21", "Romanos 5:1"]
    },
    35: {
        "pergunta": "O que é santificação?",
        "resposta": "Santificação é a obra da livre graça de Deus pela qual somos renovados em todo o nosso ser, segundo a imagem de Deus, e habilitados a morrer cada vez mais para o pecado e a viver para a retidão.",
        "versiculos": ["2 Tessalonicenses 2:13", "Efésios 4:23-24", "Romanos 6:11"]
    },
    86: {
        "pergunta": "O que é fé em Jesus Cristo?",
        "resposta": "Fé em Jesus Cristo é uma graça salvadora, pela qual o recebemos e nele confiamos, só para a salvação, como ele nos é oferecido no Evangelho.",
        "versiculos": ["Hebreus 10:39", "João 1:12", "Filipenses 3:9"]
    },
    87: {
        "pergunta": "O que é arrependimento para a vida?",
        "resposta": "Arrependimento para a vida é uma graça salvadora, pela qual o pecador, tendo um verdadeiro senso do seu pecado e apreendendo a misericórdia de Deus em Cristo, com dor e ódio do seu pecado, se converte dele para Deus, com pleno propósito de, e esforço para, uma nova obediência.",
        "versiculos": ["Atos 2:37-38", "Joel 2:12-13", "Jeremias 31:18-19"]
    },
    98: {
        "pergunta": "O que é oração?",
        "resposta": "Oração é oferecer a Deus os nossos desejos por coisas conformes à sua vontade, em nome de Cristo, confessando os nossos pecados e reconhecendo com gratidão as suas misericórdias.",
        "versiculos": ["1 João 5:14", "João 16:23", "Daniel 9:4", "Filipenses 4:6"]
    }
}
