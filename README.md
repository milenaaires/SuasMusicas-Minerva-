# Suas músicas da época 🎧

Descubra quais músicas estavam no topo das paradas nos EUA em um mês/ano específico (Billboard Hot 100) e abra cada faixa direto no Spotify.

- **App na nuvem:** https://suasmusicas.streamlit.app/
- **Repositório:** https://github.com/milenaaires/SuasMusicas-Minerva-

---

## O que este app faz
- Você escolhe **ano**, **mês** e uma **semana** daquele mês (o Billboard é **semanal**).
- O app busca o ranking **Billboard Hot 100** da semana escolhida.
- Para cada música, gera um link para ouvir no **Spotify**.
- Permite **baixar um CSV** com os resultados.

---

## Como o link do Spotify é gerado

1. **Billboard (scraping)** → pega lista de músicas (rank/título/artista)
2. **iTunes Search API (JSON)** → encontra um link público da faixa
3. **Odesli/Songlink (JSON)** → converte o link e retorna a URL do Spotify
4. **Fallback** → se não encontrar, gera um link de **busca do Spotify** para a música

Isso garante que o usuário sempre terá um link para abrir.

---

## Arquitetura do projeto
- `app.py` → Interface Streamlit (UI, filtros, cards, CSV)
- `services/billboard.py` → Busca e extração do Hot 100 do Billboard
- `services/links.py` → iTunes + Odesli + fallback para gerar link do Spotify
- `services/tests/` → testes unitários (offline com mocks/fixtures)

---

## Performance
- Cache de resultados com `st.cache_data`
- Geração de links em paralelo (ThreadPool)
- Barra de progresso ao gerar os links

---

## Rodar localmente

### 1) Criar e ativar ambiente virtual
**Windows (PowerShell):**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1

2) Instalar dependências
pip install -r requirements.txt

3) Rodar o app
streamlit run app.py
```
### 2) Instalar dependências
```bash
pip install -r requirements.txt
```
### 3) Rodar o app
```bash
streamlit run app.py
```
Abra no navegador: http://localhost:8501
---
## Testes
### Rodar testes
```bash
pytest -q
```
### Rodar cobertura
```bash
pytest --cov=services --cov-report=term-missing
```
Os testes são offline: usam mocks e fixtures, sem depender de internet.

## CI/CD e Deploy

- CI com GitHub Actions: roda pytest e coverage a cada push/PR

- Deploy automático no Streamlit Cloud: atualiza a cada push na branch principal

```bash
::contentReference[oaicite:0]{index=0}
```

