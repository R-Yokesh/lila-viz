# LILA BLACK — Player Journey Visualizer

Tool for visualizing player movement, fights, loot, and deaths across matches — overlaid directly on the minimap.

Built to help level designers see how matches actually play out.

---

## What it does

- Draws player paths on the minimap (humans in cyan, bots in orange)
- Shows kill/death/loot/storm events as map markers
- Timeline scrubber to replay a match or jump to any point
- Heatmaps for kill zones, death zones, and general traffic
- Filter by humans, bots, paths, or events independently
- Browse matches by map and day

---

## Running it locally

You need Python 3.8+. No Node, no build step.

```bash
pip install pyarrow pandas numpy

python process_data.py --input ./player_data --output ./public/data

cp player_data/minimaps/* public/minimaps/

python -m http.server 8080 --directory public
```

Then open `http://localhost:8080`.

---

## Deploying

Push to GitHub, import to [Vercel](https://vercel.com), set root directory to `public`, deploy. No env vars needed.

---

## Project structure

```
lila-viz/
├── public/
│   ├── index.html
│   ├── data/
│   │   ├── AmbroseValley.json
│   │   ├── GrandRift.json
│   │   └── Lockdown.json
│   └── minimaps/
│       ├── AmbroseValley_Minimap.png
│       ├── GrandRift_Minimap.png
│       └── Lockdown_Minimap.jpg
├── process_data.py
├── ARCHITECTURE.md
├── INSIGHTS.md
└── README.md
```

---

## Data

5 days of production data (Feb 10–14), 796 matches, ~89k events.

- Bots have numeric `user_id`; humans have UUID `user_id`
- Only `x` and `z` are used for 2D plotting — `y` is elevation, ignored
- Timestamps are ms from match start, relative per match
```
