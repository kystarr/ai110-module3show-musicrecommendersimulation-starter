import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py

    CHALLENGE 1: Added popularity, release_decade, and mood_tags fields.
    Defaults are set so existing tests pass without modification.
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # CHALLENGE 1 fields
    popularity: int = 50          # 0-100 chart popularity
    release_decade: int = 2010    # e.g. 1980, 1990, 2000, 2010, 2020
    mood_tags: str = ""           # pipe-separated detail tags, e.g. "euphoric|uplifting"


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> float:
        """Returns a score between 0.0 and 1.0 reflecting how well a song matches the user's profile."""
        genre_match = 1 if song.genre == user.favorite_genre else 0
        mood_match  = 1 if song.mood  == user.favorite_mood  else 0
        energy_prox = 1 - abs(song.energy - user.target_energy)
        return (genre_match * 0.30) + (mood_match * 0.20) + (energy_prox * 0.50)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Scores all songs and returns the top k matches for the given user profile."""
        ranked = sorted(self.songs, key=lambda s: self._score(user, s), reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a human-readable string explaining why a song was recommended."""
        reasons = []
        if song.genre == user.favorite_genre:
            reasons.append(f"genre matches ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"mood matches ({song.mood})")
        energy_prox = 1 - abs(song.energy - user.target_energy)
        reasons.append(f"energy proximity {energy_prox:.2f}")
        return ", ".join(reasons)


def build_profile_from_likes(liked_ids: List[int], songs: List[Song]) -> UserProfile:
    """
    Builds a UserProfile by averaging the features of songs the user has liked.
    This lets the system infer taste from behaviour rather than requiring
    the user to fill in explicit preferences.
    """
    liked = [s for s in songs if s.id in liked_ids]
    if not liked:
        raise ValueError("No matching songs found for the provided liked_ids.")

    favorite_genre = Counter(s.genre for s in liked).most_common(1)[0][0]
    favorite_mood  = Counter(s.mood  for s in liked).most_common(1)[0][0]
    target_energy  = sum(s.energy        for s in liked) / len(liked)
    likes_acoustic = (sum(s.acousticness for s in liked) / len(liked)) >= 0.5

    return UserProfile(
        favorite_genre=favorite_genre,
        favorite_mood=favorite_mood,
        target_energy=target_energy,
        likes_acoustic=likes_acoustic,
    )


def load_songs(csv_path: str) -> List[Dict]:
    """
    Reads songs from a CSV file and returns them as a list of dictionaries.
    Numerical fields are cast to int or float; categorical fields stay as strings.
    """
    # Fields to cast and their target types
    # CHALLENGE 1: added "popularity" and "release_decade" to int_fields
    int_fields   = {"id", "tempo_bpm", "popularity", "release_decade"}
    float_fields = {"energy", "valence", "danceability", "acousticness"}

    songs = []

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Skip any blank rows the CSV reader may produce
                if not any(row.values()):
                    continue

                song = {}
                for key, value in row.items():
                    if key in int_fields:
                        song[key] = int(float(value))   # float() first handles "78.0"
                    elif key in float_fields:
                        song[key] = float(value)
                    else:
                        song[key] = value               # genre, mood, title, artist

                songs.append(song)

    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find songs file at: {csv_path}")
    except ValueError as e:
        raise ValueError(f"Failed to convert a field to the expected type: {e}")

    return songs


def _score_song_dict(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """Scores a single song dict against user preferences and returns (total_score, reasons)."""
    score = 0.0
    reasons = []

    # Genre match: +2.0 points
    if song.get("genre") == user_prefs.get("genre"):
        score += 2.0
        reasons.append("genre match (+2.0)")

    # Mood match: +1.0 point
    if song.get("mood") == user_prefs.get("mood"):
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Energy similarity: up to +1.0 point
    song_energy   = song.get("energy", 0.0)
    target_energy = user_prefs.get("energy", 0.0)
    similarity    = 1 - (abs(song_energy - target_energy) / 10)
    energy_score  = round(similarity * 1.0, 2)
    score        += energy_score
    reasons.append(f"energy similarity (+{energy_score})")

    # CHALLENGE 1: Popularity bonus — up to +0.5 points, scales linearly with chart popularity
    popularity = song.get("popularity", 50)
    pop_score  = round((popularity / 100) * 0.5, 2)
    score     += pop_score
    reasons.append(f"popularity {popularity}/100 (+{pop_score})")

    # CHALLENGE 1: Decade proximity — up to +1.0 point, rewards songs from the user's preferred era.
    # Score = max(0, 1 - gap/30): same decade +1.0, 10 yrs off +0.67, 30+ yrs off 0
    if "preferred_decade" in user_prefs:
        song_decade  = song.get("release_decade", 2010)
        pref_decade  = user_prefs["preferred_decade"]
        decade_score = round(max(0.0, 1 - abs(song_decade - pref_decade) / 30), 2)
        score       += decade_score
        reasons.append(f"decade {song_decade} vs pref {pref_decade} (+{decade_score})")

    # CHALLENGE 1: Mood-tag overlap — +0.4 per shared detailed tag, capped at +1.2
    if "mood_tags" in user_prefs:
        song_tags = set(song.get("mood_tags", "").split("|"))
        user_tags = set(user_prefs["mood_tags"])
        shared    = song_tags & user_tags
        tag_score = round(min(len(shared) * 0.4, 1.2), 2)
        score    += tag_score
        if shared:
            reasons.append(f"mood tags {shared} (+{tag_score})")

    return round(score, 4), ", ".join(reasons)


# ---------------------------------------------------------------------------
# Challenge 2 — Strategy Pattern
# ---------------------------------------------------------------------------
# Each ScoringStrategy subclass encapsulates one ranking philosophy.
# Adding a new mode = adding one class and one entry in SCORING_MODES.
# recommend_songs() accepts an optional `strategy=` parameter so callers
# in main.py can switch modes without touching any scoring logic.
# ---------------------------------------------------------------------------

class ScoringStrategy:
    """
    CHALLENGE 2: Base class for the Strategy pattern.

    Each subclass encapsulates one ranking philosophy.
    Subclasses must implement score(), which returns (total_score, reasons_string)
    for a single (user_prefs, song) pair.
    """
    name: str = "base"

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, str]:
        raise NotImplementedError(f"{self.__class__.__name__} must implement score()")


class GenreFirstStrategy(ScoringStrategy):
    """
    CHALLENGE 2: Genre-First scoring mode.

    Genre match is the dominant signal (+4.0).
    Mood and energy act as tiebreakers.
    Best for: users who are loyal to a specific genre and want to stay in it.
    """
    name = "Genre-First"

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, str]:
        score, reasons = 0.0, []

        if song.get("genre") == user_prefs.get("genre"):
            score += 4.0
            reasons.append("genre match (+4.0)")

        if song.get("mood") == user_prefs.get("mood"):
            score += 1.0
            reasons.append("mood match (+1.0)")

        energy_prox = round(1 - abs(song.get("energy", 0) - user_prefs.get("energy", 0)), 2)
        score += energy_prox * 0.5
        reasons.append(f"energy proximity (+{energy_prox * 0.5:.2f})")

        popularity = song.get("popularity", 50)
        pop_score  = round((popularity / 100) * 0.25, 2)
        score     += pop_score
        reasons.append(f"popularity {popularity}/100 (+{pop_score})")

        return round(score, 4), ", ".join(reasons)


