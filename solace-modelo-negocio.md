# SOLACE — Modelo de Negócio

## Resumo Executivo

| Item | Valor |
|------|-------|
| **Preço da assinatura** | $5.99/mês |
| **Trial gratuito** | 7 dias (até 20 mensagens) |
| **Modelo de IA** | Claude Sonnet 4 (até 160 msg) → Haiku 3.5 (depois) |
| **Custo médio por usuário** | ~$1.50/mês |
| **Taxa gateway** | 5% (Stripe) / 15% (Google Play/App Store) |
| **Margem real por usuário** | ~$3.70 (Stripe) / ~$3.19 (Lojas) |
| **Break-even** | ~10 assinantes |
| **Limite soft** | 160 msg rápidas/mês (depois fica mais lento) |

---

## Custos da API Claude Sonnet 4

| Tipo | Preço |
|------|-------|
| Input | $3.00 / 1 milhão tokens |
| Output | $15.00 / 1 milhão tokens |

---

## Custo por Mensagem

### Conversa típica na Solace

| Componente | Tokens |
|------------|--------|
| System prompt (fixo) | ~800 |
| Mensagem do usuário | ~100 |
| Histórico (5 turnos) | ~1.500 |
| **Total Input** | **~2.400** |
| Resposta do Claude | ~400 |
| **Total Output** | **~400** |

### Cálculo

```
Input:  2.400 tokens × $3.00/1M  = $0.0072
Output:   400 tokens × $15.00/1M = $0.0060
───────────────────────────────────────────
CUSTO POR MENSAGEM: $0.013 (~1.3 centavos)
```

---

## Capacidade por Assinatura

```
$5.99 ÷ $0.013 = ~460 mensagens/mês
```

O usuário pode enviar até **460 mensagens por mês** antes de zerar a margem.

---

## Gateways de Pagamento

### Opções por Plataforma

| Plataforma | Gateway | Taxa | Obrigatório? |
|------------|---------|------|--------------|
| **Android (Play Store)** | Google Play Billing | 15%* | Sim |
| **iOS (App Store)** | Apple In-App Purchase | 15%* | Sim |
| **Web / PWA** | Stripe | ~5% | Não |

*\*15% para desenvolvedores no Small Business Program (faturamento < $1M/ano)*

### Vantagens de Cada Gateway

| Aspecto | Stripe | Google Play / App Store |
|---------|--------|-------------------------|
| **Taxa** | ~5% | 15% |
| **Experiência do usuário** | Digitar cartão | 1 clique (já logado) |
| **Confiança** | Média | Alta |
| **Gestão de assinatura** | Você implementa | Automático |
| **Reembolsos** | Você gerencia | Eles gerenciam |
| **Impostos internacionais** | Você calcula | Eles calculam |
| **Disputas/chargebacks** | Você resolve | Eles resolvem |

### Recomendação

Usar **todos os 3 gateways**:
- Apps nas lojas usam billing nativo (obrigatório)
- Oferecer opção web com Stripe (margem maior)
- Usuários que pagam pelo site = +10% de margem

---

## Cenários de Uso por Plataforma

### Via Stripe (Web) - Taxa 5%

| Perfil | Msg/mês | Custo API | Taxa (5%) | Margem Real |
|--------|---------|-----------|-----------|-------------|
| Leve | 30 | $0.39 | $0.30 | **$5.30** |
| Médio | 100 | $1.30 | $0.30 | **$4.39** |
| Intenso | 200 | $2.60 | $0.30 | **$3.09** |
| Muito intenso | 300 | $3.90 | $0.30 | **$1.79** |

### Via Google Play / App Store - Taxa 15%

| Perfil | Msg/mês | Custo API | Taxa (15%) | Margem Real |
|--------|---------|-----------|------------|-------------|
| Leve | 30 | $0.39 | $0.90 | **$4.70** |
| Médio | 100 | $1.30 | $0.90 | **$3.79** |
| Intenso | 200 | $2.60 | $0.90 | **$2.49** |
| Muito intenso | 300 | $3.90 | $0.90 | **$1.19** |

**Média esperada (100 msg/mês):**
- Stripe: **$4.39** margem (73%)
- Lojas: **$3.79** margem (63%)

---

## Sistema de Throttle (Limite Suave)

### Regra Principal

| Mensagens/mês | Modelo | Experiência |
|---------------|--------|-------------|
| 1 - 160 | Sonnet 4 | ⚡ Resposta rápida |
| 161+ | Haiku 3.5 + delay | 🐢 Resposta mais lenta |

### Por que 160?

```
160 msg × $0.013 = $2.08 custo Sonnet
$5.99 - $2.08 = $3.91 margem (65%)
```

- ~5 mensagens/dia no modo rápido
- Margem saudável garantida
- Usuário médio nunca atinge o limite

### Implementação

