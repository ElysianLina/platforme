"""
generate_listening_questions_json.py
══════════════════════════════════════════════════════════════════════
Génère 10 questions par audio via Groq API et sauvegarde en JSON.
Ne touche PAS à la base de données.

Usage :
    cd backend/scripts/listening
    python generate_listening_questions_json.py
    python generate_listening_questions_json.py --limit 5 --dry-run
══════════════════════════════════════════════════════════════════════
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  groq non installé. pip install groq")

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv non installé. pip install python-dotenv")


# ─────────────────────────────────────────────────────────────────
# CHEMINS CONFIGURÉS
# ─────────────────────────────────────────────────────────────────

# Structure du projet :
#   platform/
#   └── backend/
#       ├── .env                    ← ici
#       ├── manage.py
#       └── scripts/
#           └── listening/
#               └── generate_listening_questions.py  ← ce fichier
#
# __file__.parent            = backend/scripts/listening/
# __file__.parent.parent     = backend/scripts/
# __file__.parent.parent.parent = backend/   ← .env est ici

SCRIPT_DIR  = Path(__file__).resolve().parent   # backend/scripts/listening/
BACKEND_DIR = SCRIPT_DIR.parent.parent           # backend/

def _find_env_file():
    candidates = [
        BACKEND_DIR / ".env",            # backend/.env        ← cas normal
        BACKEND_DIR.parent / ".env",     # platform/.env       ← fallback
        Path.cwd() / ".env",             # dossier de lancement
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

ENV_PATH = _find_env_file()

# Chemin d'entrée : fichier JSON avec les transcriptions
INPUT_PATH = "../../data/listening/ljspeech_subunit_assignments.json"

# Chemin de sortie : fichier JSON avec les questions générées
OUTPUT_PATH = "../../data/listening/listening_questions_generated.json"

# Délai entre les appels API (en secondes) pour éviter le rate limiting
DELAY_BETWEEN_CALLS = 30


def load_env():
    """Charge les variables d'environnement depuis le fichier .env.
    Affiche le chemin exact trouvé pour faciliter le debug.
    """
    if not DOTENV_AVAILABLE:
        print("⚠️  python-dotenv non disponible, utilisation des variables système")
        return

    if ENV_PATH and ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)
        print(f"✅ Fichier .env chargé : {ENV_PATH}")
    else:
        # Afficher tous les chemins essayés pour aider au debug
        print("❌ Fichier .env introuvable. Chemins essayés :")
        for p in [
            BACKEND_DIR / ".env",
            BACKEND_DIR.parent / ".env",
            Path.cwd() / ".env",
        ]:
            print(f"   {'✅' if p.exists() else '✗ '} {p.resolve()}")
        print("\n   → Solutions possibles :")
        print("     1. Place le .env dans backend/ (dossier de manage.py)")
        print("     2. Lance le script depuis backend/ : python scripts/listening/generate_listening_questions.py")
        print("     3. Exporte la variable manuellement : set GROQ_API_KEYY=ta_cle  (Windows)")
        print("                                         : export GROQ_API_KEYY=ta_cle  (Linux/Mac)")


def get_groq_api_key():
    """Récupère la clé API Groq.
    Cherche GROQ_API_KEYY en premier (nom dans ton .env),
    puis les variantes courantes en fallback.
    """
    # Priorité 1 : nom exact utilisé dans ton .env
    api_key = os.getenv("GROQ_API_KEYY")
    if api_key:
        return api_key

    # Priorité 2 : variantes courantes
    for var_name in ("GROQ_API_KEY", "GROQ_KEY", "GROQ"):
        api_key = os.getenv(var_name)
        if api_key:
            print(f"   ℹ️  Clé trouvée via {var_name} (pas GROQ_API_KEYY)")
            return api_key

    # Debug : lister toutes les variables GROQ_* présentes
    groq_vars = {k: v[:10] + "..." for k, v in os.environ.items() if "GROQ" in k.upper()}
    if groq_vars:
        print(f"   ℹ️  Variables GROQ_* trouvées dans l'environnement : {groq_vars}")
    else:
        print("   ❌ Aucune variable GROQ_* dans l'environnement.")
        print("      Vérifie que ton .env contient bien : GROQ_API_KEYY=gsk_...")

    return None


def call_groq(prompt, max_tokens=2000, retries=5):
    """Appelle l'API Groq avec LLama 3.3 70B et retry en cas d'erreur."""
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Clé API Groq non trouvée")
    
    client = Groq(api_key=api_key)
    
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un professeur d'anglais niveau A1. Tu réponds UNIQUEMENT en JSON valide, sans markdown, sans explication."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Invalid API Key" in error_msg:
                print(f"   ❌ Clé API invalide.")
                raise  # inutile de retenter
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                # Backoff exponentiel : 30s, 60s, 120s
                wait_time = 30 * (2 ** attempt)
                print(f"   ⚠️  Rate limit Groq — attente {wait_time}s (tentative {attempt+1}/{retries})...")
                time.sleep(wait_time)
            else:
                wait_time = 5 * (attempt + 1)
                print(f"   ⚠️  Erreur API (tentative {attempt+1}/{retries}): {e} — attente {wait_time}s")
                time.sleep(wait_time)

            if attempt == retries - 1:
                raise
    
    return None


def generate_prompt(transcript, unit_title, subunit_title, audio_id):
    """Crée le prompt pour Groq."""
    return f"""Génère EXACTEMENT 10 questions de compréhension orale niveau A1 pour cet audio.

