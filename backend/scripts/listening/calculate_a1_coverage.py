"""
CALCULATE_A1_COVERAGE.PY - Version corrigée avec bons chemins
===========================================================
Ce script est dans: backend/scripts/listening/
Les données sont dans: backend/data/
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

# Chemin absolu du dossier courant (où est ce script)
SCRIPT_DIR = Path(__file__).parent

# Remonter de 2 niveaux: scripts/listening/ → scripts/ → backend/
BACKEND_DIR = SCRIPT_DIR.parent.parent

# Chemin vers les données
DATA_DIR = BACKEND_DIR / "data"
LISTENING_DIR = DATA_DIR / "listening"

# Fichiers
VOCAB_FILE = DATA_DIR / "word_vocabulary_a1.json"
AUDIO_ASSIGNMENTS_FILE = LISTENING_DIR / "ljspeech_subunit_assignments.json"
OUTPUT_FILE = LISTENING_DIR / "a1_coverage_results.json"

print(f"📁 Script location: {SCRIPT_DIR}")
print(f"📁 Backend location: {BACKEND_DIR}")
print(f"📁 Data location: {DATA_DIR}")
print(f"📄 Vocab file: {VOCAB_FILE}")
print(f"📄 Audio assignments: {AUDIO_ASSIGNMENTS_FILE}")
print()

# ============================================
# CHARGEMENT DU VOCABULAIRE A1
# ============================================

def load_vocabulary():
    """Charge le vocabulaire A1 depuis le fichier JSON."""
    try:
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        vocab_a1 = set([word.lower() for word in vocab_data['A1']])
        print(f"✅ Vocabulaire A1 chargé: {len(vocab_a1)} mots")
        return vocab_a1
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier non trouvé: {VOCAB_FILE}")
        print(f"   Vérifiez que le fichier existe dans: {DATA_DIR}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        raise

# ============================================
# ALGORITHME DE CALCUL A1
# ============================================

def normalize_word(word, vocab_a1):
    """Normalise un mot pour matcher le vocabulaire (lemmatisation simple)."""
    # Enlever les possessifs
    if word.endswith("'s"):
        word = word[:-2]
    if word.endswith("'"):
        word = word[:-1]

    # Gérer les pluriels simples
    if word.endswith('s') and len(word) > 3:
        singular = word[:-1]
        if singular in vocab_a1:
            return singular

    # Gérer les -ing
    if word.endswith('ing') and len(word) > 5:
        base = word[:-3]
        if base in vocab_a1:
            return base
        if base + 'e' in vocab_a1:
            return base + 'e'

    # Gérer les -ed
    if word.endswith('ed') and len(word) > 4:
        base = word[:-2]
        if base in vocab_a1:
            return base
        if base + 'e' in vocab_a1:
            return base + 'e'

    return word


def calculate_a1_coverage(transcript, vocab_a1, smoothing_factor=0.15):
    """
    Calcule le score de couverture A1 avec smoothing naturel.

    Args:
        transcript: Texte à analyser
        vocab_a1: Set de mots du vocabulaire A1
        smoothing_factor: Facteur de lissage (défaut: 0.15 = 15%)

    Returns:
        dict avec les métriques de couverture
    """
    # Tokenisation
    words_raw = re.findall(r"[a-z']+", transcript.lower())

    if not words_raw:
        return None

    # Normalisation
    normalized_words = [normalize_word(w, vocab_a1) for w in words_raw]

    # Mots fréquents avec poids différents
    high_freq = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'for', 'with'}
    medium_freq = {'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'}

    # Calcul pondéré
    a1_weighted = 0
    total_weight = 0

    for word in normalized_words:
        if word in high_freq:
            weight = 1.5
        elif word in medium_freq:
            weight = 1.3
        elif len(word) <= 3 and word in vocab_a1:
            weight = 1.2
        else:
            weight = 1.0

        if word in vocab_a1:
            a1_weighted += weight
        total_weight += weight

    # Smoothing bayésien
    pseudo_count = smoothing_factor * len(normalized_words)
    adjusted_a1 = a1_weighted + pseudo_count
    adjusted_total = total_weight + 2 * pseudo_count

    coverage = (adjusted_a1 / adjusted_total) * 100

    # Stats brutes
    a1_words = [w for w in normalized_words if w in vocab_a1]
    non_a1_words = list(set([w for w in normalized_words if w not in vocab_a1]))

    return {
        'total_words': len(normalized_words),
        'a1_words_count': len(a1_words),
        'a1_coverage_percent': round(coverage, 2),
        'raw_coverage': round((len(a1_words) / len(normalized_words)) * 100, 2),
        'a1_words_found': list(set(a1_words)),
        'non_a1_words': non_a1_words[:10]
    }


# ============================================
# FONCTION PRINCIPALE
# ============================================

def main():
    """Fonction principale."""
    print("=" * 70)
    print("CALCUL DU SCORE DE COUVERTURE VOCABULAIRE A1")
    print("=" * 70)
    print()

    # 1. Charger le vocabulaire
    vocab_a1 = load_vocabulary()

    # 2. Charger les assignations audio
    try:
        with open(AUDIO_ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
            audio_assignments = json.load(f)
        print(f"✅ Assignations audio chargées: {len(audio_assignments)} entrées")
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier non trouvé: {AUDIO_ASSIGNMENTS_FILE}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        raise

    print()

    # 3. Calculer la couverture pour chaque audio
    results = []

    for audio in audio_assignments:
        transcript = audio.get('transcript', '')
        coverage_data = calculate_a1_coverage(transcript, vocab_a1)

        if coverage_data:
            result = {
                'audio_id': audio.get('audio_id', ''),
                'unit_number': audio.get('unit_number', ''),
                'unit_title': audio.get('unit_title', ''),
                'subunit_key': audio.get('subunit_key', ''),
                'subunit_title': audio.get('subunit_title', ''),
                'transcript': transcript,
                **coverage_data
            }
            results.append(result)

    # 4. Trier par score décroissant
    results_sorted = sorted(results, key=lambda x: x['a1_coverage_percent'], reverse=True)

    # 5. Afficher les statistiques
    print("📊 STATISTIQUES GLOBALES")
    print("-" * 70)
    coverages = [r['a1_coverage_percent'] for r in results]
    print(f"   Nombre d'audios analysés: {len(results)}")
    print(f"   Couverture moyenne A1: {sum(coverages)/len(coverages):.2f}%")
    print(f"   Couverture maximale: {max(coverages):.2f}%")
    print(f"   Couverture minimale: {min(coverages):.2f}%")
    print()

    # 6. Top 10
    print("🏆 TOP 10 - Meilleure couverture A1:")
    print("-" * 70)
    for i, r in enumerate(results_sorted[:10], 1):
        print(f"{i:2d}. [{r['audio_id']}] {r['a1_coverage_percent']:5.1f}% | "
              f"{r['a1_words_count']:2d}/{r['total_words']:2d} mots A1")
        print(f"    📝 {r['transcript'][:50]}...")
    print()

    # 7. Sauvegarder les résultats
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results_sorted, f, indent=2, ensure_ascii=False)

    print(f"✅ Résultats sauvegardés dans: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()