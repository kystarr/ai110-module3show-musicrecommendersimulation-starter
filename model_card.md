# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

VibeMatch
---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

This recommender generates a ranked list of up to 5 songs from a small 20-song catalog based on three explicit user preferences: favorite genre, preferred mood, and target energy level. It is designed for classroom exploration, not real users — the catalog is too small and the scoring too simple to be useful in a production setting. The system assumes the user can clearly articulate their preferences upfront, that those preferences are stable (it has no concept of listening history or changing taste), and that genre, mood, and energy are the only signals that matter. It does not consider tempo, lyrics, artist familiarity, or what other listeners with similar tastes have enjoyed.


## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

The system looks at three things about each song: its genre (like pop, lofi, or metal), its mood (like happy, chill, or intense), and its energy level on a scale from 0 to 1, where 0 is very quiet and 1 is very loud and driving. When you give the system your preferences, it goes through every song in the catalog and awards points based on how well each song matches. A genre match is worth the most at 2 points, because if you want lofi you probably don't want metal regardless of anything else. A mood match is worth 1 point, and energy similarity adds a small bonus based on how close the song's energy is to your target. Every song gets a total score, and the system returns the top 5 in order from highest to lowest. The starter code provided empty placeholder functions, so the scoring weights, the decision to treat genre as the strongest signal, and the energy similarity formula were all choices made during the implementation. One thing that carried over from the starter structure is that all three features are evaluated independently and added together. There is no way for one signal to cancel out another, which turns out to be a real limitation when preferences conflict.


## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

The catalog contains 20 songs stored in a CSV file. 10 from the original starter dataset and 10 added during development. Each song is described by genre, mood, energy level, tempo, danceability, valence, and acousticness. The genres represented include pop, lofi, rock, metal, jazz, classical, folk, indie folk, country, hip-hop, r&b, reggae, electronic, synthwave, ambient, dream pop, and indie pop. Moods covered include happy, chill, intense, moody, sad, calm, relaxed, focused, energetic, nostalgic, romantic, upbeat, and dreamy. Even with the additions, the dataset has noticeable gaps: 16 of the 17 genres have only one song each, meaning a user whose favorite genre is jazz or country will only ever get one genre-matched result before the system runs out of options. Entire genres are missing entirely. There is nothing representing soul, blues, punk, k-pop, or Latin music, and several common emotional states like angry, melancholic, or euphoric have no matching songs. The catalog also skews toward Western, English-language genres, which means the system implicitly assumes a particular cultural background for its users.


## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

The system works best for users whose preferences align cleanly with the catalog. Particularly pop, lofi, and rock listeners, since those genres have multiple songs and the top results visibly made sense. The High-Energy Pop profile correctly surfaced Sunrise City at #1 with a perfect score of 4.00, matching on genre, mood, and energy simultaneously, which matched intuition exactly. The Chill Lofi profile similarly returned Library Rain and Midnight Coding as its top two, both genuinely fitting choices. The scoring also handles energy as a tiebreaker correctly within a genre: when two pop songs both matched genre and mood, the one with energy closer to the target ranked higher. The system is also transparent as every recommendation comes with a plain-language reason explaining exactly which signals fired and how many points each contributed, which makes it easy to understand and trust the output even when the results are imperfect.


## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

The system's biggest weakness is that it over-prioritizes genre match at the expense of every other preference. Genre is worth +2.0 points while mood is worth +1.0 and energy similarity rarely contributes more than 0.1 points of difference between songs, which means genre matching alone can outweigh mood and energy combined. This became clear when testing a "metal/calm/low-energy" profile: Iron Cathedral — a loud, intense metal song — was ranked #1 over Glass Sonata No. 3, a quiet classical piece that matched the calm mood and low energy almost perfectly, simply because Iron Cathedral shared the genre label. In practice, this means a user who wants soft, calming music but happens to label their favorite genre as "metal" will consistently receive songs that feel wrong emotionally, and the scoring system has no way to correct for that mismatch. A more balanced design would reduce the genre bonus or make it partial rather than binary, so that mood and energy can pull results in a direction that better reflects how a user actually wants to feel.


---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

I tested three standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) to establish a baseline, then designed a set of adversarial profiles intended to expose edge cases in the scoring logic. These included a "High-Energy Sad" user who wanted intense indie folk, a "Genre Tyrant" profile requesting calm metal at low energy, a profile with a genre that doesn't exist in the catalog (k-pop), and an empty profile with no preferences at all. For each profile I looked at whether the top results matched what a reasonable listener would actually want, and whether the scores and reasons shown made logical sense. I also temporarily commented out the mood check across all three scoring functions to test the system's sensitivity. I wanted to see whether removing mood changed the rankings significantly or whether another feature was already dominating. The most surprising finding was that the "High-Energy Sad" profile still ranked Tide and Ember, a quiet, low-energy song, as #1 with a score of 3.94, because genre and mood matched so strongly that the energy mismatch was almost invisible to the scoring formula. The mood removal experiment confirmed this: even without mood scoring, Tide and Ember stayed at #1 because genre match alone was enough to keep it there.
---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

The most important fix would be correcting the energy similarity formula — dividing by 10 instead of 1 compresses all energy scores into a tiny range, making energy almost meaningless as a signal. Fixing that one line would immediately make the system more sensitive to what users actually ask for. Beyond the bug, the genre weight needs rebalancing: reducing it from a flat +2.0 to something partial or graduated would allow mood and energy to surface cross-genre results that might actually fit better emotionally. Adding acousticness as a scored feature would also help, since the system already collects that preference through likes_acoustic but silently ignores it. To improve diversity, the top-k results could enforce a "no two songs from the same genre" rule so that users of well-represented genres like lofi don't receive five variations of the same sound. For handling more complex tastes, the system could accept a range for energy rather than a single target value — someone who wants "high energy" probably means anything above 0.7, not exactly 0.85 — and could blend preferences inferred from listening history with preferences the user states explicitly rather than treating them as separate paths.

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  

Before this project I had no idea how recommender systems worked in different recommendation based apps. Building this from scratch taught me the difference between content-based filtering which matches songs to a user's stated preferences, and collaborative filtering, which works by finding other users with similar taste and borrowing their history. The most surprising thing I discovered is how much a few simple numbers can go wrong: a single division by 10 in the energy formula was enough to make an entire preference signal almost meaningless, and I only caught it by running adversarial test cases. That made me think differently about apps like Spotify or YouTube Music. I used to assume they had some deep understanding of what I liked, but now I realize even large-scale recommenders are built on the same basic ideas of scoring and ranking, just with far more features and data. The logic is simpler than I expected.