CONTEXTE :
- Audio ID : "{audio_id}"
- Unité : "{unit_title}"
- Sous-unité : "{subunit_title}"
- Niveau : A1 (débutant, vocabulaire simple, phrases courtes)

TRANSCRIPTION AUDIO :
\"\"\"{transcript}\"\"\"

RÈGLES IMPORTANTES :
- Les 10 questions doivent être DIFFÉRENTES les unes des autres (pas de répétition de type ou de contenu similaire)
- Chaque question teste une compétence distincte
- Les 2 questions "mcq" (ordres 2 et 3) doivent porter sur des aspects différents de l'audio
- Les 2 questions "grammar" (ordres 7 et 8) doivent tester des règles grammaticales différentes
- Les 2 questions "vocabulary" (ordres 9 et 10) doivent porter sur des mots différents

FORMAT JSON EXACT :
{{
  "questions": [
    {{
      "order": 1,
      "type": "true_false",
      "question": "The text says that...",
      "choices": null,
      "answer": "False",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 2,
      "type": "mcq",
      "question": "What does the speaker do?",
      "choices": ["A. He eats breakfast", "B. He washes his face", "C. He goes to school", "D. He sleeps"],
      "answer": "B",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 3,
      "type": "mcq",
      "question": "Where does the action take place?",
      "choices": ["A. At home", "B. At school", "C. In a park", "D. At work"],
      "answer": "A",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 4,
      "type": "word_order",
      "question": "Put the words in the correct order:",
      "choices": ["morning", "I", "breakfast", "eat", "the"],
      "answer": "I eat breakfast in the morning",
      "target_word": null,
      "correct_order": ["I", "eat", "breakfast", "in", "the", "morning"]
    }},
    {{
      "order": 5,
      "type": "fill_blank",
      "question": "I ___ a student.",
      "choices": ["am", "is"],
      "answer": "am",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 6,
      "type": "synonym",
      "question": "What is the synonym of 'happy'?",
      "choices": null,
      "answer": "glad",
      "target_word": "happy",
      "correct_order": null
    }},
    {{
      "order": 7,
      "type": "grammar",
      "question": "She ___ to school every day.",
      "choices": ["A. go", "B. goes", "C. going", "D. gone"],
      "answer": "B",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 8,
      "type": "grammar",
      "question": "They ___ two children.",
      "choices": ["A. have", "B. has", "C. having", "D. had"],
      "answer": "A",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 9,
      "type": "vocabulary",
      "question": "What color is the sky?",
      "choices": ["A. Red", "B. Blue", "C. Green", "D. Yellow"],
      "answer": "B",
      "target_word": null,
      "correct_order": null
    }},
    {{
      "order": 10,
      "type": "vocabulary",
      "question": "How many days in a week?",
      "choices": ["A. Five", "B. Six", "C. Seven", "D. Eight"],
      "answer": "C",
      "target_word": null,
      "correct_order": null
    }}
  ]
}}