class MoodFirstStrategy(ScoringStrategy):
    """
    CHALLENGE 2: Mood-First scoring mode.

    Mood match is the dominant signal (+4.0).
    Detailed mood-tag overlap acts as a secondary signal.
    Best for: users who care most about how a song makes them feel.
    """
    name = "Mood-First"

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, str]:
        score, reasons = 0.0, []

        if song.get("mood") == user_prefs.get("mood"):
            score += 4.0
            reasons.append("mood match (+4.0)")

        if song.get("genre") == user_prefs.get("genre"):
            score += 1.0
            reasons.append("genre match (+1.0)")

        energy_prox = round(1 - abs(song.get("energy", 0) - user_prefs.get("energy", 0)), 2)
        score += energy_prox * 0.5
        reasons.append(f"energy proximity (+{energy_prox * 0.5:.2f})")

        # Mood-tag overlap: +0.5 per shared tag, capped at +1.5
        if "mood_tags" in user_prefs:
            song_tags = set(song.get("mood_tags", "").split("|"))
            user_tags = set(user_prefs["mood_tags"])
            shared    = song_tags & user_tags
            tag_score = round(min(len(shared) * 0.5, 1.5), 2)
            score    += tag_score
            if shared:
                reasons.append(f"mood tags {shared} (+{tag_score})")

        return round(score, 4), ", ".join(reasons)


