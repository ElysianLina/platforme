#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
complete_missing.py - Complète les audios manquants dans le fichier de questions
Garde les 180 questions existantes et ajoute les 480 manquantes (48 audios × 10)
"""

import json
import random
import re
import os
from typing import List, Dict, Any

# Configuration des chemins
# Le script est dans: backend/scripts/listening/
# Les données sont dans: backend/data/listening/

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DATA_DIR = os.path.join(BACKEND_DIR, 'data', 'listening')

# Fichiers
EXISTING_FILE = os.path.join(DATA_DIR, 'listening_questions_generated.json')
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, 'ljspeech_subunit_assignments.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'listening_questions_complete.json')

def extract_keywords(transcript: str) -> List[str]:
    """Extrait les mots-clés importants du transcript"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                  'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 
                  'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it', 
                  'we', 'they', 'this', 'that', 'these', 'those', 'my', 'his', 'her', 'their'}

    words = re.findall(r'\b[a-zA-Z]+\b', transcript.lower())
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]

    return list(set(keywords))[:5]

def generate_true_false_question(audio_id: str, transcript: str) -> Dict[str, Any]:
    """Génère une question vrai/faux"""
    sentences = transcript.split('.')
    first_sentence = sentences[0].strip()[:60] if sentences else transcript[:60]

    return {
        "order": 1,
        "type": "true_false",
        "question": f"The text says: '{first_sentence}'.",
        "choices": None,
        "answer": "True",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_mcq_question_1(audio_id: str, transcript: str) -> Dict[str, Any]:
    """Génère la première question à choix multiples"""
    keywords = extract_keywords(transcript)
    topic = keywords[0].title() if keywords else "the topic"

    return {
        "order": 2,
        "type": "mcq",
        "question": "What is the main subject of this audio?",
        "choices": [
            f"A. {topic}",
            "B. A different subject",
            "C. Something unrelated",
            "D. None of the above"
        ],
        "answer": "A",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_mcq_question_2(audio_id: str, transcript: str) -> Dict[str, Any]:
    """Génère la deuxième question à choix multiples"""
    return {
        "order": 3,
        "type": "mcq",
        "question": "What can be inferred from the audio?",
        "choices": [
            "A. It describes a specific situation",
            "B. It talks about general ideas",
            "C. It mentions several people",
            "D. It focuses on one main point"
        ],
        "answer": "D",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_word_order_question(audio_id: str, transcript: str) -> Dict[str, Any]:
    """Génère une question d'ordre des mots"""
    words = transcript.split()[:7]
    if len(words) < 4:
        words = ["the", "audio", "is", "short"]

    shuffled = words.copy()
    random.shuffle(shuffled)

    return {
        "order": 4,
        "type": "word_order",
        "question": f"Put the words in the correct order: {' '.join(shuffled)}",
        "choices": shuffled,
        "answer": ' '.join(words),
        "target_word": None,
        "correct_order": words,
        "audio_id": audio_id
    }

def generate_fill_blank_question(audio_id: str, transcript: str) -> Dict[str, Any]:
    """Génère une question à trou"""
    words = transcript.split()
    if len(words) > 5:
        blank_word = words[3] if len(words) > 3 else words[0]
        context_start = ' '.join(words[:3])
        context_end = ' '.join(words[4:6]) if len(words) > 5 else ""
        question_text = f"{context_start} ___ {context_end}".strip()
    else:
        question_text = "The audio mentions something about ___"
        blank_word = "topic"

    return {
        "order": 5,
        "type": "fill_blank",
        "question": f"Complete: '{question_text}'",
        "choices": [blank_word, "other", "different", "unknown"],
        "answer": blank_word,
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_synonym_question(audio_id: str) -> Dict[str, Any]:
    """Génère une question de synonyme"""
    synonyms = [
        ("said", "stated"), ("big", "large"), ("small", "little"),
        ("happy", "joyful"), ("sad", "unhappy"), ("important", "significant"),
        ("begin", "start"), ("end", "finish"), ("help", "assist"), ("show", "display")
    ]
    word, synonym = random.choice(synonyms)

    return {
        "order": 6,
        "type": "synonym",
        "question": f"What is the synonym of '{word}'?",
        "choices": None,
        "answer": synonym,
        "target_word": word,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_grammar_question_1(audio_id: str) -> Dict[str, Any]:
    """Génère la première question de grammaire"""
    return {
        "order": 7,
        "type": "grammar",
        "question": "The speaker ___ about the topic.",
        "choices": ["A. talk", "B. talks", "C. talking", "D. talked"],
        "answer": "B",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_grammar_question_2(audio_id: str) -> Dict[str, Any]:
    """Génère la deuxième question de grammaire"""
    return {
        "order": 8,
        "type": "grammar",
        "question": "They ___ to the audio yesterday.",
        "choices": ["A. listen", "B. listens", "C. listened", "D. listening"],
        "answer": "C",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_vocabulary_question_1(audio_id: str) -> Dict[str, Any]:
    """Génère la première question de vocabulaire"""
    vocab_words = [
        ("quickly", "Fast", "Slowly", "Carefully", "Loudly"),
        ("bright", "Shining", "Dark", "Dull", "Quiet"),
        ("happy", "Joyful", "Sad", "Angry", "Tired"),
        ("begin", "Start", "End", "Continue", "Stop"),
        ("important", "Significant", "Small", "Minor", "Tiny")
    ]
    word, correct, *wrong = random.choice(vocab_words)

    return {
        "order": 9,
        "type": "vocabulary",
        "question": f"What does '{word}' mean?",
        "choices": [f"A. {correct}", f"B. {wrong[0]}", f"C. {wrong[1]}", f"D. {wrong[2]}"],
        "answer": "A",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_vocabulary_question_2(audio_id: str) -> Dict[str, Any]:
    """Génère la deuxième question de vocabulaire"""
    return {
        "order": 10,
        "type": "vocabulary",
        "question": "What does 'transcript' mean?",
        "choices": [
            "A. A written version of spoken words",
            "B. A type of music",
            "C. A scientific instrument",
            "D. A mathematical equation"
        ],
        "answer": "A",
        "target_word": None,
        "correct_order": None,
        "audio_id": audio_id
    }

def generate_questions_for_audio(audio_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Génère les 10 questions pour un audio donné"""
    audio_id = audio_entry['audio_id']
    transcript = audio_entry.get('transcript', '')

    return [
        generate_true_false_question(audio_id, transcript),
        generate_mcq_question_1(audio_id, transcript),
        generate_mcq_question_2(audio_id, transcript),
        generate_word_order_question(audio_id, transcript),
        generate_fill_blank_question(audio_id, transcript),
        generate_synonym_question(audio_id),
        generate_grammar_question_1(audio_id),
        generate_grammar_question_2(audio_id),
        generate_vocabulary_question_1(audio_id),
        generate_vocabulary_question_2(audio_id)
    ]

def main():
    print("=" * 60)
    print("COMPLETION DES QUESTIONS MANQUANTES")
    print("=" * 60)

    print(f"\n📁 Chemins:")
    print(f"   Script: {SCRIPT_DIR}")
    print(f"   Données: {DATA_DIR}")

    # Vérifier que le dossier existe
    if not os.path.exists(DATA_DIR):
        print(f"\n   ✗ Dossier non trouvé: {DATA_DIR}")
        print(f"   → Création du dossier...")
        os.makedirs(DATA_DIR, exist_ok=True)

    # Charger les questions existantes
    print(f"\n[1] Chargement de '{os.path.basename(EXISTING_FILE)}'...")
    try:
        with open(EXISTING_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_questions = existing_data.get('questions', [])
        print(f"    ✓ {len(existing_questions)} questions chargées")
    except FileNotFoundError:
        print(f"    ✗ Fichier non trouvé: {EXISTING_FILE}")
        print(f"    → Recherche dans le dossier courant...")
        # Essayer dans le dossier courant
        local_file = 'listening_questions_generated.json'
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_questions = existing_data.get('questions', [])
            print(f"    ✓ Trouvé localement: {len(existing_questions)} questions")
        else:
            print(f"    ✗ Non trouvé non plus. Arrêt.")
            return
    except json.JSONDecodeError as e:
        print(f"    ✗ Erreur JSON: {e}")
        return

    # Récupérer les audio_id déjà traités
    treated_audio_ids = set(q.get('audio_id') for q in existing_questions)
    print(f"    → {len(treated_audio_ids)} audios déjà traités")

    # Charger tous les assignments
    print(f"\n[2] Chargement de '{os.path.basename(ASSIGNMENTS_FILE)}'...")
    try:
        with open(ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
        print(f"    ✓ {len(assignments)} entrées trouvées")
    except FileNotFoundError:
        print(f"    ✗ Fichier non trouvé: {ASSIGNMENTS_FILE}")
        # Essayer dans le dossier courant
        local_assign = 'ljspeech_subunit_assignments.json'
        if os.path.exists(local_assign):
            with open(local_assign, 'r', encoding='utf-8') as f:
                assignments = json.load(f)
            print(f"    ✓ Trouvé localement: {len(assignments)} entrées")
        else:
            print(f"    ✗ Non trouvé. Arrêt.")
            return

    # Identifier les audios manquants
    all_audio_ids = set(entry['audio_id'] for entry in assignments)
    missing_audio_ids = all_audio_ids - treated_audio_ids

    print(f"\n[3] Analyse:")
    print(f"    - Total dans assignments: {len(all_audio_ids)}")
    print(f"    - Déjà traités: {len(treated_audio_ids)}")
    print(f"    - Manquants: {len(missing_audio_ids)}")

    if not missing_audio_ids:
        print(f"\n    ✓ Tous les audios sont déjà traités!")
        return

    # Créer un dictionnaire pour accès rapide
    assignments_dict = {entry['audio_id']: entry for entry in assignments}

    # Copier les questions existantes
    all_questions = existing_questions.copy()
    failed_audios = []
    success_count = 0

    # Traiter les audios manquants
    print(f"\n[4] Génération des questions manquantes...")
    print("-" * 60)

    for i, audio_id in enumerate(sorted(missing_audio_ids), 1):
        entry = assignments_dict[audio_id]
        print(f"[{i:2d}/{len(missing_audio_ids)}] {audio_id}...", end=' ', flush=True)

        try:
            new_questions = generate_questions_for_audio(entry)
            all_questions.extend(new_questions)
            success_count += 1
            print(f"✓ ({len(new_questions)} q)")
        except Exception as e:
            print(f"✗ ERREUR: {str(e)[:40]}")
            failed_audios.append(audio_id)

    print("-" * 60)

    # Créer le fichier de sortie
    print(f"\n[5] Création du fichier de sortie...")
    output_data = {
        "metadata": {
            "total_audios": len(assignments),
            "total_questions": len(all_questions),
            "existing_questions": len(existing_questions),
            "new_questions": len(all_questions) - len(existing_questions),
            "failed_audios": failed_audios,
            "source_file": "ljspeech_subunit_assignments.json"
        },
        "questions": all_questions
    }

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"    ✓ Sauvegardé: '{OUTPUT_FILE}'")
    except Exception as e:
        print(f"    ✗ Erreur: {e}")
        # Essayer de sauvegarder localement
        local_output = 'listening_questions_complete.json'
        with open(local_output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"    ✓ Sauvegardé localement: '{local_output}'")

    # Rapport final
    print(f"\n" + "=" * 60)
    print("RAPPORT FINAL")
    print("=" * 60)
    print(f"  Audios dans source:      {len(assignments)}")
    print(f"  Audios déjà traités:     {len(treated_audio_ids)}")
    print(f"  Nouveaux audios:         {success_count}")
    print(f"  Audios en échec:         {len(failed_audios)}")
    print(f"  ─────────────────────────────────────")
    print(f"  Questions existantes:    {len(existing_questions)}")
    print(f"  Questions ajoutées:      {len(all_questions) - len(existing_questions)}")
    print(f"  TOTAL QUESTIONS:         {len(all_questions)}")
    print(f"  Attendu (66×10):         {len(assignments) * 10}")
    print(f"  ─────────────────────────────────────")
    if len(all_questions) == len(assignments) * 10:
        print(f"  ✅ COMPLET!")
    else:
        print(f"  ⚠️  Manque: {len(assignments) * 10 - len(all_questions)} questions")
    print("=" * 60)

    if failed_audios:
        print(f"\n⚠️  Audios en échec ({len(failed_audios)}):")
        for aid in failed_audios[:5]:
            print(f"   - {aid}")

if __name__ == "__main__":
    main()