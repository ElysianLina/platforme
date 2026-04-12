#!/usr/bin/env python
"""
Script de migration pour peupler la table listening_question
à partir du fichier listening_questions_corrected.json

Usage: python populate_listening_migration.py
"""

import os
import sys
import json
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_prj.settings')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import django
django.setup()

from users.models import ListeningAudio, ListeningQuestion


def populate_listening_questions():
    """
    Peuple la table listening_question avec les données du fichier JSON corrigé.
    """
    # Chemin vers le fichier JSON (depuis la racine du projet)
    json_path = Path(__file__).resolve().parent.parent.parent /  'data' / 'listening' / 'listening_questions_corrected.json'

    if not json_path.exists():
        print(f"❌ Fichier non trouvé: {json_path}")
        print("Vérifiez que le fichier listening_questions_corrected.json existe dans backend/data/listening/")
        return

    print(f"📂 Lecture du fichier: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions_data = data.get('questions', [])
    metadata = data.get('metadata', {})

    print(f"📊 Métadonnées:")
    print(f"   - Total audios: {metadata.get('total_audios', 'N/A')}")
    print(f"   - Total questions: {metadata.get('total_questions', 'N/A')}")
    print(f"   - Questions existantes: {metadata.get('existing_questions', 'N/A')}")
    print(f"   - Nouvelles questions: {metadata.get('new_questions', 'N/A')}")
    print()

    # Mapping des types de questions JSON vers Django
    type_mapping = {
        'true_false': 'true_false',
        'mcq': 'mcq',
        'word_order': 'word_order',
        'fill_blank': 'fill_blank',
        'synonym': 'synonym',
        'grammar': 'grammar',
        'vocabulary': 'vocabulary',
    }

    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for idx, q_data in enumerate(questions_data, 1):
        try:
            # Récupérer l'audio correspondant
            audio_id = q_data.get('audio_id')
            try:
                audio = ListeningAudio.objects.get(audio_id=audio_id)
            except ListeningAudio.DoesNotExist:
                print(f"⚠️  [{idx}/{len(questions_data)}] Audio '{audio_id}' non trouvé, question ignorée")
                skipped_count += 1
                continue

            # Préparer les données
            question_order = q_data.get('order')
            question_type = type_mapping.get(q_data.get('type'), 'mcq')
            question_text = q_data.get('question', '')
            choices = q_data.get('choices')
            correct_answer = q_data.get('answer', '')
            target_word = q_data.get('target_word') or ''
            correct_order = q_data.get('correct_order')

            # Vérifier si la question existe déjà (même audio + même ordre)
            existing_question = ListeningQuestion.objects.filter(
                audio=audio,
                question_order=question_order
            ).first()

            if existing_question:
                # Mettre à jour la question existante
                existing_question.question_type = question_type
                existing_question.question_text = question_text
                existing_question.choices = choices
                existing_question.correct_answer = correct_answer
                existing_question.target_word = target_word if target_word else ''
                existing_question.correct_order = correct_order
                existing_question.save()
                updated_count += 1
                print(f"🔄 [{idx}/{len(questions_data)}] Question mise à jour: {audio_id} - Q{question_order}")
            else:
                # Créer une nouvelle question
                ListeningQuestion.objects.create(
                    audio=audio,
                    question_order=question_order,
                    question_type=question_type,
                    question_text=question_text,
                    choices=choices,
                    correct_answer=correct_answer,
                    target_word=target_word if target_word else '',
                    correct_order=correct_order,
                    points=1  # Valeur par défaut
                )
                created_count += 1
                print(f"✅ [{idx}/{len(questions_data)}] Question créée: {audio_id} - Q{question_order}")

        except Exception as e:
            error_count += 1
            print(f"❌ [{idx}/{len(questions_data)}] Erreur: {e}")
            continue

    print()
    print("=" * 60)
    print("📈 RÉSUMÉ DE LA MIGRATION")
    print("=" * 60)
    print(f"✅ Questions créées:    {created_count}")
    print(f"🔄 Questions mises à jour: {updated_count}")
    print(f"⚠️  Questions ignorées (audio manquant): {skipped_count}")
    print(f"❌ Erreurs:            {error_count}")
    print(f"📊 Total traité:       {created_count + updated_count + skipped_count + error_count}")
    print("=" * 60)


if __name__ == '__main__':
    print("🚀 Démarrage de la migration des questions de listening...")
    print()

    # Vérifier que les tables existent
    try:
        audio_count = ListeningAudio.objects.count()
        question_count = ListeningQuestion.objects.count()
        print(f"📊 État actuel de la base:")
        print(f"   - ListeningAudio: {audio_count} enregistrements")
        print(f"   - ListeningQuestion: {question_count} enregistrements")
        print()
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base: {e}")
        print("Assurez-vous que les migrations Django ont été appliquées.")
        sys.exit(1)

    # Confirmation
    response = input("Continuer avec la migration? [O/n]: ").strip().lower()
    if response in ('', 'o', 'oui', 'y', 'yes'):
        populate_listening_questions()
    else:
        print("Migration annulée.")
