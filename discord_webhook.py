import requests

_ddragon_version = None


def _get_ddragon_version():
    """Fetch the latest Data Dragon version for champion icons."""
    global _ddragon_version
    if _ddragon_version:
        return _ddragon_version

    try:
        resp = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
        if resp.status_code == 200:
            versions = resp.json()
            _ddragon_version = versions[0]
            return _ddragon_version
    except Exception as e:
        print(f"Failed to fetch Data Dragon version: {e}")

    _ddragon_version = "14.4.1"  # fallback
    return _ddragon_version


def send_shame_message(webhook_url, player_name, champion, kills, deaths, assists, kda, roast):
    """Send a shame embed to Discord via webhook."""
    version = _get_ddragon_version()
    icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion}.png"

    payload = {
        "embeds": [
            {
                "title": "🚨 SHAME ALERT 🚨",
                "description": roast,
                "color": 0xFF0000,
                "fields": [
                    {"name": "Summoner", "value": player_name, "inline": True},
                    {"name": "Champion", "value": champion, "inline": True},
                    {"name": "KDA", "value": f"{kills}/{deaths}/{assists} ({kda:.2f})", "inline": True},
                ],
                "thumbnail": {"url": icon_url},
                "footer": {"text": "LoL Shamer Bot \u2022 git gud or get shamed"},
            }
        ]
    }

    try:
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code in (200, 204):
            return True
        print(f"Discord webhook error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Discord webhook request failed: {e}")

    return False


def send_demotion_message(webhook_url, player_name, old_rank, new_rank, queue_name, roast):
    """Send a demotion shame embed to Discord via webhook."""
    payload = {
        "embeds": [
            {
                "title": "\u2b07\ufe0f DEMOTION ALERT \u2b07\ufe0f",
                "description": roast,
                "color": 0x8B0000,
                "fields": [
                    {"name": "Summoner", "value": player_name, "inline": True},
                    {"name": "Queue", "value": queue_name, "inline": True},
                    {"name": "Rank", "value": f"~~{old_rank}~~ \u2192 {new_rank}", "inline": True},
                ],
                "footer": {"text": "LoL Shamer Bot \u2022 git gud or get shamed"},
            }
        ]
    }

    try:
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code in (200, 204):
            return True
        print(f"Discord webhook error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Discord webhook request failed: {e}")

    return False
