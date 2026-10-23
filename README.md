# CHATBOT SONG RECOMMENDATION SYSTEM

A beginner-friendly Python + Flask web app that recommends songs by calling the public **iTunes Search API**. It can search by artist, title, genre, language, or mood-related words. Results may include album artwork, track links, and short audio previews when available.

**Project link https://chatbotsong-recommendationsystem.onrender.com**

**<img width="1917" height="1078" alt="image" src="https://github.com/user-attachments/assets/1dbb0917-e306-44e4-bbad-487953ce6148" />
<img width="800" height="450" alt="ezgif-optimized" src="https://github.com/user-attachments/assets/e04d3cff-00f8-40ef-8984-1395226bbcfd" />**


## Requirements

- Python 3.10 or newer
- Internet connection
- A modern browser

**No API key is required** for the iTunes Search API. The API is provided by Apple and its results, preview availability, and regional catalog may vary.
## Run on Windows

1. Extract the ZIP file.
2. Open the extracted `song_recommendation_chatbot` folder in VS Code.
3. Open Terminal in that folder.
4. Create a virtual environment (recommended):

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run `.venv\\Scripts\\activate.bat`, or skip the virtual environment.

5. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

6. Start the website:

   ```powershell
   py app.py
   ```

7. Open **http://127.0.0.1:5000** in your browser.

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**.

## Try these searches

- `happy Tamil songs`
- `romantic English songs`
- `relaxing music`
- `AR Rahman songs`
- `Imagine Dragons`
- `Adele`

## How it works

1. The browser sends your message to Flask's `/api/recommend` endpoint.
2. Python sends a search request to `https://itunes.apple.com/search`.
3. The API returns song metadata as JSON.
4. Flask returns selected fields to the browser.
5. JavaScript renders song cards, artwork, track links, and previews where available.

## API endpoint

`POST /api/recommend`

Example JSON request:

```json
{
  "message": "happy Tamil songs"
}
```

Example response shape:

```json
{
  "reply": "I found song recommendations related to your search.",
  "songs": [
    {
      "title": "Example Song",
      "artist": "Example Artist",
      "artwork": "https://...",
      "preview": "https://...",
      "url": "https://..."
    }
  ]
}
```

Actual results depend on the live API response.

## Troubleshooting

- **`python` is not recognized:** try `py app.py` on Windows or reinstall Python and enable "Add Python to PATH".
- **`ModuleNotFoundError`:** activate your environment and run `python -m pip install -r requirements.txt`.
- **No results:** check your internet connection and try a shorter query.
- **Preview missing:** not every track has a preview URL. Use the track link when available.
- **Port already in use:** stop the other Flask app or change the port in `app.run(...)`.

## Notes

- This is a learning/demo project. Flask's debug server is for local development, not production hosting.
- Do not assume a preview URL is available for every track.
- Follow the API provider's terms and rate limits if you expand or deploy the app.
#
#
