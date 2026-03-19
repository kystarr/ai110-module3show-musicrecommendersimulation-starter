"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import textwrap
from tabulate import tabulate  # CHALLENGE 4: visual summary tables

from recommender import load_songs, recommend_songs, SCORING_MODES

# CHALLENGE 4: Max character width for the "Why" column before wrapping.
_REASONS_WIDTH = 52


PROFILES = {
    "High-Energy Pop":    {"genre": "pop",   "mood": "happy",   "energy": 0.85},
    "Chill Lofi":         {"genre": "lofi",  "mood": "chill",   "energy": 0.35},
    "Deep Intense Rock":  {"genre": "rock",  "mood": "intense", "energy": 0.95},

    # --- Advanced-feature profiles (Challenge 1) ---
    "A1. Nostalgic 2000s Fan    (folk/nostalgic/0.35)": {
        "genre": "folk", "mood": "nostalgic", "energy": 0.35,
        "preferred_decade": 2000, "mood_tags": ["nostalgic", "melancholic"],
    },
    "A2. Modern Euphoric Dancer (pop/happy/0.90)":      {
        "genre": "pop", "mood": "happy", "energy": 0.90,
        "preferred_decade": 2020, "mood_tags": ["euphoric", "energizing"],
    },
    "A3. 90s Introspective Chill (lofi/chill/0.30)":   {
        "genre": "lofi", "mood": "chill", "energy": 0.30,
        "preferred_decade": 1990, "mood_tags": ["introspective", "serene"],
    },

    # --- Adversarial / edge-case profiles ---
    "1a. Energy Phantom LOW  (pop/happy/0.01)":     {"genre": "pop",        "mood": "happy",      "energy": 0.01},
    "1b. Energy Phantom HIGH (pop/happy/0.99)":     {"genre": "pop",        "mood": "happy",      "energy": 0.99},
    "2.  Genre Tyrant        (metal/calm/0.1)":     {"genre": "metal",      "mood": "calm",       "energy": 0.1},
    "3.  Nonexistent Genre   (k-pop/happy/0.5)":    {"genre": "k-pop",      "mood": "happy",      "energy": 0.5},
    "4.  Nonexistent Mood    (lofi/devastated/0.4)":{"genre": "lofi",       "mood": "devastated", "energy": 0.4},
    "5.  High-Energy Sad     (indie folk/sad/0.9)": {"genre": "indie folk", "mood": "sad",        "energy": 0.9},
    "9.  Empty Prefs":                              {},
}


def _make_table(recommendations: list) -> str:
    """
    CHALLENGE 4: Convert a recommendations list into a tabulate grid string.

    Columns: Rank | Title | Artist | Genre | Score | Why
    The "Why" column is word-wrapped to _REASONS_WIDTH chars so long reason
    strings don't blow out the terminal width.
    """
    rows = []
    for i, (song, score, reasons) in enumerate(recommendations, start=1):
        wrapped = textwrap.fill(reasons, width=_REASONS_WIDTH)
        rows.append([
            f"#{i}",
            song.get("title", ""),
            song.get("artist", ""),
            song.get("genre", ""),
            f"{score:.2f}",
            wrapped,
        ])
    headers = ["#", "Title", "Artist", "Genre", "Score", "Why"]
    return tabulate(rows, headers=headers, tablefmt="grid")


def print_recommendations(profile_name: str, recommendations: list) -> None:
    """CHALLENGE 4: Display recommendations as a formatted ASCII grid table."""
    print(f"\n  Profile: {profile_name}")
    print(_make_table(recommendations))


# CHALLENGE 2: Profile used to demonstrate how the same user gets different
# results depending on which scoring mode is active.
MODE_DEMO_PROFILE = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.85,
    "preferred_decade": 2020,
    "mood_tags": ["euphoric", "energizing"],
}


def print_mode_comparison(songs: list) -> None:
    """CHALLENGE 2: Run MODE_DEMO_PROFILE through every scoring mode and print a side-by-side view."""
    print("\n" + "#" * 55)
    print("  CHALLENGE 2 -- SCORING MODE COMPARISON")
    print("  Same profile, different ranking strategies")
    print("#" * 55)

    for mode_key, strategy in SCORING_MODES.items():
        label = strategy.name if strategy is not None else "Default"
        print(f"\n  Mode: {label}  [{mode_key}]")
        results = recommend_songs(MODE_DEMO_PROFILE, songs, k=3, strategy=strategy)
        print(_make_table(results))

    print("\n" + "#" * 55 + "\n")


# CHALLENGE 3: Profiles where repeated artists/genres appear without diversity,
# making them good candidates to show the penalty in action.
DIVERSITY_DEMO_PROFILES = {
    "Neon Echo fan (pop/happy/0.85)": {"genre": "pop", "mood": "happy", "energy": 0.85},
    "Lofi devotee  (lofi/chill/0.38)": {"genre": "lofi", "mood": "chill", "energy": 0.38},
}


def print_diversity_comparison(songs: list) -> None:
    """
    CHALLENGE 3: Run each DIVERSITY_DEMO_PROFILE with diversity=False then
    diversity=True and print both lists side by side so the penalty is visible.
    """
    print("\n" + "#" * 55)
    print("  CHALLENGE 3 -- DIVERSITY PENALTY COMPARISON")
    print("  Same profile: diversity OFF vs diversity ON")
    print("#" * 55)

    for profile_name, user_prefs in DIVERSITY_DEMO_PROFILES.items():
        print(f"\n{'=' * 55}")
        print(f"  Profile: {profile_name}")
        print(f"{'=' * 55}")

        for label, flag in [("diversity=OFF", False), ("diversity=ON ", True)]:
            print(f"\n  [{label}]")
            results = recommend_songs(user_prefs, songs, k=5, diversity=flag)
            print(_make_table(results))

    print("\n" + "#" * 55 + "\n")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for profile_name, user_prefs in PROFILES.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(profile_name, recommendations)

    print_mode_comparison(songs)
    print_diversity_comparison(songs)


if __name__ == "__main__":
    main()
