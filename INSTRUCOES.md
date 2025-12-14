# SOLACE - Instruções para Desenvolvimento

## O QUE É
App de consolo bíblico com IA. Oferece apoio emocional baseado na Escritura.

## STACK
- Mobile: React Native + Expo + TypeScript
- Backend: FastAPI + Python + Claude API

---

## PASSO 1: CRIAR PROJETO EXPO

```bash
npx create-expo-app solace-mobile --template blank-typescript
cd solace-mobile
npx expo install expo-router expo-font
```

---

## PASSO 2: CORES

```typescript
export const Colors = {
  gold: '#b8860b',
  goldLight: '#d4a855', 
  goldDark: '#8b6914',
  goldBg: '#faf6ed',
  bgPrimary: '#fdfcfa',
  bgSecondary: '#f5f3ef',
  bgCard: '#ffffff',
  textDark: '#1a1a1a',
  textBody: '#3d3d3d',
  textMuted: '#6b6b6b',
  border: '#e5e0d5',
  success: '#2e7d32',
};
```

---

## PASSO 3: TELAS

### Welcome
- Logo "S" dourado em círculo
- Título "SOLACE"
- Versículo Mateus 11:28
- Botão "Começar"

### Chat
- Header: avatar + "Solace Online"
- Mensagens (user direita, AI esquerda)
- Input + botão enviar

### Devocional
- Versículo do dia
- Meditação
- Oração

---

## PASSO 4: BACKEND

```bash
cd backend
pip install -r requirements.txt
# Edite backend.py e cole sua ANTHROPIC_API_KEY
python backend.py
```

---

## COMANDO PARA CLAUDE NO VS CODE

```
Crie um app React Native + Expo idêntico ao PROTOTIPO.html.
Use as cores do INSTRUCOES.md.
Comece pela tela Welcome.
```