Réponds UNIQUEMENT avec le JSON dans un objet "questions"."""


def parse_questions(json_text, audio_id):
    """Parse et valide la réponse de Groq."""
    try:
        data = json.loads(json_text)
        questions = data.get("questions", [])
        
        for q in questions:
            q['audio_id'] = audio_id
        
        required_fields = ['order', 'type', 'question', 'answer']
        for q in questions:
            for field in required_fields:
                if field not in q:
                    raise ValueError(f"Champ manquant: {field}")
        
        return questions
        
    except json.JSONDecodeError as e:
        print(f"❌ Erreur parsing JSON pour {audio_id}: {e}")
        print(f"Texte reçu: {json_text[:300]}...")
        return None


def generate_questions_for_entry(entry, dry_run=False):
    """Génère les 10 questions pour une entrée audio."""
    audio_id = entry['audio_id']
    transcript = entry['transcript']
    unit_title = entry['unit_title']
    subunit_title = entry['subunit_title']
    
    print(f"\n🎵 {audio_id}")
    print(f"   Unit: {unit_title} / {subunit_title}")
    print(f"   Transcript: {transcript[:60]}...")
    
    if dry_run:
        print(f"   → [DRY RUN] Simulation")
        return [{
            "audio_id": audio_id,
            "order": i,
            "type": "true_false" if i == 1 else "mcq",
            "question": f"Question test {i}",
            "choices": ["A. opt1", "B. opt2", "C. opt3", "D. opt4"] if i > 1 else None,
            "answer": "A",
            "target_word": None,
            "correct_order": None
        } for i in range(1, 11)]
    
    prompt = generate_prompt(transcript, unit_title, subunit_title, audio_id)
    
    try:
        response = call_groq(prompt)
    except Exception as e:
        print(f"   ❌ Erreur API Groq après retries: {e}")
        return None
    
    if not response:
        print("   ❌ Réponse vide")
        return None
    
    questions = parse_questions(response, audio_id)
    if questions:
        print(f"   ✅ {len(questions)} questions générées")
    
    return questions


def main():
    parser = argparse.ArgumentParser(description="Génère questions listening en JSON")
    parser.add_argument('--limit', '-l', type=int, default=None, help='Limiter le nombre d\'audios')
    parser.add_argument('--offset', '-o', type=int, default=0, help='Commencer à partir de l\'index N')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Simulation sans appel API')
    args = parser.parse_args()
    
    print("=" * 70)
    print("  GÉNÉRATION QUESTIONS LISTENING → JSON (Groq API)")
    print(f"  Input:  {INPUT_PATH}")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Mode:   {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    print(f"  Délai:  {DELAY_BETWEEN_CALLS}s entre appels")
    print("=" * 70)
    
    load_env()
    
    if not args.dry_run:
        api_key = get_groq_api_key()
        if not api_key:
            print("❌ Clé API Groq non trouvée")
            return
        else:
            print(f"✅ Clé API trouvée: {api_key[:10]}...")
    
    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lecture {INPUT_PATH}: {e}")
        return
    
    print(f"\n📊 {len(entries)} entrées trouvées")
    
    # Appliquer offset et limit
    entries = entries[args.offset:]
    if args.limit:
        entries = entries[:args.limit]
    
    print(f"   → Traitement de {len(entries)} entrées (offset: {args.offset})")
    
    all_questions = []
    failed = []
    
    for i, entry in enumerate(entries):
        print(f"\n[{i+1}/{len(entries)}] ", end="")
        # Délai AVANT chaque appel (pas après) pour respecter le rate limit Groq
        if i > 0 and not args.dry_run:
            print(f"   ⏳ Pause {DELAY_BETWEEN_CALLS}s (rate limit Groq)...", flush=True)
            time.sleep(DELAY_BETWEEN_CALLS)
        questions = generate_questions_for_entry(entry, args.dry_run)
        if questions:
            all_questions.extend(questions)
        else:
            failed.append(entry['audio_id'])
    
    # Sauvegarder
    output_data = {
        "metadata": {
            "total_audios": len(entries),
            "total_questions": len(all_questions),
            "failed_audios": failed,
            "source_file": INPUT_PATH
        },
        "questions": all_questions
    }
    
    try:
        output_dir = os.path.dirname(OUTPUT_PATH)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Fichier sauvegardé: {OUTPUT_PATH}")
        print(f"   {len(all_questions)} questions pour {len(entries) - len(failed)} audios")
        if failed:
            print(f"   ⚠️  {len(failed)} échecs: {', '.join(failed[:10])}")
    except Exception as e:
        print(f"\n❌ Erreur sauvegarde: {e}")
    
    print(f"\n{'='*70}")
    print("  TERMINÉ")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()