class EnergyFocusedStrategy(ScoringStrategy):
    """
    CHALLENGE 2: Energy-Focused scoring mode.

    Energy proximity is the dominant signal (up to +4.0).
    Genre and mood contribute small bonuses.
    Best for: activity-based listening (workouts, studying, sleep) where
    energy level matters more than genre or mood label.
    """
    name = "Energy-Focused"

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, str]:
        score, reasons = 0.0, []

        # Energy proximity scaled to 0–4
        energy_prox  = 1 - abs(song.get("energy", 0) - user_prefs.get("energy", 0))
        energy_score = round(energy_prox * 4.0, 2)
        score       += energy_score
        reasons.append(f"energy proximity (+{energy_score})")

        if song.get("genre") == user_prefs.get("genre"):
            score += 1.0
            reasons.append("genre match (+1.0)")

        if song.get("mood") == user_prefs.get("mood"):
            score += 0.5
            reasons.append("mood match (+0.5)")

        # Danceability bonus when user energy is high (above 0.7): up to +0.5
        if user_prefs.get("energy", 0) >= 0.7:
            dance_score = round(song.get("danceability", 0) * 0.5, 2)
            score      += dance_score
            reasons.append(f"danceability (+{dance_score})")

        return round(score, 4), ", ".join(reasons)


class VibeMatchStrategy(ScoringStrategy):
    """
    CHALLENGE 2: Vibe-Match scoring mode.

    Detailed mood-tag overlap and era proximity are the dominant signals.
    Combines CHALLENGE 1 features (mood_tags, release_decade) into a single feel score.
    Best for: users who want the system to understand their vibe, not just
    their genre or a broad mood label.
    """
    name = "Vibe-Match"

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, str]:
        score, reasons = 0.0, []

        # Mood-tag overlap: +1.5 per shared tag, capped at +3.0
        if "mood_tags" in user_prefs:
            song_tags = set(song.get("mood_tags", "").split("|"))
            user_tags = set(user_prefs["mood_tags"])
            shared    = song_tags & user_tags
            tag_score = round(min(len(shared) * 1.5, 3.0), 2)
            score    += tag_score
            if shared:
                reasons.append(f"mood tags {shared} (+{tag_score})")

        # Decade proximity: up to +2.0
        # max(0, 1 - gap/30) scaled to 2
        if "preferred_decade" in user_prefs:
            song_decade  = song.get("release_decade", 2010)
            pref_decade  = user_prefs["preferred_decade"]
            decade_score = round(max(0.0, 1 - abs(song_decade - pref_decade) / 30) * 2.0, 2)
            score       += decade_score
            reasons.append(f"decade {song_decade} vs pref {pref_decade} (+{decade_score})")

        # Energy proximity: up to +1.0
        energy_prox = round(1 - abs(song.get("energy", 0) - user_prefs.get("energy", 0)), 2)
        score      += energy_prox
        reasons.append(f"energy proximity (+{energy_prox})")

        # Popularity: up to +0.5
        popularity = song.get("popularity", 50)
        pop_score  = round((popularity / 100) * 0.5, 2)
        score     += pop_score
        reasons.append(f"popularity {popularity}/100 (+{pop_score})")

        return round(score, 4), ", ".join(reasons)


# Registry — add new strategies here and they become available in main.py
SCORING_MODES: Dict[str, ScoringStrategy] = {
    "default":        None,                  # uses the original _score_song_dict
    "genre-first":    GenreFirstStrategy(),
    "mood-first":     MoodFirstStrategy(),
    "energy-focused": EnergyFocusedStrategy(),
    "vibe-match":     VibeMatchStrategy(),
}


