#!/usr/bin/env python3
"""
Script d'import/mise à jour des exercices de writing avec les IDs de subunit corrects.

Usage:
    cd backend
    python scripts/writing/import_writing_exercises.py
"""

import os
import sys
import json

# Configuration Django - CORRIGÉ pour votre structure
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_prj.settings')

# Ajouter le backend au path
backend_path = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(backend_path))

import django
django.setup()

from users.models import WritingExercise, SubUnit, Unit


def load_corrected_json():
    """Charge le JSON corrigé avec les vrais IDs."""
    json_path = os.path.join(
        os.path.dirname(__file__), 
        '../../data/writing/writing_exercises_a1.json'
    )

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['exercises']


def update_writing_exercises():
    """Met à jour les writing_exercises avec les bons IDs de subunit."""
    exercises = load_corrected_json()

    updated_count = 0
    created_count = 0
    error_count = 0

    print("=" * 60)
    print("MISE À JOUR DES EXERCICES DE WRITING")
    print("=" * 60)

    for ex_data in exercises:
        try:
            metadata = ex_data['metadata']
            exercise = ex_data['exercise']
            model_answer = ex_data['model_answer']
            teacher_notes = ex_data['teacher_notes']

            # Extraire les IDs corrects du JSON corrigé
            unit_id = int(metadata['unit_id'])
            sub_unit_id = int(metadata['sub_unit_id'])
            subunit_title = metadata['sub_unit_title']
            unit_title = metadata['unit_title']

            # Vérifier que la subunit existe
            try:
                sub_unit = SubUnit.objects.get(id=sub_unit_id)
            except SubUnit.DoesNotExist:
                print(f"❌ ERREUR: SubUnit ID {sub_unit_id} n\'existe pas ({subunit_title})")
                error_count += 1
                continue

            # Vérifier que l'unit correspond
            if sub_unit.unit.id != unit_id:
                print(f"⚠️  ATTENTION: Unit mismatch pour subunit {sub_unit_id}")
                print(f"   Attendu: {unit_id}, Trouvé: {sub_unit.unit.id}")

            # Préparer les données pour WritingExercise
            exercise_data = {
                'sub_unit': sub_unit,
                'instruction': exercise['instruction'],
                'guiding_points': exercise['guiding_points'],
                'word_count_target': exercise.get('word_count_target', '60-80 words'),
                'model_answer_text': model_answer['text'],
                'model_answer_vocabulary': model_answer.get('vocabulary_used', []),
                'model_answer_grammar': model_answer.get('grammar_focus', []),
                'key_vocabulary': teacher_notes.get('key_vocabulary', []),
                'grammar_patterns': teacher_notes.get('grammar_points', []),
                'difficulty': metadata.get('cefr_level', 'A1'),
                'theme': metadata.get('theme', ''),
                'unit_title': unit_title,
                'subunit_title': subunit_title,
            }

            # Créer ou mettre à jour l'exercice
            writing_ex, created = WritingExercise.objects.update_or_create(
                sub_unit=sub_unit,  # Un exercice par subunit
                defaults=exercise_data
            )

            if created:
                created_count += 1
                print(f"✅ CRÉÉ: {unit_title} / {subunit_title} (SubUnit ID: {sub_unit_id})")
            else:
                updated_count += 1
                print(f"🔄 MIS À JOUR: {unit_title} / {subunit_title} (SubUnit ID: {sub_unit_id})")

        except Exception as e:
            print(f"❌ ERREUR sur {metadata.get('sub_unit_title', 'UNKNOWN')}: {str(e)}")
            error_count += 1
            continue

    print("=" * 60)
    print("RÉSULTATS:")
    print(f"  - Exercices créés: {created_count}")
    print(f"  - Exercices mis à jour: {updated_count}")
    print(f"  - Erreurs: {error_count}")
    print(f"  - Total traité: {created_count + updated_count}")
    print("=" * 60)


if __name__ == '__main__':
    update_writing_exercises()