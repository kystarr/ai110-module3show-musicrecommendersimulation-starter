import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
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
    int_fields   = {"id", "tempo_bpm"}
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

    return round(score, 4), ", ".join(reasons)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, sorts by score, and returns the top k results.
    """
    scored = []

    # Step 1: Score every song and collect results
    for song in songs:
        score, reasons = _score_song_dict(user_prefs, song)
        scored.append((song, score, reasons))

    # Step 2: Sort all results from highest to lowest score
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)

    # Step 3: Return only the top k
    return ranked[:k]
