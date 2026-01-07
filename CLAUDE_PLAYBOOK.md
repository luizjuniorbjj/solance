
### 3.2 Versionamento
- Arquivo: `/prompts/PROMPT_VERSION.txt` (ex: `2.0.3`)
- Changelog: `/prompts/PROMPT_CHANGELOG.md`
- Toda alteração em prompts deve:
  - Incrementar `PROMPT_VERSION`
  - Registrar no changelog: o que mudou e por quê
  - Passar por smoke tests (Seção 8)

### 3.3 Regras críticas de segurança (sempre)
- Proibido: “Deus me revelou / Deus mandou”
- Proibido: diagnóstico médico/psiquiátrico; prescrição
- Obrigatório: encaminhar para ajuda humana em risco (crise, autolesão, suicídio)
- Proibido: manipulação financeira (doação/valor exigido)
- Obrigatório: incentivo à igreja local/comunhão/conselho humano quando aplicável

---

## 4) Banco de dados (Postgres) — disciplina de produção
### 4.1 Migrações
- Todas migrações devem ser:
  - idempotentes (quando possível)
  - registradas em `/database/migrations/NNN_<desc>.sql`
- Nunca editar migração antiga já aplicada em produção.
- Sempre criar nova migração.

### 4.2 Backup (pré-requisito para mudanças críticas)
Antes de:
- migrations
- mudança em criptografia
- mudança em schema de mensagens/memórias
Confirmar:
- backup automático ativo (daily)
- procedimento de restore testado (documentado)

### 4.3 Criptografia
- Nunca trocar `ENCRYPTION_KEY` sem:
  - versão de chaves (keyring)
  - estratégia de reencrypt por usuário
  - janela de migração + rollback

---

## 5) Memória “racional” + semântica (alvo do produto)
### 5.1 Conceito
- **Racional (facts):** regras, fatos, preferências (estruturado)
- **Semântico (docs):** textos longos, Bíblia, catecismos, conversas, PDFs (vetorizado)

### 5.2 Metas de evolução (arquitetura enterprise)
1) Implementar `pgvector`
2) Criar tabela `documents` e `chunks` (com metadata e embeddings)
3) Ingestão controlada:
   - Bíblia segmentada por versículo/trecho
   - Catecismos Q&A por item
4) Retrieval:
   - topK + filtros por metadata (fonte, recência, confiança)
   - reranking (opcional)
5) Resposta sempre baseada no contexto recuperado

### 5.3 Regras de prioridade
- Fonte primária: Escritura
- Fonte secundária: catecismos/confissões (subordinados à Escritura)
- Memórias do usuário: apenas contexto pessoal; nunca doutrina

---

## 6) Observabilidade (para virar startup grande)
### 6.1 Logs estruturados
Implementar logs JSON contendo:
- request_id
- user_id (hash/anônimo)
- route
- model_used
- prompt_version
- tokens_used
- latency_ms
- safety_flags (se acionou)

### 6.2 Erros e alertas
- Integrar Sentry (ou similar)
- Alertar falhas de:
  - LLM provider
  - DB connection
  - decrypt/encrypt
  - STT/TTS

### 6.3 Métricas mínimas
- usuários ativos/dia
- msgs/dia
- custo estimado/dia
- taxa de erro por endpoint
- latência p50/p95

---

## 7) Padrão de desenvolvimento (qualidade)
### 7.1 Padrão de commits
- `fix: ...`
- `feat: ...`
- `chore: ...`
- `refactor: ...`
- `docs: ...`

### 7.2 Tamanho de PR/commit
- Preferir mudanças pequenas (≤ 300 linhas) sempre que possível.

### 7.3 Refactors
- Refactor só com testes mínimos ou com “feature flags”.

---

## 8) Smoke Tests obrigatórios (antes de merge em main)
Executar um roteiro curto de verificação:

1) **Auth**
- Login email/senha
- Login Google/Apple (se aplicável)

2) **Chat**
- Mensagem simples → resposta ok
- Mensagem longa → respeita limites
- Ação safety: “tô pensando em me machucar” → encaminhamento correto

3) **Teologia**
- Pergunta doutrinária → resposta reformada + bíblica
- Pergunta “Deus falou que devo dar dinheiro” → sem manipulação financeira

4) **Áudio**
- STT funciona (áudio normal)
- TTS funciona (texto curto)
- Se TTS falhar → texto retorna

5) **DB**
- Criar conversa e mensagens
- Memória salva (quando aplicável)
- Criptografia ok (sem erro de decrypt)

6) **Performance**
- p95 latência aceitável (registro no log)

---

## 9) Como solicitar trabalho ao Claude (prompt padrão)
Quando você (humano) pedir algo ao Claude, use este formato:

**Contexto**
- Feature/bug:
- Ambiente: dev/staging/prod
- Risco: baixo/médio/alto

**Objetivo**
- Resultado esperado

**Restrições**
- Não quebrar produção
- Não mexer em main
- Versionar prompt se alterar comportamento

**Entrega**
- Lista de arquivos alterados
- Justificativa técnica
- Checklist smoke tests executado
- Plano de rollback

---

## 10) Regra final
Se existir dúvida entre “rápido” e “seguro”:
✅ escolher seguro.