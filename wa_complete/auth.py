"""Login page with salted PBKDF2 password hashes from st.secrets and an optional 30-day cookie.

Secrets (.streamlit/secrets.toml locally, the Secrets box on Streamlit Cloud):

    [auth]
    cookie_key = "<64 hex characters>"          # signs the login cookie
    [auth.users.Marc]
    salt = "<hex>"
    hash = "<hex>"                              # pbkdf2_hmac("sha256", password, salt, 310000)

Make a hash: python -m wa_complete.auth "<password>"
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sys
import time

import streamlit as st

COOKIE = "wa_auth"
ITER = 310_000
KEEP_DAYS = 30


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITER).hex()


def _cfg():
    try:
        return st.secrets["auth"]
    except Exception:
        return None


def _users() -> dict:
    cfg = _cfg()
    return {k: dict(v) for k, v in (cfg.get("users") or {}).items()} if cfg else {}


def _check(username: str, password: str) -> str | None:
    for name, u in _users().items():
        if name.lower() == username.strip().lower():
            _, h = hash_password(password, u["salt"])
            return name if hmac.compare_digest(h, u["hash"]) else None
    hash_password(password)            # same work for unknown users (no timing hint)
    return None


def _sign(body: str) -> str:
    return hmac.new(_cfg()["cookie_key"].encode(), body.encode(), hashlib.sha256).hexdigest()


def _token(user: str, seconds: int) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"u": user, "exp": int(time.time()) + seconds}).encode()).decode()
    return f"{body}.{_sign(body)}"


def _verify(token: str | None) -> str | None:
    try:
        body, sig = token.split(".")
        if not hmac.compare_digest(sig, _sign(body)):
            return None
        d = json.loads(base64.urlsafe_b64decode(body.encode()))
        return d["u"] if d["exp"] > time.time() and d["u"] in _users() else None
    except Exception:
        return None


def _set_cookie(value: str, max_age: int | None):
    """Write the cookie on the app's own page (component iframes share its origin)."""
    import streamlit.components.v1 as components
    age = "" if max_age is None else f"; max-age={max_age}"
    components.html(f"""<script>
      const p = window.parent;
      const sec = p.location.protocol === "https:" ? "; Secure" : "";
      p.document.cookie = "{COOKIE}={value}; path=/{age}; SameSite=Lax" + sec;
    </script>""", height=0)


def logout():
    st.session_state.pop("user", None)
    st.session_state.logged_out = True              # the old cookie is still in this connection's headers
    st.session_state["cookie_action"] = ("", 0)


def require_login(T: dict) -> str:
    """Returns the logged-in user, or draws the login page and stops the script."""
    if _cfg() is None or not _users():
        st.error("Login is not configured: add [auth] to the app's secrets (see wa_complete/auth.py).")
        st.stop()
    if st.session_state.get("cookie_action") is not None:      # set / clear the cookie on this run, once
        value, age = st.session_state.pop("cookie_action")
        _set_cookie(value, age)
    user = st.session_state.get("user")
    if not user and st.session_state.get("logged_out") is not True:
        user = _verify(st.context.cookies.get(COOKIE))
        if user:
            st.session_state.user = user
    if user:
        return user

    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'] { display: none; }</style>",
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.write("")
        st.write("")
        st.markdown("<div class='wa-eyebrow'>Waltzing Analytics · xDanger</div>", unsafe_allow_html=True)
        st.markdown("## Match Hub 26-27")
        st.markdown("<div class='wa-muted'>Eredivisie · Jupiler Pro League · Bundesliga · 2. Bundesliga · 3. Liga · "
                    "Regionalligen</div>", unsafe_allow_html=True)
        st.write("")
        with st.form("login", border=True):
            name = st.text_input("Username", autocomplete="username")
            pw = st.text_input("Password", type="password", autocomplete="current-password")
            keep = st.checkbox(f"Keep me logged in for {KEEP_DAYS} days", value=True)
            ok = st.form_submit_button("Log in", type="primary", width="stretch")
        if ok:
            who = _check(name, pw)
            if who:
                st.session_state.user = who
                st.session_state.logged_out = False
                age = KEEP_DAYS * 86400 if keep else None
                st.session_state["cookie_action"] = (_token(who, age or 12 * 3600), age)
                st.rerun()
            else:
                time.sleep(1.0)
                st.error("Wrong username or password.")
        st.caption("Data: IMPECT, Opta, StatsBomb, SkillCorner, Transfermarkt · Models: Waltzing Analytics")
    st.stop()


if __name__ == "__main__":         # python -m wa_complete.auth "<password>"
    s, h = hash_password(sys.argv[1])
    print(f'salt = "{s}"\nhash = "{h}"')
