from . import league, models, penalties, post, pre, restarts, scouting, setpieces, spscout  # noqa: F401

PAGES = [  # key, label, module
    ("league", "League", league), ("pre", "Pre-match", pre), ("post", "Post-match", post),
    ("sp", "Set pieces", setpieces), ("rs", "Restarts", restarts), ("pen", "Penalties", penalties),
    ("scout", "Scouting", scouting), ("spscout", "Set-piece scouting", spscout), ("models", "Models", models),
]
