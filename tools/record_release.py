"""Registreer een geslaagde Pages-uitgave in Supabase."""
from __future__ import annotations

import json, os, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def release_notes(release: dict[str, object]) -> list[str]:
    """Geef de gebruikersnotities terug in het formaat van releases.notes.

    Oudere releases gebruikten direct ``notes``. Het huidige releaseformaat
    scheidt zichtbare gebruikerswijzigingen van technische beheernotities.
    De beheertabel bewaart bewust alleen de zichtbare lijst.
    """
    notes = release.get("user_notes", release.get("notes", []))
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        raise ValueError("release.json moet een lijst met gebruikersnotities bevatten.")
    return notes


def request(method: str, url: str, key: str, payload: object | None = None) -> None:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        # Een herstart van een workflow mag dezelfde versie bijwerken in plaats
        # van te mislukken op de unieke versiecode.
        "Prefer": "resolution=merge-duplicates",
    }
    if data:
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=30) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"Supabase gaf HTTP {response.status}")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Supabase gaf HTTP {error.code}: {error.read().decode('utf-8', 'replace')}") from error


def main() -> None:
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    record = {"version": release["version"], "release_kind": release["kind"], "published_at": release["released_at"] + "T00:00:00Z", "notes": release_notes(release), "commit_sha": os.environ.get("GITHUB_SHA", ""), "pages_url": os.environ.get("PAGES_URL", "")}
    request("POST", base + "/rest/v1/releases?on_conflict=version", key, record)
    ids = [str(item) for item in release.get("resolved_comment_ids", []) if str(item)]
    if ids:
        quoted = ",".join(urllib.parse.quote(item, safe="") for item in ids)
        request("PATCH", base + f"/rest/v1/comments?id=in.({quoted})", key, {"status": "Doorgevoerd", "resolved_in_version": release["version"], "resolved_at": release["released_at"] + "T00:00:00Z"})
    print(f"Versie {release['version']} geregistreerd.")


if __name__ == "__main__":
    main()
