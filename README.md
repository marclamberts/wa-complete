# WA Complete

The Waltzing Analytics **Match Hub 2026-27** as a Streamlit app: Eredivisie, Jupiler Pro League, Bundesliga,
2. Bundesliga, 3. Liga and the five Regionalligen, driven by the WA xDanger models on IMPECT events, with Opta, StatsBomb,
SkillCorner and Transfermarkt from the WA Scouting DB.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Reports

| Page | Contents |
|---|---|
| League | table with xG, xDanger and set-piece xG for / against, xDanger for vs against scatter |
| Pre-match | win / draw / loss and expected goals, where the edges are, style radar (both teams vs the league), team cards: ranks, last five, key xDanger creators, set pieces, squad (Transfermarkt, SkillCorner, StatsBomb, Opta) |
| Post-match | match numbers, xG race, xDanger momentum, shot maps, players with xDanger and the Model 5 rating, every set piece |
| Set pieces | attacking and defending per type vs the league, corner maps for and against, delivery menu, takers, targets |
| Restarts | goal kicks, throw-ins, kick-offs, own-half free kicks: own and opponents' (pressing), restart menu, league build-up |
| Penalties | goal-mouth placement, takers, keepers, teams |
| Scouting | filterable player table (xDanger per 90 with percentiles, Models 3 to 5, every provider); select a row for the **pizza** and **deviation radar**, with a second player to compare |
| Set-piece scouting | delivery and finishing / heading archetypes with definitions, zone profiles and delivery quality |
| Models | how the numbers are made |

**Navy / fog** in the sidebar. The URL keeps league, page, selection and style, so any view can be bookmarked.

## Downloads (every page)

- **PDF**: "Make PDF", then "Download PDF": a cover, the page's charts and its tables, in the active style.
- **Excel**: every table of the view, one sheet each.
- **CSV**: one table or all of them as a zip.
- **JSON**: the data behind the view.
- **League Excel / League CSV**: the whole league (20 tables) as written by the daily agent.

## Data

The app reads the league files written every day by the **WA Match Hub 26-27** agent
(`~/Downloads/Agents/WA Match Hub 26-27`, launchd job at 12:30). Where it looks, first hit wins:

1. `WA_HUB_DATA` environment variable, a folder with `<KEY>/WA_Hub_*.json`
2. `./data` in this repo (git-ignored)
3. `~/Downloads/Agents/WA Match Hub 26-27/web/exports`

The app reloads a league as soon as the agent writes a new file. League data is licensed and is never committed
(`data/` is in `.gitignore`); for a hosted copy, sync the exports to the server's `data/` folder or set `WA_HUB_DATA`.

## Layout

```
app.py                     sidebar (style, league, page) and routing
wa_complete/data.py        finds and caches the league payloads
wa_complete/style.py       navy / fog palettes: Streamlit theme, CSS, matplotlib
wa_complete/charts.py      pitch, shot maps, xG race, momentum, corner maps, goal mouth, pizza, deviation radar
wa_complete/analytics.py   pizza / radar profiles, team style
wa_complete/exports.py     PDF, Excel, CSV, JSON download bar
wa_complete/views/         one module per page
```
