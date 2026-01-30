import pathlib
from services.billboard import fetch_hot100

def test_fetch_hot100_parses_titles_and_artists(mocker):
    # carrega html de fixture
    html_path = pathlib.Path(__file__).parent / "fixtures" / "billboard_sample.html"
    html = html_path.read_text(encoding="utf-8")

    # mock do requests.get
    fake_response = mocker.Mock()
    fake_response.text = html
    fake_response.raise_for_status = mocker.Mock()

    mock_get = mocker.patch("services.billboard.requests.get", return_value=fake_response)

    songs = fetch_hot100("2015-01-03", limit=10)

    assert mock_get.called
    assert len(songs) == 2
    assert songs[0]["rank"] == 1
    assert songs[0]["title"] == "Song A"
    assert songs[0]["artist"] == "Artist A"
    assert songs[1]["rank"] == 2
    assert songs[1]["title"] == "Song B"
    assert songs[1]["artist"] == "Artist B"
