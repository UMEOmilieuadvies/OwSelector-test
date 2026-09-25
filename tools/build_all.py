#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

BASE = Path(__file__).resolve().parent
APPROOT = BASE.parent
DATA = APPROOT / "data"
SOURCE = DATA / "source"
GRAPH = DATA / "graph"

REGS = [
    ("OW",  "BWBR0037885", "omgevingswet", "ow"),
    ("BAL", "BWBR0041330", "bal", "bal"),
    ("BBL", "BWBR0041297", "bbl", "bbl"),
    ("BKL", "BWBR0041313", "bkl", "bkl"),
    ("OB",  "BWBR0041278", "ob", "ob"),
    ("OR",  "BWBR0045528", "or", "or"),
]

PARSER = BASE / "bwb_parser.py"
EXTERNAL_REFS = BASE / "build_external_refs.py"
BACK_REFERENCES = BASE / "build_back_references.py"
VERIFY_EXTERNAL_REFERENCES = BASE / "verify_external_references.py"
VERIFY_TABLE_LAYOUTS = BASE / "verify_table_layouts.py"

def log(msg):
    print(msg, flush=True)

def main():
    if not PARSER.exists():
        print("FOUT: parser ontbreekt:", PARSER)
        return 1

    ok = True
    built = 0
    missing = []
    for label, bwb, xmlstem, graphstem in REGS:
        xml = SOURCE / f"{xmlstem}.xml"
        graph = GRAPH / f"{graphstem}_legal_graph.json"
        log(f"[{label}] XML: {xml}")
        log(f"[{label}] GRAPH: {graph}")

        if not xml.exists():
            log(f"[{label}] WAARSCHUWING: XML ontbreekt; regeling wordt deze cyclus overgeslagen")
            missing.append(label)
            continue

        try:
            first = xml.read_bytes()[:200000]
            if bwb.encode() not in first and bwb not in xml.read_text(encoding="utf-8", errors="ignore")[:200000]:
                log(f"[{label}] WAARSCHUWING: BWB-id niet aangetroffen in XML-kop")
        except Exception as e:
            log(f"[{label}] FOUT XML-controle: {e}")
            ok = False
            continue

        cmd = [sys.executable, str(PARSER), str(xml), str(graph)]
        log(f"[{label}] Parse gestart")
        r = subprocess.run(cmd, cwd=BASE)
        if r.returncode != 0:
            log(f"[{label}] FOUT parser exitcode={r.returncode}")
            ok = False
            continue

        if not graph.exists():
            log(f"[{label}] FOUT: graph niet aangemaakt")
            ok = False
            continue

        try:
            obj = json.loads(graph.read_text(encoding="utf-8"))
            actual = obj.get("bwb_id")
            if actual and actual != bwb:
                log(f"[{label}] FOUT BWB-ID graph={actual}, verwacht={bwb}")
                ok = False
                continue
            gs = obj.get("glossary_stats") or {}
            count = int(gs.get("count") or 0)
            if label == "BAL":
                controls = gs.get("control_terms") or {}
                if not gs.get("appendix_found") or not gs.get("section_a_found") or count < 100 or not all(controls.values()):
                    log(f"[BAL] FOUT begrippenlijst onvolledig: count={count}, appendix={gs.get('appendix_found')}, onderdeel_A={gs.get('section_a_found')}, controls={controls}")
                    ok = False
                    continue
                log(f"[BAL] Begrippenlijst gecontroleerd: {count} begrippen, Bijlage I onderdeel A")
            else:
                log(f"[{label}] Begrippenlijst: {count} begrippen (methode={gs.get('method','geen')})")
            log(f"[{label}] GESLAAGD: {graph.name} bytes={graph.stat().st_size}")
            built += 1
        except Exception as e:
            log(f"[{label}] FOUT graph-validatie: {e}")
            ok = False

    if ok and built == len(REGS):
        result = subprocess.run([sys.executable, str(EXTERNAL_REFS)], cwd=BASE)
        if result.returncode != 0:
            log("FOUT extern-verwijzingenregister kon niet worden gebouwd.")
            return 1
        result = subprocess.run([sys.executable, str(BACK_REFERENCES)], cwd=BASE)
        if result.returncode != 0:
            log("FOUT terugverwijzingenregister kon niet worden gebouwd.")
            return 1
        result = subprocess.run([sys.executable, str(VERIFY_EXTERNAL_REFERENCES)], cwd=BASE)
        if result.returncode != 0:
            log("FOUT EU-verwijzingen konden niet volledig worden gecontroleerd.")
            return 1
        result = subprocess.run([sys.executable, str(VERIFY_TABLE_LAYOUTS)], cwd=BASE)
        if result.returncode != 0:
            log("FOUT tabelstructuur kon niet volledig worden gecontroleerd.")
            return 1
        log("ALLE ZES REGELINGEN ZIJN GEBOUWD.")
        return 0
    if built > 0:
        log(f"GEDEELDE BUILD GEREED: {built}/{len(REGS)} regelingen beschikbaar.")
        if missing:
            log("Tijdelijk niet beschikbaar:", ", ".join(missing))
        return 0
    log("GEEN REGELINGEN BESCHIKBAAR; build kan niet worden voortgezet.")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
