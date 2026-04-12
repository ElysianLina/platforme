"""
ljspeech_cefr_filter.py
══════════════════════════════════════════════════════════════════════
Pipeline de filtrage CEFR pour LJSpeech-1.1 (chemin Windows personnalisé).
Place ce fichier dans backend/scripts/
"""

import os
import re
import sys
import csv
import json
import tarfile
import argparse
import io
from pathlib import Path
from collections import Counter

# ══════════════════════════════════════════════════════════════════
#  CHEMIN VERS TON DATASET (MODIFIE ICI SI BESOIN)
# ══════════════════════════════════════════════════════════════════

TAR_PATH = r"C:\Users\HP\Desktop\PFE Master Document\DATASets\data_moi\audio\LJSpeech-1.1.tar.bz2"
OUTPUT_DIR = r"C:\Users\HP\Desktop\PFE Master Document\DATASets\data_moi\audio\output_ljspeech_filtered"
TARGET_LEVELS = ["A1"]
MAX_EXAMPLES = None

# ══════════════════════════════════════════════════════════════════
#  IMPORT CEFR DETECTOR + CONFIGURATION DES CHEMINS
# ══════════════════════════════════════════════════════════════════

# Déterminer les chemins corrects
scripts_dir = Path(__file__).parent           # backend/scripts/
backend_dir = scripts_dir.parent              # backend/
data_dir = backend_dir / "data"               # backend/data/

print(f"📁 Scripts dir : {scripts_dir}")
print(f"📁 Backend dir : {backend_dir}")
print(f"📁 Data dir    : {data_dir}")

sys.path.insert(0, str(scripts_dir))  # Pour importer cefr_detector_v2

try:
    from cefr_detector_v2 import CefrDetector
    print("✅ cefr_detector_v2.py importé avec succès")
except ImportError as e:
    print(f"❌ Impossible d'importer cefr_detector_v2.py : {e}")
    sys.exit(1)


def preprocess_text(text: str) -> str:
    """Nettoie le texte avant détection CEFR."""
    if not text:
        return text
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u02bc', "'").replace('\u0060', "'")
    text = re.sub(r"(\w)'(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_metadata_from_tar(tar_path: str, max_examples: int = None) -> list[dict]:
    """Lit metadata.csv depuis l'archive TAR."""
    tar_path = Path(tar_path)
    
    if not tar_path.exists():
        print(f"\n❌ Fichier introuvable : {tar_path}")
        parent = tar_path.parent
        if parent.exists():
            print(f"\n🔍 Contenu de {parent} :")
            for f in parent.iterdir():
                size = f.stat().st_size / (1024**3) if f.is_file() else 0
                print(f"     {'📁' if f.is_dir() else '📄'} {f.name}" + 
                      (f" ({size:.2f} Go)" if f.is_file() else ""))
        sys.exit(1)

    print(f"\n📦 Archive : {tar_path.name}")
    print(f"   Taille : {tar_path.stat().st_size / (1024**3):.2f} Go")

    records = []
    metadata_file = "LJSpeech-1.1/metadata.csv"

    with tarfile.open(tar_path, "r:bz2") as tar:
        try:
            member = tar.getmember(metadata_file)
        except KeyError:
            candidates = [m for m in tar.getmembers() if m.name.endswith("metadata.csv")]
            if not candidates:
                print("❌ metadata.csv introuvable")
                sys.exit(1)
            member = candidates[0]

        f = tar.extractfile(member)
        content = f.read().decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(content), delimiter="|")

        for i, row in enumerate(reader):
            if max_examples and i >= max_examples:
                break
            if len(row) < 2:
                continue
            records.append({
                "id": row[0].strip(),
                "text": row[2].strip() if len(row) >= 3 else row[1].strip(),
                "text_raw": row[1].strip(),
            })

    print(f"✅ {len(records):,} entrées lues")
    return records


def detect_and_filter(records: list[dict], detector: CefrDetector,
                      target_levels: list[str]) -> list[dict]:
    """Détecte CEFR et filtre."""
    total = len(records)
    print(f"\n🔍 Analyse CEFR de {total:,} textes...")

    for i, record in enumerate(records):
        text = preprocess_text(record["text"])
        record["cefr"] = detector.detect(text)
        if (i + 1) % 500 == 0 or (i + 1) == total:
            print(f"   Progression : {i+1:,}/{total:,} ({(i+1)/total*100:.0f}%)", end="\r")
    print()

    dist = Counter(r["cefr"] for r in records)
    print("\n📊 Distribution CEFR :")
    for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        n = dist.get(lvl, 0)
        pct = n / total * 100 if total else 0
        print(f"   {lvl} : {pct:5.1f}% ({n:,})")

    filtered = [r for r in records if r["cefr"] in target_levels]
    print(f"\n✅ Gardés ({target_levels}) : {len(filtered):,} ({len(filtered)/total*100:.1f}%)")
    return filtered


