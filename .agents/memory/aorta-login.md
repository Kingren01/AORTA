---
name: AORTA login system
description: How the login gate works in app.py and what credentials to use
---

The login gate lives in `show_login_page()` in `app.py` (just before `main()`).

**How it works:**
- Checks `st.session_state.logged_in` at the top of `main()`
- If False, calls `show_login_page()` then `st.stop()`
- Login validates against `os.environ.get("APP_USERNAME", "admin")` and `os.environ.get("APP_PASSWORD", "aorta2024")`
- "Sign Out" button in sidebar sets `logged_in = False` and reruns

**Why:** User asked for a login page as part of the Clinical Dark UI overhaul.

**How to apply:** To change default credentials, set `APP_USERNAME` and `APP_PASSWORD` in Replit Secrets. To remove login, delete the login gate block in `main()` (the 4 lines after "Login gate" comment).
