# services/links.py
import requests
from urllib.parse import quote

ITUNES_SEARCH = "https://itunes.apple.com/search"
ODESLI_API = "https://api.song.link/v1-alpha.1/links?url="

def itunes_find_track_url(session: requests.Session, title: str, artist: str) -> str | None:
    term = f"{title} {artist}".strip()
    params = {
        "term": term,
        "media": "music",
        "entity": "song",
        "limit": 1,
        "country": "US",
    }
    r = session.get(ITUNES_SEARCH, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    if not results:
        return None
    return results[0].get("trackViewUrl")

def odesli_get_spotify_url(session: requests.Session, source_url: str) -> str | None:
    r = session.get(ODESLI_API + quote(source_url, safe=""), timeout=20)
    r.raise_for_status()
    data = r.json()
    links = data.get("linksByPlatform", {})
    sp = links.get("spotify")
    if sp and isinstance(sp, dict):
        return sp.get("url")
    return None

def spotify_search_url(title: str, artist: str) -> str:
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"

def best_spotify_link(session: requests.Session, title: str, artist: str) -> tuple[str, str]:
    try:
        it_url = itunes_find_track_url(session, title, artist)
        if it_url:
            sp = odesli_get_spotify_url(session, it_url)
            if sp:
                return sp, "odesli"
    except Exception:
        pass
    return spotify_search_url(title, artist), "search_fallback"
