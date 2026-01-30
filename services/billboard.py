# services/billboard.py
import requests
from bs4 import BeautifulSoup

BILLBOARD_URL = "https://www.billboard.com/charts/hot-100/{date_str}/"

def fetch_hot100(date_str: str, limit: int = 10):
    """
    date_str: 'YYYY-MM-DD'
    returns: list of dicts: {rank, title, artist}
    """
    url = BILLBOARD_URL.format(date_str=date_str)
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Billboard muda classes às vezes; este seletor costuma funcionar bem:
    # títulos geralmente aparecem em h3 com id 'title-of-a-story' dentro das linhas do chart
    rows = soup.select("li.o-chart-results-list__item > h3#title-of-a-story")
    # fallback (mais amplo)
    if not rows:
        rows = soup.select("h3#title-of-a-story")

    titles = [x.get_text(strip=True) for x in rows if x.get_text(strip=True)]
    # artistas geralmente aparecem em span logo abaixo do título, com classes variáveis
    # vamos pegar blocos de item e extrair título+artista juntos:
    entries = []
    chart_items = soup.select("li.o-chart-results-list__item > h3#title-of-a-story")
    if chart_items:
        # melhor abordagem: subir pro container do item
        for h3 in chart_items[:limit]:
            title = h3.get_text(strip=True)
            container = h3.find_parent()
            artist = ""
            # tenta achar o primeiro span “não vazio” depois do título
            for sp in container.find_all("span"):
                txt = sp.get_text(strip=True)
                if txt and txt.lower() not in ("-",):
                    # heurística: artistas não são "NEW", "RE-ENTRY", etc.
                    if len(txt) >= 2 and txt.upper() not in ("NEW", "RE-ENTRY"):
                        artist = txt
                        break
            entries.append({"title": title, "artist": artist})
    else:
        # fallback bem simples só com títulos
        for t in titles[:limit]:
            entries.append({"title": t, "artist": ""})

    # adiciona rank
    for i, e in enumerate(entries, start=1):
        e["rank"] = i

    return entries
