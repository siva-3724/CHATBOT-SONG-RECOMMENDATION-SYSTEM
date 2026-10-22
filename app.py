import logging
import os
import re
from flask import Flask, jsonify, render_template, request
import requests

# Configure logging for professional production monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurations
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
REQUEST_TIMEOUT = 100
DEFAULT_LIMIT = 100
MAX_LIMIT = 120
MAX_MESSAGE_LENGTH = 180

# English and Tamil mood keywords
MOOD_TERMS = {
    "happy": [
        "happy Tamil songs",
        "Tamil feel good songs",
        "Tamil upbeat songs",
    ],
    "sad": [
        "sad Tamil songs",
        "Tamil melody songs",
        "Tamil emotional songs",
    ],
    "romantic": [
        "romantic Tamil songs",
        "Tamil love songs",
        "Tamil melody love songs",
    ],
    "energetic": [
        "energetic Tamil songs",
        "Tamil dance songs",
        "Tamil kuthu songs",
    ],
    "relaxing": [
        "relaxing Tamil songs",
        "Tamil soft melody songs",
        "Tamil peaceful songs",
    ],
}

TAMIL_KEYWORDS = [
    "tamil",
    "tamizh",
    "tamil songs",
    "tamil song",
    "தமிழ்",
    "தமிழ் பாடல்",
    "தமிழ் பாடல்கள்",
    "தமிழ் பாட்டு",
    "தமிழ் பாட்டுகள்",
]

TAMIL_MOOD_KEYWORDS = {
    "happy": ["happy", "joy", "feel good", "மகிழ்ச்சி", "சந்தோஷம்"],
    "sad": ["sad", "heartbreak", "melancholy", "சோகம்", "வருத்தம்"],
    "romantic": ["romantic", "love", "காதல்", "காதல் பாடல்"],
    "energetic": ["energetic", "dance", "workout", "குத்து", "ஆட்டம்"],
    "relaxing": ["relax", "relaxing", "chill", "அமைதி", "மெலடி"],
}

TAMIL_ARTISTS = [
    "A. R. Rahman",
    "Ilaiyaraaja",
    "Anirudh Ravichander",
    "Harris Jayaraj",
    "Yuvan Shankar Raja",
    "G. V. Prakash Kumar",
    "Santhosh Narayanan",
    "D. Imman",
    "Vijay Antony",
    "Sid Sriram",
    "S. P. Balasubrahmanyam",
    "K. S. Chithra",
    "Shreya Ghoshal Tamil",
    "T. M. Soundararajan",
]


def contains_tamil(text):
  """Return True if the text contains Tamil Unicode characters."""
  return bool(re.search(r"[\u0B80-\u0BFF]", text))


def normalize_text(text):
  """Normalize text for case-insensitive comparisons."""
  return re.sub(r"\s+", " ", (text or "").strip().lower())


def detect_mood(text):
  """Identify a mood from English or common Tamil keywords."""
  lowered = normalize_text(text)
  for mood, keywords in TAMIL_MOOD_KEYWORDS.items():
    if any(keyword in lowered for keyword in keywords):
      return mood
  return None


def wants_tamil(text):
  """Detect explicit Tamil-language intent."""
  lowered = normalize_text(text)
  return contains_tamil(text) or any(
      keyword in lowered for keyword in TAMIL_KEYWORDS
  )


def build_search_terms(message):
  """Create several search phrases to improve Tamil song discovery."""
  original = message.strip()
  lowered = normalize_text(original)
  tamil_requested = wants_tamil(original)
  mood = detect_mood(original)
  terms = [original]

  if tamil_requested:
    terms.extend([
        f"Tamil songs {original}",
        "Tamil songs",
    ])
    if mood and mood in MOOD_TERMS:
      terms.extend(MOOD_TERMS[mood])
  elif mood:
    terms.extend(MOOD_TERMS[mood])

  for artist in TAMIL_ARTISTS:
    if artist.lower() in lowered:
      terms.extend([
          f"{artist} Tamil songs",
          artist,
      ])
      break

  # Preserve order while removing duplicates
  unique_terms = []
  seen = set()
  for term in terms:
    term = term.strip()
    key = normalize_text(term)
    if key and key not in seen:
      seen.add(key)
      unique_terms.append(term)

  return unique_terms[:5]


