import hashlib
import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://zstib.edu.pl/plan-lekcji"
STATE_FILE = Path("state.json")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "").strip()
TEST_NOTIFICATION = os.environ.get("TEST_NOTIFICATION", "false").lower() == "true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ZSTiB-Plan-Monitor/1.0; "
        "+https://github.com/)"
    )
}


def fetch_plan():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Usuwamy elementy, które nie są treścią planu.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    # Szukamy widocznej na stronie daty aktualizacji planu.
    match = re.search(
        r"data\s+aktualizacji\s+planu\s*:\s*"
        r"(\d{1,2}\.\d{1,2}\.\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    update_date = match.group(1) if match else "nieznana"

    # Hashujemy oczyszczoną treść strony planu.
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {
        "hash": content_hash,
        "update_date": update_date,
    }


def load_state():
    if not STATE_FILE.exists():
        return None

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def send_discord(old_state, new_state):
    if not WEBHOOK:
        print("Brak DISCORD_WEBHOOK - nie mogę wysłać powiadomienia.")
        return

    old_date = old_state.get("update_date", "nieznana")

    payload = {
        "username": "ZSTiB Plan Monitor",
        "content": (
            "🚨 **Wykryto zmianę planu lekcji ZSTiB!**\n"
            f"📅 Poprzednia data aktualizacji: **{old_date}**\n"
            f"📅 Nowa data aktualizacji: **{new_state['update_date']}**\n"
            f"🔗 {URL}"
        ),
    }

    response = requests.post(WEBHOOK, json=payload, timeout=30)
    response.raise_for_status()


def main():
    if TEST_NOTIFICATION:
        if not WEBHOOK:
            print("Brak DISCORD_WEBHOOK - nie mogę wysłać testu.", file=sys.stderr)
            sys.exit(1)

        payload = {
            "username": "ZSTiB Plan Monitor",
            "content": (
                "✅ **Test monitora ZSTiB działa!**\n"
                "Jeśli widzisz tę wiadomość, Discord webhook i GitHub Actions są poprawnie skonfigurowane.\n"
                f"🔗 {URL}"
            ),
        }

        response = requests.post(WEBHOOK, json=payload, timeout=30)
        response.raise_for_status()
        print("Testowe powiadomienie wysłane.")
        return

    try:
        new_state = fetch_plan()
    except Exception as exc:
        print(f"Błąd pobierania planu: {exc}", file=sys.stderr)
        sys.exit(1)

    old_state = load_state()

    if old_state is None:
        print(
            "Pierwsze uruchomienie. "
            f"Zapamiętuję plan (data: {new_state['update_date']})."
        )
        save_state(new_state)
        return

    if old_state.get("hash") == new_state["hash"]:
        print(
            "Brak zmian. "
            f"Data aktualizacji planu: {new_state['update_date']}"
        )
        return

    print(
        "WYKRYTO ZMIANĘ: "
        f"{old_state.get('update_date', 'nieznana')} -> "
        f"{new_state['update_date']}"
    )

    send_discord(old_state, new_state)
    save_state(new_state)


if __name__ == "__main__":
    main()