```python
if user.messages_this_month <= 160:
    model = "claude-sonnet-4-20250514"
    # Resposta imediata
else:
    model = "claude-haiku-3-5-20250514"
    await asyncio.sleep(3)  # Delay de 3 segundos
```

### Vantagens do Throttle

✅ **Nunca bloqueia** — usuário sempre consegue usar  
✅ **Sem "compre créditos"** — péssimo para app espiritual  
✅ **Invisível** — usuário não sabe que mudou de modelo  
✅ **Sustentável** — quem usa pouco subsidia quem usa muito  
✅ **Sem frustração** — experiência suave, só mais lenta

---

## Custos de Desenvolvimento e Operação

### Investimento Inicial

| Item | Custo |
|------|-------|
| Desenvolvimento completo (App iOS/Android + Backend) | $38,000 |

### Custos Fixos Mensais

| Item | Custo |
|------|-------|
| Equipe (desenvolvimento + manutenção) | $12,000 |
| Provedor IA (Claude API) | $1,500 |
| Servidores e infraestrutura | $500 |
| **Total Mensal** | **$14,000/mês** |

### Break-even Operacional

```
$14,000 / $5.99 = 2,337 assinantes para cobrir custos fixos
Meta: alcançar em 6-8 meses de operação
```

---

## Projeção de Lucro (com custos reais)

### Cenário Realista: Mix de Plataformas (70% Lojas / 30% Web)

*Custo fixo mensal: $14,000 | Taxa média: 12%*

| Assinantes | Receita | Custo API | Taxa (12%) | Custo Fixo | **Lucro** |
|------------|---------|-----------|------------|------------|-----------|
| 1.000 | $5,990 | $1,500 | $719 | $14,000 | **-$10,229** |
| 2,500 | $14,975 | $3,750 | $1,797 | $14,000 | **-$4,572** |
| 3,500 | $20,965 | $5,250 | $2,516 | $14,000 | **-$801** |
| 5,000 | $29,950 | $7,500 | $3,594 | $14,000 | **$4,856** |
| 10,000 | $59,900 | $15,000 | $7,188 | $14,000 | **$23,712** |
| 50,000 | $299,500 | $75,000 | $35,940 | $14,000 | **$174,560** |
| 100,000 | $599,000 | $150,000 | $71,880 | $14,000 | **$363,120** |
| 1,000,000 | $5,990,000 | $1,500,000 | $718,800 | $14,000 | **$3,757,200** |

### Ponto de Equilíbrio

```
Break-even = ~3,800 assinantes
Receita: $22,762/mês
Custos: $14,000 (fixo) + $5,700 (API) + $2,731 (gateway) = $22,431/mês
```

### Projeção para 1 Milhão de Usuários

| Métrica | Valor Mensal | Valor Anual |
|---------|--------------|-------------|
| Receita | $5,990,000 | $71,880,000 |
| Custo API | $1,500,000 | $18,000,000 |
| Taxa Gateway (12%) | $718,800 | $8,625,600 |
| Custo Fixo | $14,000 | $168,000 |
| **Lucro** | **$3,757,200** | **$45,086,400** |
| **Margem** | **62.7%** | **62.7%** |

**Conclusão:** Com os custos reais de operação, o break-even é ~3,800 assinantes. A partir daí, cada novo assinante gera ~$3.79 de lucro.

---

## Estratégia de Monetização

### Trial Gratuito (7 dias)

| Aspecto | Detalhe |
|---------|---------|
| **Duração** | 7 dias |
| **Limite de mensagens** | 20 mensagens no total |
| **Modelo usado** | Haiku 3.5 (custo mínimo) |
| **Custo máximo do trial** | ~$0.05 por usuário |
| **Conversão esperada** | 10-15% para assinatura |

**Regras do Trial:**
- Não requer cartão de crédito para começar
- Contador de mensagens visível ("Você usou 5 de 20 mensagens")
- Ao acabar trial: tela de conversão com benefícios do plano pago
- Usuário pode assinar a qualquer momento durante o trial

**Custo de Aquisição:**
```
Se 100 pessoas fazem trial → custo: $5.00
Se 12 convertem (12%) → receita mês 1: $71.88
CAC efetivo: $5.00 ÷ 12 = $0.42 por assinante
```

---

### Plano Único: $5.99/mês

**Inclui:**
- Chat ilimitado com Solace (até ~460 msg/mês na prática)
- Devocional diário personalizado
- Versículos salvos
- Memória espiritual (histórico)
- Sem anúncios
- Modelo Sonnet 4 (primeiras 160 msg)

### Opção Futura: Plano Anual

- $59.99/ano (desconto de ~17%)
- Equivale a $5.00/mês
- Melhora retenção e fluxo de caixa
- **Reduz churn significativamente**

---

## Por que Sonnet 4 e não Haiku?