def song_relevance(song, message, tamil_requested):
  """Give a basic relevance score to search results."""
  query_words = {
      word
      for word in re.findall(r"[a-zA-Z0-9]+", message.lower())
      if len(word) > 2
  }
  title = normalize_text(song.get("title"))
  artist = normalize_text(song.get("artist"))
  album = normalize_text(song.get("album"))
  combined = f"{title} {artist} {album}"
  score = 0

  for word in query_words:
    if word in combined:
      score += 3

  if tamil_requested and "tamil" in combined:
    score += 2

  return score


def search_songs(message, limit=DEFAULT_LIMIT):
  """Search iTunes for music using multiple relevant search phrases."""
  text = str(message or "").strip()
  if not text:
    return []

  limit = max(1, min(int(limit), MAX_LIMIT))
  terms = build_search_terms(text)
  tamil_requested = wants_tamil(text)
  collected = {}

  with requests.Session() as session:
    for term in terms:
      try:
        response = session.get(
            ITUNES_SEARCH_URL,
            params={
                "term": term,
                "entity": "song",
                "media": "music",
                "country": "IN",
                "limit": 25,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
      except requests.RequestException as e:
        logger.warning(f"iTunes API request failed for term '{term}': {e}")
        continue
      except ValueError:
        logger.warning(
            f"Failed to parse JSON response from iTunes for term '{term}'"
        )
        continue

      for item in data.get("results", []):
        track_id = item.get("trackId")
        if not track_id:
          continue

        song = {
            "id": track_id,
            "title": item.get("trackName") or "Unknown title",
            "artist": item.get("artistName") or "Unknown artist",
            "album": item.get("collectionName") or "Single",
            "artwork": (
                item.get("artworkUrl600") or item.get("artworkUrl100") or ""
            ),
            "preview": item.get("previewUrl") or "",
            "url": item.get("trackViewUrl") or "",
            "genre": item.get("primaryGenreName") or "Music",
            "release_date": (item.get("releaseDate") or "")[:4],
        }
        song["_score"] = song_relevance(song, text, tamil_requested)

        if (
            track_id not in collected
            or song["_score"] > collected[track_id]["_score"]
        ):
          collected[track_id] = song

      if len(collected) >= limit * 3:
        break

  songs = sorted(
      collected.values(),
      key=lambda song: song["_score"],
      reverse=True,
  )[:limit]

  for song in songs:
    song.pop("_score", None)

  return songs


@app.route("/")
def home():
  return render_template("index.html")


@app.route("/api/recommend", methods=["POST"])
def recommend():
  data = request.get_json(silent=True)
  if not data or not isinstance(data, dict):
    return (
        jsonify({
            "reply": "Invalid request format. Please send valid JSON.",
            "songs": [],
        }),
        400,
    )

  message = str(data.get("message", "")).strip()
  if not message:
    return (
        jsonify({
            "reply": "Enter a mood, artist, or song name to get recommendations.",
            "songs": [],
        }),
        400,
    )

  if len(message) > MAX_MESSAGE_LENGTH:
    return (
        jsonify({
            "reply": (
                f"Please keep your search under {MAX_MESSAGE_LENGTH}"
                " characters."
            ),
            "songs": [],
        }),
        400,
    )

  try:
    songs = search_songs(message)
    if songs:
      language = "Tamil" if wants_tamil(message) else "music"
      return jsonify({
          "reply": (
              f"I found {len(songs)} {language} recommendations related to"
              f" “{message}”."
          ),
          "songs": songs,
      })

    return jsonify({
        "reply": (
            "I couldn't find matching songs right now. Check your internet"
            " connection or try an artist name, such as Anirudh, A. R. Rahman,"
            " or Ilaiyaraaja."
        ),
        "songs": [],
    })
  except Exception as e:
    logger.error(f"Unexpected error in /api/recommend: {e}", exc_info=True)
    return (
        jsonify({
            "reply": "An internal error occurred. Please try again later.",
            "songs": [],
        }),
        500,
    )


@app.route("/health", methods=["GET"])
def health():
  return jsonify({"status": "ok", "service": "music-recommendation-chatbot"})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
  app.run(host="0.0.0.0", port=port, debug=debug_mode)