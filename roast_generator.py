import random
from google import genai

_client = None

FALLBACK_ROASTS = [
    "Oof. {name}'s {champ} is currently a walking cannon minion. {k}/{d}/{a}.",
    "{name}: {k}/{d}/{a}. A tragedy in three acts.",
    "We regret to inform you that {name} is currently playing League of Legends. {k}/{d}/{a} on {champ}.",
    "The enemy team just sent {name} a thank-you card for the free gold. {k}/{d}/{a} on {champ}.",
    "Can someone do a wellness check on {name}? Playing {champ} like this violates the Geneva Conventions. {k}/{d}/{a}.",
]


def generate_roast(player_name, champion, kills, deaths, assists, gemini_api_key):
    """Generate a humorous roast using Gemini. Falls back to a template on failure."""
    global _client

    try:
        if _client is None:
            _client = genai.Client(api_key=gemini_api_key)

        prompt = (
            "You are a trash-talk bot for a Discord friend group that plays League of Legends together.\n"
            "Generate a short, punchy roast (1-2 sentences max) for a player who just had a terrible game.\n\n"
            f"Player: {player_name}\n"
            f"Champion played: {champion}\n"
            f"KDA: {kills}/{deaths}/{assists}\n\n"
            "Here are examples of the tone and style to match:\n"
            f'- "{player_name} just opened a soup kitchen in their lane, because they are feeding the enemy team out of their minds. Current KDA: {kills}/{deaths}/{assists}."\n'
            f'- "Just a heads up, {player_name} is currently {kills}/{deaths}/{assists} on {champion}. They\'re desperately rushing that 0/10 power spike. Everyone stay calm."\n'
            f'- "Oof. {player_name}\'s {champion} is currently a walking cannon minion."\n'
            f'- "{player_name}: {kills}/{deaths}/{assists}. A tragedy in three acts."\n'
            f'- "We regret to inform you that {player_name} is currently playing League of Legends."\n'
            f'- "I\'ve seen beginner bots with better macro than {player_name} is showing right now. Absolute cinema."\n'
            f'- "Did {player_name}\'s mouse disconnect, or is this just what their {champion} gameplay naturally looks like?"\n\n'
            "Rules:\n"
            "- Keep it SHORT and PUNCHY like the examples above\n"
            "- Friendly banter, not genuinely hurtful\n"
            "- No slurs or offensive language\n"
            "- Do not use any markdown formatting\n"
            "- Reply with ONLY the roast text, nothing else"
        )

        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        roast = response.text.strip()
        if roast:
            return roast
    except Exception as e:
        print(f"Gemini API error: {e}")

    # Fallback to template
    template = random.choice(FALLBACK_ROASTS)
    return template.format(name=player_name, champ=champion, k=kills, d=deaths, a=assists)


FALLBACK_DEMOTION_ROASTS = [
    "{name} just demoted from {old_rank} to {new_rank}. The climb was nice while it lasted.",
    "Breaking news: {name} has been sent back to {new_rank}. Skill issue.",
    "{name} just speedran a demotion from {old_rank} to {new_rank}. Impressive, honestly.",
    "Press F for {name}. {old_rank} was too good for them anyway. Welcome back to {new_rank}.",
    "Riot just personally demoted {name} from {old_rank} to {new_rank}. Even the system is disappointed.",
]


def generate_demotion_roast(player_name, old_rank, new_rank, queue_name, gemini_api_key):
    """Generate a humorous demotion roast using Gemini."""
    global _client

    try:
        if _client is None:
            _client = genai.Client(api_key=gemini_api_key)

        prompt = (
            "You are a trash-talk bot for a Discord friend group that plays League of Legends together.\n"
            "Generate a short, punchy roast (1-2 sentences max) for a player who just DEMOTED in ranked.\n\n"
            f"Player: {player_name}\n"
            f"Queue: {queue_name}\n"
            f"Demoted from: {old_rank}\n"
            f"Demoted to: {new_rank}\n\n"
            "Here are examples of the tone and style to match:\n"
            f'- "{player_name} just got sent back to {new_rank}. The elo gods have spoken."\n'
            f'- "Press F for {player_name}. {old_rank} was too good for them anyway."\n'
            f'- "{player_name} speedran a demotion from {old_rank} to {new_rank}. Impressive, honestly."\n'
            f'- "Riot personally kicked {player_name} out of {old_rank}. Even the system is disappointed."\n\n'
            "Rules:\n"
            "- Keep it SHORT and PUNCHY like the examples above\n"
            "- Friendly banter, not genuinely hurtful\n"
            "- No slurs or offensive language\n"
            "- Do not use any markdown formatting\n"
            "- Reply with ONLY the roast text, nothing else"
        )

        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        roast = response.text.strip()
        if roast:
            return roast
    except Exception as e:
        print(f"Gemini API error: {e}")

    template = random.choice(FALLBACK_DEMOTION_ROASTS)
    return template.format(name=player_name, old_rank=old_rank, new_rank=new_rank)