| Aspecto | Haiku 3.5 | Sonnet 4 |
|---------|-----------|----------|
| Custo | 12x mais barato | Referência |
| Nuance teológica | ⚠️ Limitada | ✅ Excelente |
| Tom pastoral | ⚠️ Inconsistente | ✅ Consistente |
| Situações delicadas | ⚠️ Pode falhar | ✅ Confiável |
| **Recomendação** | MVP/testes | **Produção** |

Para um app de **consolo espiritual**, a qualidade das respostas é crítica. Sonnet 4 vale o custo extra.

---

## Estratégia de Retenção (Reduzir Churn)

### Métricas de Churn

| Cenário | Churn Mensal | Impacto |
|---------|--------------|---------|
| Ruim | 15%+ | Perde metade dos usuários em 4 meses |
| Médio | 8-10% | Estabiliza com aquisição constante |
| Bom | 5% | Crescimento saudável |
| Excelente | <3% | Crescimento exponencial |

**Meta: manter churn abaixo de 8%**

---

### Táticas de Retenção

#### 1. Engajamento Diário
| Ação | Implementação |
|------|---------------|
| **Devocional diário** | Push notification às 7h com versículo do dia |
| **Streak de leitura** | "7 dias consecutivos na Palavra" - gamificação leve |
| **Lembretes gentis** | "Sentimos sua falta" após 3 dias sem uso |

#### 2. Valor Acumulado (Lock-in positivo)
| Ação | Implementação |
|------|---------------|
| **Histórico de conversas** | Usuário acumula "memória espiritual" |
| **Versículos salvos** | Coleção pessoal de favoritos |
| **Jornada espiritual** | Visualização do progresso ao longo do tempo |
| **Insights pessoais** | "Você buscou conforto sobre ansiedade 5x este mês" |

#### 3. Prevenção de Cancelamento
| Gatilho | Ação |
|---------|------|
| **Usuário clica em cancelar** | Oferecer 1 mês grátis para ficar |
| **Não usa há 7 dias** | Email personalizado com devocional |
| **Usou muito no início, parou** | "Vimos que você gostou de conversar sobre X" |

#### 4. Plano Anual (Maior Retenção)
```
Mensal: $5.99/mês → Churn médio 8%/mês
Anual:  $59.99/ano → Churn efetivo ~2%/mês

Desconto de 17% + compromisso de 12 meses = retenção muito maior
```

---

### Projeção com Churn

| Mês | Novos | Churn (8%) | Ativos | Receita |
|-----|-------|------------|--------|---------|
| 1 | 20 | 0 | 20 | $120 |
| 2 | 15 | 2 | 33 | $197 |
| 3 | 15 | 3 | 45 | $269 |
| 6 | 12 | 6 | 72 | $431 |
| 12 | 10 | 8 | 95 | $569 |

**Com retenção boa (5% churn):**

| Mês | Novos | Churn (5%) | Ativos | Receita |
|-----|-------|------------|--------|---------|
| 1 | 20 | 0 | 20 | $120 |
| 2 | 15 | 1 | 34 | $204 |
| 3 | 15 | 2 | 47 | $281 |
| 6 | 12 | 4 | 85 | $509 |
| 12 | 10 | 6 | 138 | $826 |

**Diferença em 12 meses: +$257/mês (45% mais receita)**

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Usuário usa demais | Sistema de throttle: após 160 msg, muda para Haiku + delay |
| Poucos assinantes | Break-even baixo (10). Marketing orgânico em igrejas |
| Claude aumenta preços | Margem de 62% absorve aumentos moderados |
| Concorrência | Diferencial teológico reformado é nicho específico |
| Churn alto | Estratégia de retenção + plano anual + valor acumulado |
| Trial abusado | Limite de 20 msg + modelo Haiku = custo mínimo |

---

## Conclusão

✅ **$5.99/mês é viável e lucrativo**

### Investimento Necessário

| Item | Valor |
|------|-------|
| Desenvolvimento inicial | $38,000 |
| Operação 12 meses ($14K/mês) | $168,000 |
| Marketing e reserva | $18,000 |
| **Total** | **$200,000** |

### Métricas-Chave

| Métrica | Valor |
|---------|-------|
| Break-even operacional | ~3,800 assinantes |
| Margem por assinante (após break-even) | ~$3.79 |
| Meta 1M usuários - Lucro anual | $45M+ |
| Runway com investimento | 12+ meses |

### Resumo

- Trial gratuito reduz fricção de entrada
- Margem real: 62-73% dependendo da plataforma
- Break-even operacional: ~3,800 assinantes (meta 6-8 meses)
- Estratégia de retenção pode aumentar receita em 45%
- **Funciona em todas as plataformas** (Android, iOS, Web)

---

*Documento atualizado em Dezembro/2025*
*Projeto Solace — Seu refúgio quando você precisar*
