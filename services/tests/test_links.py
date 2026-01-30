import requests
from services.links import itunes_find_track_url, odesli_get_spotify_url, best_spotify_link, spotify_search_url

class FakeResp:
    def __init__(self, json_data=None):
        self._json = json_data or {}
    def raise_for_status(self):
        return None
    def json(self):
        return self._json

def test_itunes_find_track_url_returns_track_url():
    session = requests.Session()

    def fake_get(url, params=None, timeout=None):
        return FakeResp({
            "results": [{"trackViewUrl": "https://music.apple.com/us/track/x"}]
        })

    session.get = fake_get  # monkeypatch simples

    url = itunes_find_track_url(session, "Hello", "Adele")
    assert url == "https://music.apple.com/us/track/x"

def test_odesli_get_spotify_url_returns_spotify():
    session = requests.Session()

    def fake_get(url, timeout=None):
        return FakeResp({
            "linksByPlatform": {"spotify": {"url": "https://open.spotify.com/track/abc"}}
        })

    session.get = fake_get

    sp = odesli_get_spotify_url(session, "https://music.apple.com/us/track/x")
    assert sp == "https://open.spotify.com/track/abc"

def test_best_spotify_link_fallback_when_no_itunes_results():
    session = requests.Session()

    def fake_get(url, params=None, timeout=None):
        # iTunes sem resultados
        return FakeResp({"results": []})

    session.get = fake_get

    sp, method = best_spotify_link(session, "Unknown Song", "Unknown Artist")
    assert method == "search_fallback"
    assert sp == spotify_search_url("Unknown Song", "Unknown Artist")

def test_best_spotify_link_fallback_when_odesli_has_no_spotify():
    session = requests.Session()

    # vamos simular duas chamadas:
    # 1) iTunes retorna trackViewUrl
    # 2) Odesli retorna sem spotify
    calls = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        calls["n"] += 1
        if "itunes.apple.com" in url:
            return FakeResp({"results": [{"trackViewUrl": "https://music.apple.com/us/track/x"}]})
        else:
            return FakeResp({"linksByPlatform": {}})

    session.get = fake_get

    sp, method = best_spotify_link(session, "Song A", "Artist A")
    assert method == "search_fallback"
    assert sp.startswith("https://open.spotify.com/search/")