def extract_audios(tar_path: str, filtered: list[dict], output_dir: str):
    """Extrait les fichiers .wav filtrés."""
    id_to_cefr = {r["id"]: r["cefr"] for r in filtered}
    total = len(id_to_cefr)

    audio_base = Path(output_dir) / "audio"
    for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        (audio_base / lvl).mkdir(parents=True, exist_ok=True)

    print(f"\n🔊 Extraction de {total:,} audio...")
    extracted = 0
    id_to_path = {}

    with tarfile.open(tar_path, "r:bz2") as tar:
        for member in tar:
            if not member.name.endswith(".wav"):
                continue
            
            audio_id = Path(member.name).stem
            if audio_id not in id_to_cefr:
                continue

            cefr = id_to_cefr[audio_id]
            out_path = audio_base / cefr / f"{audio_id}.wav"

            f = tar.extractfile(member)
            if f:
                with open(out_path, "wb") as out_f:
                    out_f.write(f.read())
                id_to_path[audio_id] = str(out_path)
                extracted += 1

            if extracted % 50 == 0 or extracted == total:
                print(f"   ✅ {extracted}/{total}", end="\r")
            
            if extracted >= total:
                break

    print(f"\n✅ {extracted} audio extraits dans : {audio_base}")
    return id_to_path


def save_results(filtered: list[dict], output_dir: str, 
                 target_levels: list[str], id_to_path: dict = None):
    """Sauvegarde JSON + CSV."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    levels_str = "_".join(target_levels)

    records = []
    for r in filtered:
        rec = {
            "id": r["id"],
            "text": r["text"],
            "text_raw": r["text_raw"],
            "cefr": r["cefr"],
        }
        if id_to_path and r["id"] in id_to_path:
            rec["audio_path"] = id_to_path[r["id"]]
        records.append(rec)

    # JSON
    json_path = out / f"ljspeech_{levels_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON : {json_path}")

    # CSV
    csv_path = out / f"ljspeech_{levels_str}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"💾 CSV  : {csv_path}")

    # Résumé
    summary = out / f"summary_{levels_str}.txt"
    dist = Counter(r["cefr"] for r in records)
    with open(summary, "w") as f:
        f.write(f"Dataset : LJSpeech-1.1\nNiveaux : {target_levels}\n")
        f.write(f"Total   : {len(records):,}\n\nDistribution :\n")
        for lvl, n in sorted(dist.items()):
            f.write(f"  {lvl} : {n:,}\n")
    print(f"💾 Résumé : {summary}")


def main():
    parser = argparse.ArgumentParser(description="Filtre LJSpeech par CEFR")
    parser.add_argument("--tar", default=TAR_PATH)
    parser.add_argument("--levels", nargs="+", default=TARGET_LEVELS)
    parser.add_argument("--output", default=OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Analyse sans extraction")
    parser.add_argument("--max", type=int, default=MAX_EXAMPLES)
    parser.add_argument("--vocab-dir", default=str(data_dir))  # Utilise backend/data/
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════╗")
    print("║     LJSpeech-1.1  ×  CEFR Filter                      ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"Archive  : {args.tar}")
    print(f"Niveaux  : {args.levels}")
    print(f"Sortie   : {args.output}")
    print(f"Vocab    : {args.vocab_dir}")

    if not Path(args.tar).exists():
        print(f"\n❌ Fichier non trouvé : {args.tar}")
        sys.exit(1)

    # Vérifier que le dossier vocab existe
    vocab_path = Path(args.vocab_dir)
    if not vocab_path.exists():
        print(f"\n❌ Dossier vocabulaire introuvable : {vocab_path}")
        print(f"   Crée-le ou vérifie le chemin.")
        sys.exit(1)

    # Vérifier les fichiers vocabulaire
    required_files = ['word_vocabulary_a1.json', 'word_vocabulary_a2.json', 
                      'word_vocabulary_b1.json', 'word_vocabulary_b2.json', 
                      'word_vocabulary_c1.json']
    missing = [f for f in required_files if not (vocab_path / f).exists()]
    if missing:
        print(f"\n⚠️  Fichiers vocabulaire manquants :")
        for f in missing:
            print(f"   - {f}")
        print(f"\n   Attendus dans : {vocab_path}")

    # Exécution
    detector = CefrDetector(vocab_dir=args.vocab_dir)
    records = load_metadata_from_tar(args.tar, max_examples=args.max)
    
    if not records:
        print("❌ Aucune donnée trouvée")
        return

    filtered = detect_and_filter(records, detector, args.levels)
    
    if not filtered:
        print(f"⚠️  Aucun résultat pour {args.levels}")
        return

    print(f"\n─── Exemples {args.levels[0]} ───")
    for r in filtered[:3]:
        print(f"\nID  : {r['id']}")
        print(f"Text: {r['text'][:100]}...")

    id_to_path = {}
    if not args.dry_run:
        id_to_path = extract_audios(args.tar, filtered, args.output)
    else:
        print("\nℹ️  Dry-run : pas d'extraction audio")

    save_results(filtered, args.output, args.levels, id_to_path)
    print(f"\n✅ Terminé ! Résultats dans : {Path(args.output).absolute()}")


if __name__ == "__main__":
    main()



# statistique 
# python sps_corpus_cefr_filter.py --levels A1 --max 20
# extraction A1et A2 
# python sps_corpus_cefr_filter.py --levels A1 A2