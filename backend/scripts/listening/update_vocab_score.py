"""
update_vocab_score.py
=====================
Met à jour la colonne vocab_score de ListeningAudio à partir du fichier a1_coverage_results.json

Usage:
    cd backend/scripts/listening
    python update_vocab_score.py
"""

import os
import sys
import json
from pathlib import Path

# Configuration Django
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_prj.settings')
import django
django.setup()

from users.models import ListeningAudio

# Chemin du fichier de résultats (dans data/listening/)
RESULTS_FILE = BACKEND_DIR / "data" / "listening" / "a1_coverage_results.json"


def main():
    print("=" * 70)
    print("MISE À JOUR DES VOCAB_SCORE DANS LISTENINGAUDIO")
    print("=" * 70)
    print()

    # Vérifier que le fichier existe
    if not RESULTS_FILE.exists():
        print(f"❌ Fichier non trouvé: {RESULTS_FILE}")
        print(f"   Vérifiez que le fichier existe dans: data/listening/")
        return

    # Charger les résultats
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"📊 {len(results)} résultats chargés depuis:")
    print(f"   {RESULTS_FILE}")
    print()

    updated = 0
    not_found = []

    for item in results:
        audio_id = item['audio_id']
        vocab_score = item['a1_coverage_percent']

        try:
            audio = ListeningAudio.objects.get(audio_id=audio_id)
            audio.vocab_score = vocab_score
            audio.save(update_fields=['vocab_score'])
            updated += 1
            print(f"✅ [{audio_id}] vocab_score = {vocab_score}%")
        except ListeningAudio.DoesNotExist:
            not_found.append(audio_id)
            print(f"❌ [{audio_id}] Audio non trouvé dans la base")

    print()
    print("=" * 70)
    print("RÉSULTAT")
    print("=" * 70)
    print(f"   ✅ Mis à jour: {updated}/{len(results)}")
    if not_found:
        print(f"   ❌ Non trouvés: {len(not_found)}")
        for aid in not_found:
            print(f"      - {aid}")
    print("=" * 70)


if __name__ == "__main__":
    main()
