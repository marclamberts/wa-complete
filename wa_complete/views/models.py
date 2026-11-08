import streamlit as st


def render(p, T, lg):
    st.markdown(f"""
### The models behind the app

Everything runs on IMPECT event data and the Waltzing Analytics xDanger models. The models were trained on the 2024 to
2025-26 IMPECT seasons, so 2026-27 is out of sample. Every number is computed inside one league: leagues are never mixed.

**xDanger family (every report)**
- **xDanger**: how dangerous the next 15 seconds are for the team on the ball (the most dangerous moment it is expected
  to reach, as a goal probability). Credited to players as xDanger added, won (regains), denied (defending) and received.
- **xG (Model 1)**, **xGOT** and **xShot** (chance of a shot within 15 seconds).
- **Restart pillars**: every restart is followed for 30 seconds and scored on reach danger, peak xShot, xG, goal, another
  set piece, retention, dominance, second ball and goal against, then compared with the league per restart option.

**Models 2 to 5 (match ratings and scouting)**
- **Model 2, possession value** and **Model 3, conceding value**: net value = Model 2 minus Model 3, per action.
- **Model 4, xPass**: completion probability of every delivery; xPass +/100 = completed above expected per 100 passes.
- **Model 5, match rating**: 0 to 10, 6.5 = position average.

**Pre-match probabilities**: Poisson on a 60/40 blend of non-penalty xG and xDanger (rescaled to xG), attack times
opponent defence, with the league's home and away rates.

**Pizza and deviation radar**: percentiles and standard deviations against the same position group in the same league
({450}+ minutes).

**Other providers**: Opta (WTV), StatsBomb (OBV, aerials, height), SkillCorner (top speed, high-intensity distance) and
Transfermarkt (market value, contract) come from the WA Scouting DB 26-27, matched to IMPECT players by id.

**This league**: {p['name']}, {p['n_played']} matches, {p['n_actions']:,} actions, Models 2 to 5
{'included' if p.get('models5') else 'not available'}. Data updated {(p.get('updated') or '').replace('T', ' ')} by the
WA Match Hub daily agent.
""")
