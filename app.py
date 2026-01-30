import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta, SA
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.billboard import fetch_hot100
from services.links import best_spotify_link

# ---------- Config ----------
st.set_page_config(
    page_title="Top músicas do mês",
    page_icon="🎧",
    layout="wide",
)

st.markdown(
    """
    <style>
      :root{
        --bg: #0b0f0c;
        --panel: #111814;
        --card: #121a15;
        --card2: #0f1612;
        --text: #e8f1eb;
        --muted: rgba(232,241,235,0.72);
        --border: rgba(232,241,235,0.10);
        --green: #1DB954;
        --green2:#1ed760;
      }

      /* fundo */
      .stApp { background: radial-gradient(1200px 800px at 20% 0%, rgba(29,185,84,0.10), transparent 60%),
                         radial-gradient(900px 600px at 90% 10%, rgba(30,215,96,0.08), transparent 55%),
                         var(--bg) !important; color: var(--text) !important; }

      /* sidebar */
      section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, rgba(17,24,20,0.95), rgba(10,14,11,0.95)) !important;
        border-right: 1px solid var(--border);
      }

      /* título e texto */
      .hero { padding: 0.65rem 0 0.25rem 0; }
      .subtitle { color: var(--muted); font-size: 1.05rem; margin-top: -0.35rem; }

      /* cards */
      .card {
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px 16px;
        margin-bottom: 12px;
        background: linear-gradient(180deg, rgba(18,26,21,0.92), rgba(15,22,18,0.92));
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      }

      .rank { font-weight: 800; font-size: 1.05rem; color: rgba(232,241,235,0.85); }
      .song { font-weight: 800; font-size: 1.10rem; }
      .artist { color: var(--muted); margin-top: 4px; }

      /* botão estilo spotify */
      .btnlink a {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid rgba(29,185,84,0.25);
        background: rgba(29,185,84,0.12);
        color: var(--text) !important;
        text-decoration: none !important;
        font-weight: 700;
      }
      .btnlink a:hover {
        border-color: rgba(30,215,96,0.45);
        background: rgba(30,215,96,0.18);
        transform: translateY(-1px);
      }

      .muted { color: var(--muted); font-size: 0.92rem; }

      /* “Primary button” do Streamlit (Buscar músicas) */
      .stButton > button[kind="primary"]{
        background: linear-gradient(90deg, var(--green), var(--green2)) !important;
        color: #06110a !important;
        border: 0 !important;
        border-radius: 999px !important;
        font-weight: 800 !important;
        padding: 0.8rem 1.0rem !important;
        box-shadow: 0 12px 30px rgba(29,185,84,0.20) !important;
      }
      .stButton > button[kind="primary"]:hover{
        filter: brightness(1.05);
        transform: translateY(-1px);
      }

      /* inputs */
      .stSelectbox, .stNumberInput, .stTextInput{
        border-radius: 14px;
      }

      /* dataframe mais clean */
      div[data-testid="stDataFrame"]{
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
      }

      /* esconder “made with streamlit” e afins se quiser */
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Caches ----------
@st.cache_data(ttl=60 * 60 * 12)  # 12h
def cached_billboard(date_str: str, limit: int):
    return fetch_hot100(date_str, limit=limit)

@st.cache_data(ttl=60 * 60 * 24 * 30)  # 30 dias
def cached_link(title: str, artist: str):
    # cache “puro” por música; a sessão fica fora do cache
    # (vamos chamar best_spotify_link dentro de um wrapper)
    return {"title": title, "artist": artist}

def build_weeks(year: int, month: int):
    first_day = date(year, month, 1)
    next_month = first_day + relativedelta(months=1)
    saturdays = []
    d = first_day + relativedelta(weekday=SA(1))
    while d < next_month:
        saturdays.append(d)
        d = d + relativedelta(weeks=1)
    return saturdays

# ---------- Sidebar (UX melhor) ----------
with st.sidebar:
    st.header("⚙️ Escolha a época")
    year = st.number_input("Ano", min_value=1958, max_value=2100, value=2015, step=1)
    month = st.selectbox("Mês", list(range(1, 13)), index=0)

    weeks = build_weeks(int(year), int(month))
    week_date = st.selectbox(
        "Semana (Billboard é semanal)",
        weeks,
        format_func=lambda x: x.strftime("%Y-%m-%d"),
    )

    st.divider()
    top_n = st.selectbox("Quantidade", [10, 20, 50, 100], index=0)
    speed_mode = st.toggle("🚀 Modo rápido (menos verificações)", value=True)
    st.caption("Dica: o modo rápido tende a usar mais links de busca do Spotify e fica mais ágil.")

# ---------- Header ----------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.title("🎧 Suas músicas da época")
st.markdown(
    '<div class="subtitle">Escolha um mês e descubra o que estava no topo das paradas nos EUA. '
    'Abra cada faixa direto no Spotify.</div>',
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Action ----------
date_str = week_date.strftime("%Y-%m-%d")

colA, colB = st.columns([1, 2])
with colA:
    go = st.button("Buscar músicas", type="primary", use_container_width=True)
with colB:
    st.markdown(
        f'<div class="muted">📅 Semana selecionada: <b>{date_str}</b> '
        f'&nbsp;•&nbsp; Fonte: Billboard Hot 100</div>',
        unsafe_allow_html=True,
    )

if go:
    # 1) Billboard
    with st.spinner("Buscando ranking do Billboard..."):
        songs = cached_billboard(date_str, int(top_n))

    if not songs:
        st.error("Não consegui extrair a lista do Billboard para essa semana.")
        st.stop()

    # 2) Links (paralelo)
    # session reutilizável
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    session.headers.update(headers)

    # modo rápido: se quiser, a gente evita algumas chamadas pesadas:
    # aqui fazemos normalmente, mas você pode reduzir workers ou quantidade.
    max_workers = 18 if speed_mode else 10

    def resolve_one(s):
        # cache key “lógica” (título/artista) – só pra estabilizar
        _ = cached_link(s["title"], s["artist"])
        sp_url, method = best_spotify_link(session, s["title"], s["artist"])
        return {
            "Rank": s["rank"],
            "Música": s["title"],
            "Artista": s["artist"],
            "Spotify": sp_url,
            "Método": method,
        }

    with st.spinner("Gerando links do Spotify..."):
        rows = []
        progress = st.progress(0)
        done = 0
        total = len(songs)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(resolve_one, s) for s in songs]
            for f in as_completed(futures):
                rows.append(f.result())
                done += 1
                progress.progress(done / total)

        progress.empty()

    df = pd.DataFrame(rows).sort_values("Rank")

    # ---------- Results ----------
    st.subheader("Resultado")
    st.caption("Se algum link abrir em busca do Spotify, é o fallback quando a conversão automática não encontra a faixa.")

    # Cards (visual)
    for _, r in df.iterrows():
        st.markdown(
            f"""
            <div class="card">
              <div class="rank">#{int(r['Rank'])}</div>
              <div class="song">{r['Música']}</div>
              <div class="artist">{r['Artista']}</div>
              <div style="margin-top:10px" class="btnlink">
                <a href="{r['Spotify']}" target="_blank" rel="noopener noreferrer">🟢 Ouvir no Spotify</a>
                <span class="muted" style="margin-left:10px">({r['Método']})</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Tabela + download
    st.subheader("Tabela (para copiar/baixar)")
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Spotify": st.column_config.LinkColumn("Spotify", display_text="Abrir no Spotify"),
        },
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name=f"hot100_{date_str}.csv",
        mime="text/csv",
        use_container_width=True,
    )