# ---------------------------------------------------------------------------
# CHALLENGE 3 — Diversity Penalty
# ---------------------------------------------------------------------------
# _apply_diversity_penalty uses a greedy selection loop rather than a simple
# score modifier.  Why greedy?  Because whether a song deserves a penalty
# depends on what has *already been selected*, which changes with each pick.
#
# Rules (applied multiplicatively so both can stack):
#   Duplicate artist : score × ARTIST_PENALTY  (default 0.70 → -30%)
#   Duplicate genre  : score × GENRE_PENALTY   (default 0.85 → -15%)
#   Both             : score × 0.70 × 0.85 = 0.595 (≈ -40%)
#
# The penalty is recorded in the reasons string so every output line shows
# exactly why a song was demoted.
# ---------------------------------------------------------------------------

def _apply_diversity_penalty(
    scored: List[Tuple[Dict, float, str]],
    k: int,
    artist_penalty: float = 0.70,
    genre_penalty: float = 0.85,
) -> List[Tuple[Dict, float, str]]:
    """
    CHALLENGE 3: Greedy re-ranker that penalizes repeated artists and genres.

    Algorithm:
      1. Sort all songs by their raw score (best first).
      2. Greedily pick the highest-scoring song into the result list.
      3. Before each subsequent pick, multiply the raw score of any remaining
         song whose artist or genre already appears in the result list.
      4. Repeat until k songs are selected or the pool is exhausted.

    Args:
        scored:         Output of the scoring step — list of (song, score, reasons).
        k:              Number of songs to return.
        artist_penalty: Multiplier applied when the artist is already selected (0-1).
        genre_penalty:  Multiplier applied when the genre is already selected (0-1).

    Returns:
        Re-ranked list of (song, adjusted_score, reasons) of length <= k.
    """
    remaining = sorted(scored, key=lambda x: x[1], reverse=True)
    selected  = []
    seen_artists: set = set()
    seen_genres:  set = set()

    while len(selected) < k and remaining:
        # Apply penalties based on what is already selected
        candidates = []
        for song, raw_score, reasons in remaining:
            adjusted = raw_score
            penalty_notes = []

            if song.get("artist") in seen_artists:
                adjusted *= artist_penalty
                penalty_notes.append(f"artist repeat x{artist_penalty}")

            if song.get("genre") in seen_genres:
                adjusted *= genre_penalty
                penalty_notes.append(f"genre repeat x{genre_penalty}")

            adjusted = round(adjusted, 4)
            if penalty_notes:
                reasons = reasons + f", DIVERSITY PENALTY ({', '.join(penalty_notes)}) -> {adjusted}"

            candidates.append((song, adjusted, reasons))

        # Pick the best candidate after penalties
        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0]
        selected.append(best)

        # Register the chosen song's artist and genre as seen
        seen_artists.add(best[0].get("artist"))
        seen_genres.add(best[0].get("genre"))

        # Remove the chosen song from remaining (match by original raw score + title)
        chosen_title = best[0].get("title")
        remaining = [(s, sc, r) for s, sc, r in remaining if s.get("title") != chosen_title]

    return selected


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diversity: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, sorts by score, and returns the top k results.

    CHALLENGE 2: Added optional `strategy` parameter.
    Pass any ScoringStrategy instance (or a value from SCORING_MODES) to
    switch ranking modes. Defaults to the original _score_song_dict
    behaviour when strategy is None.

    CHALLENGE 3: Added optional `diversity` flag.
    When True, passes results through _apply_diversity_penalty before
    returning, which prevents repeated artists and genres from dominating
    the top-k list.
    """
    scored = []

    for song in songs:
        if strategy is None:
            score, reasons = _score_song_dict(user_prefs, song)
        else:
            score, reasons = strategy.score(user_prefs, song)
        scored.append((song, score, reasons))

    if diversity:
        return _apply_diversity_penalty(scored, k)

    ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    return ranked[:k]
