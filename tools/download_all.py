import subprocess, sys
import json
import shutil
import time
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
APPROOT = BASE.parent
DATA = APPROOT / "data"
SOURCE = DATA / "source"
DOWN = BASE / "download_regeling.py"

REGULATIONS = [
    ("OW",  "BWBR0037885", "omgevingswet.xml"),
    ("BAL", "BWBR0041330", "bal.xml"),
    ("BBL", "BWBR0041297", "bbl.xml"),
    ("BKL", "BWBR0041313", "bkl.xml"),
    ("OB",  "BWBR0041278", "ob.xml"),
    ("OR",  "BWBR0045528", "or.xml"),
]

# Iedere build gebruikt de dag van uitvoeren als peildatum. Daardoor haalt de
# dagelijkse Pages-controle steeds de op dat moment geldende BWB-tekst op.
PEILDATUM = date.today().isoformat()

if not DOWN.exists():
    print(f"FOUT: downloader ontbreekt: {DOWN}")
    raise SystemExit(1)
SOURCE.mkdir(parents=True, exist_ok=True)
VERSION_FILE = DATA / "regulation_versions.json"

def load_versions():
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": 1, "regulations": {}}

def official_version_date(xml_file):
    """Return the official state date advertised by the downloaded BWB XML."""
    try:
        root = ET.parse(xml_file).getroot()
        value = root.attrib.get("inwerkingtreding", "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        source = root.attrib.get("bwb-ng-vast-deel", "")
        match = re.search(r"/(\d{4}-\d{2}-\d{2})/", source)
        return match.group(1) if match else None
    except (OSError, ET.ParseError):
        return None

versions = load_versions()
versions.setdefault("schema_version", 1)
versions.setdefault("regulations", {})

failed = []
reused = []
for rid, bwb, filename in REGULATIONS:
    target = SOURCE / filename
    print()
    print(f"[{rid}] API ophalen")
    print(f"  BWB-ID: {bwb}")
    print(f"  Peildatum: {PEILDATUM}")
    print(f"  Doel: {target}")
    cmd = [sys.executable, str(DOWN), bwb, PEILDATUM, str(target)]
    print("  Opdracht:", " ".join(f'"{x}"' if " " in x else x for x in cmd))
    rc = 1
    for attempt in range(1, 4):
        print(f"  Poging {attempt}/3...")
        rc = subprocess.call(cmd, cwd=str(BASE))
        if rc == 0:
            break
        if attempt < 3:
            print(f"  Tijdelijke API-fout voor {rid}; opnieuw proberen...")
            time.sleep(2)
    if rc != 0:
        # The downloader deliberately leaves an existing XML untouched on a
        # transient network failure. Reuse that file in this same single pass
        # instead of aborting and forcing the user to run start.bat again.
        if target.exists() and target.stat().st_size > 0:
            try:
                head = target.read_bytes()[:200000]
                usable = bwb.encode('ascii') in head
            except Exception:
                usable = False
            if usable:
                reused.append(rid)
                print(f"  WAARSCHUWING: API {rid} code {rc}; bestaand XML-bestand blijft behouden en wordt gebruikt.")
                continue
        failed.append((rid, rc))
        print(f"  FOUT: {rid} code {rc}; geen bruikbaar bestaand XML-bestand beschikbaar.")
    else:
        if not target.exists() or target.stat().st_size == 0:
            failed.append((rid, 3))
            print(f"  FOUT: XML niet aangemaakt: {target}")
        else:
            print(f"  GESLAAGD: {target}")
            previous = versions["regulations"].get(rid, {})
            versions["regulations"][rid] = {
                "imported_on": PEILDATUM,
                "official_version_date": official_version_date(target) or previous.get("official_version_date"),
                "bwb_id": bwb,
            }

print()
if reused:
    print("Bestaande XML-bestanden hergebruikt na tijdelijke API-fout:", ", ".join(reused))
if failed:
    print("API-ophalen mislukt en geen bruikbare XML beschikbaar voor:", ", ".join(f"{r}(code {c})" for r,c in failed))
    raise SystemExit(1)

# De datum is alleen de datum waarop deze officiële bron met succes is opgehaald.
# Bij een tijdelijke fout blijft de eerder bekende datum van een hergebruikt bestand staan.
VERSION_FILE.write_text(json.dumps(versions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Versieoverzicht bijgewerkt:", VERSION_FILE)

print("Downloadfase voltooid in één enkele cyclus (maximaal 3 pogingen per regeling).")
