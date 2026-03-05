import json
import os

from riot_api import get_puuid, get_recent_match_ids, get_match_details, get_ranked_entries
from discord_webhook import send_shame_message, send_demotion_message
from roast_generator import generate_roast, generate_demotion_roast

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
FRIENDS_PATH = os.path.join(SCRIPT_DIR, "friends.json")
PROCESSED_PATH = os.path.join(SCRIPT_DIR, "processed_matches.json")
RANKS_PATH = os.path.join(SCRIPT_DIR, "ranks.json")
MAX_STORED_MATCHES = 50
MIN_GAME_DURATION_SECONDS = 300  # skip remakes

TIER_ORDER = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
DIVISION_ORDER = ["IV", "III", "II", "I"]

QUEUE_NAMES = {
    "RANKED_SOLO_5x5": "Solo/Duo",
    "RANKED_FLEX_SR": "Flex",
}


def load_config():
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    # Env vars override config.json (used in GitHub Actions)
    config["riot_api_key"] = os.environ.get("RIOT_API_KEY", config.get("riot_api_key", ""))
    config["discord_webhook_url"] = os.environ.get("DISCORD_WEBHOOK_URL", config.get("discord_webhook_url", ""))
    config["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", config.get("gemini_api_key", ""))
    # Load friends from friends.json (committed to repo, no secrets)
    if os.path.exists(FRIENDS_PATH):
        with open(FRIENDS_PATH) as f:
            config["friends"] = json.load(f)
    return config


def load_processed():
    if os.path.exists(PROCESSED_PATH):
        with open(PROCESSED_PATH) as f:
            return json.load(f)
    return {}


def save_processed(data):
    with open(PROCESSED_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_ranks():
    if os.path.exists(RANKS_PATH):
        with open(RANKS_PATH) as f:
            return json.load(f)
    return {}


def save_ranks(data):
    with open(RANKS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def rank_value(tier, division):
    t = TIER_ORDER.index(tier) if tier in TIER_ORDER else -1
    d = DIVISION_ORDER.index(division) if division in DIVISION_ORDER else 0
    return t * 4 + d


def format_rank(tier, division):
    return f"{tier.capitalize()} {division}"


def check_demotions(puuid, display_name, api_key, webhook_url, gemini_key, stored_ranks):
    entries = get_ranked_entries(puuid, api_key)
    if not entries:
        return

    if puuid not in stored_ranks:
        stored_ranks[puuid] = {}

    for entry in entries:
        queue = entry.get("queueType", "")
        tier = entry.get("tier", "")
        division = entry.get("rank", "")
        if not tier or not division:
            continue

        queue_name = QUEUE_NAMES.get(queue, queue)
        current_rank = format_rank(tier, division)
        current_value = rank_value(tier, division)

        if queue in stored_ranks[puuid]:
            prev = stored_ranks[puuid][queue]
            prev_value = rank_value(prev["tier"], prev["division"])
            if current_value < prev_value:
                old_rank = format_rank(prev["tier"], prev["division"])
                game_name = display_name.split("#")[0]
                roast = generate_demotion_roast(game_name, old_rank, current_rank, queue_name, gemini_key)
                sent = send_demotion_message(webhook_url, display_name, old_rank, current_rank, queue_name, roast)
                status = "SENT" if sent else "FAILED"
                print(f"[DEMOTION {status}] {display_name} - {queue_name}: {old_rank} -> {current_rank}")

        stored_ranks[puuid][queue] = {"tier": tier, "division": division}


def extract_player_stats(match_data, puuid):
    for participant in match_data.get("info", {}).get("participants", []):
        if participant.get("puuid") == puuid:
            return {
                "kills": participant["kills"],
                "deaths": participant["deaths"],
                "assists": participant["assists"],
                "championName": participant["championName"],
                "win": participant["win"],
            }
    return None


def calculate_kda(kills, deaths, assists):
    return (kills + assists) / max(deaths, 1)


def main():
    config = load_config()
    processed = load_processed()
    stored_ranks = load_ranks()

    api_key = config["riot_api_key"]
    webhook_url = config["discord_webhook_url"]
    gemini_key = config["gemini_api_key"]
    kda_threshold = config.get("kda_threshold", 1.5)
    match_count = config.get("match_count", 5)

    # Resolve all friends' Riot IDs to PUUIDs
    friends = {}
    for riot_id in config["friends"]:
        parts = riot_id.split("#", 1)
        if len(parts) != 2:
            print(f"Invalid Riot ID format: {riot_id}")
            continue
        game_name, tag_line = parts
        puuid = get_puuid(game_name, tag_line, api_key)
        if puuid:
            friends[puuid] = riot_id
            if puuid not in processed:
                processed[puuid] = []
            print(f"Resolved {riot_id} -> {puuid[:8]}...")
        else:
            print(f"Failed to resolve {riot_id}")

    if not friends:
        print("No friends resolved. Check your config and API key.")
        return

    # Check matches
    for puuid, display_name in friends.items():
        match_ids = get_recent_match_ids(puuid, api_key, match_count)
        new_ids = [m for m in match_ids if m not in processed.get(puuid, [])]

        for match_id in new_ids:
            match_data = get_match_details(match_id, api_key)
            if not match_data:
                continue

            if match_data.get("info", {}).get("gameDuration", 0) < MIN_GAME_DURATION_SECONDS:
                processed[puuid].append(match_id)
                continue

            stats = extract_player_stats(match_data, puuid)
            if not stats:
                processed[puuid].append(match_id)
                continue

            kda = calculate_kda(stats["kills"], stats["deaths"], stats["assists"])
            processed[puuid].append(match_id)

            if kda < kda_threshold:
                game_name = display_name.split("#")[0]
                roast = generate_roast(game_name, stats["championName"], stats["kills"], stats["deaths"], stats["assists"], gemini_key)
                sent = send_shame_message(webhook_url, display_name, stats["championName"], stats["kills"], stats["deaths"], stats["assists"], kda, roast)
                status = "SENT" if sent else "FAILED"
                print(f"[SHAME {status}] {display_name} - {stats['championName']} {stats['kills']}/{stats['deaths']}/{stats['assists']} (KDA: {kda:.2f})")
            else:
                print(f"[OK] {display_name} - {stats['championName']} {stats['kills']}/{stats['deaths']}/{stats['assists']} (KDA: {kda:.2f})")

        processed[puuid] = processed[puuid][-MAX_STORED_MATCHES:]

    # Check rank demotions
    for puuid, display_name in friends.items():
        check_demotions(puuid, display_name, api_key, webhook_url, gemini_key, stored_ranks)

    save_processed(processed)
    save_ranks(stored_ranks)
    print("Done.")


if __name__ == "__main__":
    main()
