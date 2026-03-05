import time
import requests

BASE_URL = "https://europe.api.riotgames.com"
PLATFORM_URL = "https://eun1.api.riotgames.com"

_puuid_cache = {}


def _get(url, api_key):
    """Make a GET request with Riot API auth and 429 retry."""
    headers = {"X-Riot-Token": api_key}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 5))
        print(f"Rate limited, waiting {retry_after}s...")
        time.sleep(retry_after)
        resp = requests.get(url, headers=headers)

    if resp.status_code == 403:
        print("ERROR: 403 Forbidden. Your Riot API key may have expired. "
              "Regenerate it at https://developer.riotgames.com/")
        return None

    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {url}")
        return None

    return resp.json()


def get_puuid(game_name, tag_line, api_key):
    """Resolve a Riot ID (gameName#tagLine) to a PUUID. Results are cached."""
    cache_key = f"{game_name}#{tag_line}"
    if cache_key in _puuid_cache:
        return _puuid_cache[cache_key]

    data = _get(
        f"{BASE_URL}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
        api_key,
    )
    if data and "puuid" in data:
        _puuid_cache[cache_key] = data["puuid"]
        return data["puuid"]
    return None


def get_recent_match_ids(puuid, api_key, count=5):
    """Get the most recent match IDs for a player."""
    data = _get(
        f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}",
        api_key,
    )
    return data if isinstance(data, list) else []


def get_match_details(match_id, api_key):
    """Get full match details by match ID."""
    return _get(f"{BASE_URL}/lol/match/v5/matches/{match_id}", api_key)


def get_ranked_entries(puuid, api_key):
    """Get ranked entries for a player by PUUID. Returns list of queue entries."""
    data = _get(
        f"{PLATFORM_URL}/lol/league/v4/entries/by-puuid/{puuid}",
        api_key,
    )
    return data if isinstance(data, list) else []
