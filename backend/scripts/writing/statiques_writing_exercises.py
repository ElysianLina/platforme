#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
statiques_writing_exercises.py

Script pour générer des exercices d'écriture CEFR A1 via l'API Groq.
Génère un exercice par sous-unité avec énoncé unique et correction modèle.

Usage:
    python backend/scripts/writing/generate_writing_exercises.py

Configuration:
    Placer GROQ_API_KEY dans backend/.env

Output:
    backend/data/writing/writing_exercises_a1.json
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# CONFIGURATION DES CHEMINS
# =============================================================================

# Chemin absolu du script actuel: backend/scripts/writing/
SCRIPT_DIR = Path(__file__).parent.resolve()
# Remonter à backend/
BACKEND_DIR = SCRIPT_DIR.parent.parent.resolve()
# Dossier data/writing/
DATA_DIR = BACKEND_DIR / "data" / "writing"
# Fichier .env
ENV_FILE = BACKEND_DIR / ".env"

# Ajouter backend au path pour imports si nécessaire
sys.path.insert(0, str(BACKEND_DIR))

# =============================================================================
# CHARGEMENT DE LA CLÉ API DEPUIS .ENV
# =============================================================================

def load_env_file(env_path: Path) -> Dict[str, str]:
    """
    Charge les variables d'environnement depuis un fichier .env

    Args:
        env_path: Chemin vers le fichier .env

    Returns:
        Dictionnaire des variables chargées
    """
    env_vars = {}

    if not env_path.exists():
        print(f"⚠️ Warning: .env file not found at {env_path}")
        return env_vars

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignorer les lignes vides et commentaires
                if not line or line.startswith('#'):
                    continue
                # Parser KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Enlever quotes
                    env_vars[key] = value
    except Exception as e:
        print(f"⚠️ Error reading .env file: {e}")

    return env_vars


# Charger les variables d'environnement du fichier .env
ENV_VARS = load_env_file(ENV_FILE)

# =============================================================================
# IMPORT GROQ
# =============================================================================

try:
    from groq import Groq
except ImportError:
    print("❌ Erreur: Le package 'groq' n'est pas installé.")
    print("   Installez-le avec: pip install groq")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class Config:
    """Configuration du script."""
    API_KEY: str = ENV_VARS.get("GROQ_API_w", os.environ.get("GROQ_API_w", ""))
    MODEL: str = "llama-3.1-8b-instant"  # Modèle recommandé pour qualité A1
    TEMPERATURE: float = 0.7  # Créativité contrôlée pour variété
    MAX_TOKENS: int = 2048
    OUTPUT_DIR: Path = DATA_DIR
    OUTPUT_FILE: str = "writing_exercises_a1.json"
    RATE_LIMIT_DELAY: float = 1.5  # Délai entre requêtes (respect rate limits)
    MAX_RETRIES: int = 3


# =============================================================================
# DONNÉES DES UNITÉS ET SOUS-UNITÉS - 69 SOUS-UNITÉS
# =============================================================================

UNITS_DATA = [
    {
        "unit_id": "01",
        "unit_title": "Daily Routines",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Morning Customs", "theme": "morning routine, waking up, breakfast habits, early day activities"},
            {"sub_unit_id": "A1.2", "title": "Wake-up Sequence", "theme": "alarm clock, getting out of bed, morning activities step by step"},
            {"sub_unit_id": "A1.3", "title": "Home Day", "theme": "staying at home, daily activities at home, relaxing, indoor routine"}
        ]
    },
    {
        "unit_id": "02",
        "unit_title": "Family and Relationships",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "My Family", "theme": "family members, describing family, simple relationships, who is in my family"},
            {"sub_unit_id": "A1.2", "title": "Friends and Family", "theme": "friends, family together, simple social interactions, spending time together"},
            {"sub_unit_id": "A1.3", "title": "Family Tree", "theme": "family relationships, parents, siblings, grandparents, extended family"}
        ]
    },
    {
        "unit_id": "03",
        "unit_title": "Travel and Transportation",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Town Directions", "theme": "giving directions in town, left, right, straight, finding places in town"},
            {"sub_unit_id": "A1.2", "title": "Travel Plans", "theme": "planning a trip, where to go, simple travel intentions, vacation ideas"},
            {"sub_unit_id": "A1.3", "title": "Simple Directions", "theme": "asking and giving directions, locations, where is the..., turn left/right"},
            {"sub_unit_id": "A1.4", "title": "Daily Transportation", "theme": "bus, car, walking, how to get to places, commuting, going to school/work"},
            {"sub_unit_id": "A1.5", "title": "Shopping Trip", "theme": "going shopping, buying things, shops in town, market visit"}
        ]
    },
    {
        "unit_id": "04",
        "unit_title": "Hobbies and Interests",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "My Free Time", "theme": "free time activities, what I like to do, leisure time, after school/work"},
            {"sub_unit_id": "A1.2", "title": "What I Do on Weekends", "theme": "weekend activities, Saturday and Sunday plans, weekend routine"},
            {"sub_unit_id": "A1.3", "title": "Toy Selection", "theme": "toys, games, playing, children activities, choosing toys, favorite games"},
            {"sub_unit_id": "A1.4", "title": "My Hobbies on the Weekend", "theme": "hobbies, weekend interests, favorite activities, sports, reading, music"}
        ]
    },
    {
        "unit_id": "05",
        "unit_title": "Clothing and Fashion",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Clothing Shop", "theme": "buying clothes, shop vocabulary, sizes, trying on clothes, shopping experience"},
            {"sub_unit_id": "A1.2", "title": "My Clothing", "theme": "describing my clothes, what I wear, my wardrobe, favorite outfit"},
            {"sub_unit_id": "A1.3", "title": "Colorful Clothing", "theme": "colors and clothes, describing appearance, bright colors, matching colors"},
            {"sub_unit_id": "A1.4", "title": "Getting Dressed", "theme": "putting on clothes, daily dressing routine, getting ready, wearing clothes"},
            {"sub_unit_id": "A1.5", "title": "Seasonal Clothing", "theme": "clothes for seasons, summer and winter wear, warm and cool clothes"},
            {"sub_unit_id": "A1.6", "title": "Clothing Description", "theme": "describing clothes, materials, styles, patterns, new and old clothes"}
        ]
    },
    {
        "unit_id": "06",
        "unit_title": "Weather and Seasons",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Today's Weather", "theme": "describing weather today, sunny, rainy, cloudy, hot, cold, outside now"},
            {"sub_unit_id": "A1.2", "title": "Seasonal Wear", "theme": "clothes for different weather, hot and cold days, what to wear when"},
            {"sub_unit_id": "A1.3", "title": "Climate Details", "theme": "temperature, weather vocabulary, degrees, seasons description"},
            {"sub_unit_id": "A1.4", "title": "Seasons", "theme": "four seasons, spring, summer, autumn, winter, months and weather"},
            {"sub_unit_id": "A1.5", "title": "Atmosphere Kinds", "theme": "types of weather, windy, snowy, foggy, stormy, different conditions"},
            {"sub_unit_id": "A1.6", "title": "Small Talk Sky", "theme": "talking about weather, simple conversations, British small talk, daily chat"}
        ]
    },
    {
        "unit_id": "07",
        "unit_title": "Homes and Rooms",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "My Home", "theme": "describing my house or apartment, rooms, home sweet home, living place"},
            {"sub_unit_id": "A1.2", "title": "My Room", "theme": "my bedroom, furniture, personal space, my own room, decorating"},
            {"sub_unit_id": "A1.3", "title": "My Bedroom Details", "theme": "bed, desk, wardrobe, bedroom objects, lamp, mirror, details"},
            {"sub_unit_id": "A1.4", "title": "Kitchen", "theme": "kitchen objects, cooking, eating area, fridge, table, making food"}
        ]
    },
    {
        "unit_id": "08",
        "unit_title": "Food and Drink",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "My Favorite Food", "theme": "favorite foods, likes and dislikes, tasty food, yum, delicious"},
            {"sub_unit_id": "A1.2", "title": "Breakfast Food", "theme": "morning meals, breakfast items, eating breakfast, cereal, toast, eggs"},
            {"sub_unit_id": "A1.3", "title": "Food Preferences", "theme": "what I like to eat, healthy food, tastes, sweet, salty, preferences"},
            {"sub_unit_id": "A1.4", "title": "Making Sandwich", "theme": "making food, sandwich ingredients, steps, bread, cheese, ham, vegetables"},
            {"sub_unit_id": "A1.5", "title": "Food and Drink", "theme": "meals, beverages, eating habits, drinking water, juice, milk"},
            {"sub_unit_id": "A1.6", "title": "Lunch Food", "theme": "midday meals, lunch at home or school, sandwich, soup, salad"},
            {"sub_unit_id": "A1.7", "title": "Food Recipe", "theme": "simple recipes, cooking steps, ingredients, how to make, instructions"}
        ]
    },
    {
        "unit_id": "09",
        "unit_title": "Pets and Animals",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Zoo Animals", "theme": "animals at the zoo, wild animals, visiting zoo, lions, elephants, monkeys"},
            {"sub_unit_id": "A1.2", "title": "Pet Companion", "theme": "my pet, taking care of pets, animals at home, dog, cat, fish, bird"},
            {"sub_unit_id": "A1.3", "title": "Animals", "theme": "common animals, describing animals, sounds, farm animals, pets, wild"}
        ]
    },
    {
        "unit_id": "10",
        "unit_title": "Town and City",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Town Places", "theme": "places in town, bank, post office, shop, pharmacy, small town"},
            {"sub_unit_id": "A1.2", "title": "City Places", "theme": "big city locations, cinema, museum, park, mall, big buildings"},
            {"sub_unit_id": "A1.3", "title": "Park Visit", "theme": "going to the park, playground, activities, trees, benches, fun outside"},
            {"sub_unit_id": "A1.4", "title": "My Town", "theme": "describing my town, where I live, small place, quiet, nice town"},
            {"sub_unit_id": "A1.5", "title": "My City", "theme": "describing my city, big city life, busy, exciting, many people"},
            {"sub_unit_id": "A1.6", "title": "Town Transportation", "theme": "getting around town, bus, taxi, walking, bicycle, moving in town"},
            {"sub_unit_id": "A1.7", "title": "Basic Directions", "theme": "where is..., finding places, simple navigation, go straight, turn here"},
            {"sub_unit_id": "A1.8", "title": "Park Location", "theme": "describing location, near, far, next to, behind, in front of, prepositions"}
        ]
    },
    {
        "unit_id": "11",
        "unit_title": "Learning and Skills",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "My Skills", "theme": "what I can do, abilities, I can..., talents, things I am good at"}
        ]
    },
    {
        "unit_id": "12",
        "unit_title": "Objects and Descriptions",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Object Description", "theme": "describing things, color, size, shape, big, small, round, square"},
            {"sub_unit_id": "A1.2", "title": "My Things", "theme": "my possessions, objects I own, personal items, bag, phone, book"},
            {"sub_unit_id": "A1.3", "title": "Book Location", "theme": "where things are, prepositions of place, on the table, under the chair"}
        ]
    },
    {
        "unit_id": "13",
        "unit_title": "School Life",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "School Day", "theme": "my day at school, classes, timetable, subjects, learning"},
            {"sub_unit_id": "A1.2", "title": "Classroom Objects", "theme": "things in the classroom, desk, chair, board, computer, map"},
            {"sub_unit_id": "A1.3", "title": "School Bag", "theme": "my school bag, books, pencils, contents, what I carry"},
            {"sub_unit_id": "A1.4", "title": "My Classroom", "theme": "describing the classroom, where I study, room layout, my place"},
            {"sub_unit_id": "A1.5", "title": "School Objects", "theme": "school supplies, pen, ruler, eraser, pencil case, scissors, glue"}
        ]
    },
    {
        "unit_id": "14",
        "unit_title": "Introductions and Greetings",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Simple Questions", "theme": "introducing myself, asking simple questions, greetings, hello, how are you, name"}
        ]
    },
    {
        "unit_id": "15",
        "unit_title": "Numbers and Colors",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Counting Numbers", "theme": "numbers 1-100, counting, basic math, how many, quantity"},
            {"sub_unit_id": "A1.2", "title": "Colors", "theme": "basic colors, naming colors, red, blue, green, yellow, favorite color"},
            {"sub_unit_id": "A1.3", "title": "Colorful Objects", "theme": "describing colors of things around me, my colorful room, world colors"},
            {"sub_unit_id": "A1.4", "title": "Numbers and Ages", "theme": "saying age, how old are you, numbers, birthday, years old"},
            {"sub_unit_id": "A1.5", "title": "Numbers and Prices", "theme": "prices, shopping, how much, cost, money, buying, cheap, expensive"},
            {"sub_unit_id": "A1.6", "title": "Numbers and Colors", "theme": "combining numbers and colors, descriptions, three red apples, two blue pens"}
        ]
    },
    {
        "unit_id": "16",
        "unit_title": "Shopping and Money",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Going Shopping", "theme": "shopping trip, buying things, stores, going to buy, need and want"},
            {"sub_unit_id": "A1.2", "title": "Supermarket", "theme": "supermarket shopping, food shopping, cart, shelves, products, checkout"},
            {"sub_unit_id": "A1.3", "title": "Shopping List", "theme": "making a list, what to buy, planning, items needed, organize shopping"}
        ]
    },
    {
        "unit_id": "17",
        "unit_title": "Time and Schedules",
        "level": "A1",
        "sub_units": [
            {"sub_unit_id": "A1.1", "title": "Telling Time", "theme": "clock, time, what time is it, daily schedule, hours, minutes, o'clock"}
        ]
    }
]


# =============================================================================
# PROMPTS ENGINEERING - MODIFIÉ POUR RÉPONSES PLUS LONGUES
# =============================================================================

SYSTEM_PROMPT = """You are an expert English language teacher specializing in CEFR Level A1 (beginner) writing exercises. 
Your task is to create unique, engaging writing exercises appropriate for absolute beginners.

Rules for CEFR A1 writing:
- Use simple present tense predominantly
- Vocabulary: high-frequency everyday words only
- Sentence structure: simple SVO, short sentences (5-8 words average)
- Avoid: complex clauses, phrasal verbs, idioms, abstract concepts
- Include: concrete, familiar topics from daily life
- Length: 60-80 words for student response expected (3-4 lines, NOT just 1-2 lines)
- Grammar focus: articles (a/an/the), basic prepositions (in, on, at, under), simple adjectives

IMPORTANT: The model answer MUST be 3-4 lines long (approximately 60-80 words), NOT a single short sentence.
Each sentence should add new information to build a complete paragraph.

You must generate exercises that are pedagogically sound, culturally neutral, and progressively build confidence."""


def build_user_prompt(sub_unit: Dict, unit_title: str) -> str:
    """
    Construit le prompt utilisateur pour générer un exercice unique.
    """
    prompt = f"""Create ONE unique writing exercise for CEFR Level A1 English learners.

UNIT: {unit_title}
SUB-UNIT: {sub_unit['title']} ({sub_unit['sub_unit_id']})
THEME: {sub_unit['theme']}

Requirements:
1. The exercise MUST be totally unique and specific to the theme "{sub_unit['title']}"
2. NO redundancy with other common topics - focus specifically on: {sub_unit['theme']}
3. Task type: Write a short paragraph (60-80 words, 3-4 lines) about the given topic
4. Provide a clear, simple writing prompt/instruction
5. Include 3-4 bullet points to guide the student (what to include)
6. Provide a model answer (correction) at A1 level - MUST BE 3-4 LINES LONG (60-80 words), not just 1-2 short sentences
7. Include a brief "Teacher Notes" section with key vocabulary and grammar points

CRITICAL REQUIREMENT FOR MODEL ANSWER:
- The model answer MUST be 3-4 lines long
- Each line should be a complete sentence
- Total word count: 60-80 words
- Example of GOOD length: "I wake up at seven o'clock every morning. I eat breakfast with my family. I like to eat toast and drink orange juice. Then I brush my teeth and get ready for school."
- Example of BAD length (too short): "I wake up at 7 am. I eat toast. I go to school." (This is only 1-2 lines and too short!)

Format your response EXACTLY as this JSON structure:
{{
    "exercise": {{
        "instruction": "Clear writing instruction in simple English",
        "guiding_points": [
            "Point 1: what to mention",
            "Point 2: what to describe", 
            "Point 3: simple detail to include"
        ],
        "word_count_target": "60-80 words (3-4 lines)",
        "difficulty": "A1"
    }},
    "model_answer": {{
        "text": "The model paragraph at A1 level - MUST BE 3-4 LINES LONG with 60-80 words total. Write complete sentences that flow together as a paragraph.",
        "vocabulary_used": ["word1", "word2", "word3", "word4", "word5"],
        "grammar_focus": ["grammar point 1", "grammar point 2"]
    }},
    "teacher_notes": {{
        "key_vocabulary": ["key word 1", "key word 2", "key word 3"],
        "grammar_points": ["point 1", "point 2"],
        "common_mistakes": ["mistake to avoid 1", "mistake to avoid 2"]
    }}
}}

IMPORTANT: 
- The exercise must be specifically about "{sub_unit['title']}", not generic
- Use vocabulary and contexts related to: {sub_unit['theme']}
- Model answer MUST demonstrate achievable A1 level writing with 3-4 LINES (60-80 words)
- Response must be valid JSON only, no markdown formatting, no explanation outside JSON"""

    return prompt


# =============================================================================
# CLASSE PRINCIPALE
# =============================================================================

class WritingExerciseGenerator:
    """Générateur d'exercices d'écriture via API Groq."""

    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.results = []
        self.errors = []

        if not self.config.API_KEY:
            raise ValueError(
                f"GROQ_API_KEY not found! Please add it to {ENV_FILE} or set as environment variable.\n"
                f"Format in .env file: GROQ_API_KEY=gsk_your_key_here"
            )

        self.client = Groq(api_key=self.config.API_KEY)

        # Créer le répertoire de sortie
        self.config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.config.OUTPUT_DIR}")

    def _call_api(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Appelle l'API Groq avec retry logic."""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.config.MODEL,
                    temperature=self.config.TEMPERATURE,
                    max_completion_tokens=self.config.MAX_TOKENS,
                    top_p=0.9,
                    stream=False
                )

                return chat_completion.choices[0].message.content

            except Exception as e:
                print(f"    ⚠️ Attempt {attempt + 1}/{self.config.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

    def _parse_response(self, content: str, sub_unit: Dict) -> Optional[Dict]:
        """Parse la réponse JSON de l'API."""
        try:
            # Nettoyer le contenu
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            # Valider la structure minimale
            if "exercise" not in data or "model_answer" not in data:
                raise ValueError("Missing required keys in response")

            # Vérifier la longueur du texte modèle
            model_text = data.get("model_answer", {}).get("text", "")
            word_count = len(model_text.split())

            if word_count < 40:
                print(f"    ⚠️ Warning: Model answer seems short ({word_count} words)")

            # Enrichir avec métadonnées
            data["metadata"] = {
                "unit_id": sub_unit.get("unit_id", ""),
                "sub_unit_id": sub_unit["sub_unit_id"],
                "unit_title": sub_unit.get("unit_title", ""),
                "sub_unit_title": sub_unit["title"],
                "theme": sub_unit["theme"],
                "generated_at": datetime.now().isoformat(),
                "model": self.config.MODEL,
                "model_answer_word_count": word_count
            }

            return data

        except json.JSONDecodeError as e:
            print(f"    ❌ JSON parsing error: {e}")
            print(f"    Content preview: {content[:200]}...")
            return None
        except Exception as e:
            print(f"    ❌ Validation error: {e}")
            return None

    def generate_exercise(self, sub_unit: Dict, unit_title: str, unit_id: str) -> Optional[Dict]:
        """Génère un exercice pour une sous-unité spécifique."""
        sub_unit_with_meta = {
            **sub_unit,
            "unit_id": unit_id,
            "unit_title": unit_title
        }

        prompt = build_user_prompt(sub_unit_with_meta, unit_title)

        print(f"  📝 Generating exercise for {sub_unit['sub_unit_id']}: {sub_unit['title']}")

        content = self._call_api(prompt, SYSTEM_PROMPT)

        if content is None:
            self.errors.append(f"{sub_unit['sub_unit_id']}: API call failed")
            return None

        exercise = self._parse_response(content, sub_unit_with_meta)

        if exercise is None:
            self.errors.append(f"{sub_unit['sub_unit_id']}: Parsing failed")
            return None

        return exercise

    def generate_all(self) -> List[Dict]:
        """Génère tous les exercices pour toutes les unités."""
        total_sub_units = sum(len(u["sub_units"]) for u in UNITS_DATA)

        separator = ":" * 60
        print(f"\n{separator}")
        print(f"🚀 Starting Writing Exercise Generation")
        print(f"   Model: {self.config.MODEL}")
        print(f"   Total sub-units to generate: {total_sub_units}")
        print(f"   Target: 60-80 words per model answer (3-4 lines)")
        print(f"   Output: {self.config.OUTPUT_DIR / self.config.OUTPUT_FILE}")
        print(f"{separator}\n")

        current = 0

        for unit in UNITS_DATA:
            unit_id = unit["unit_id"]
            unit_title = unit["unit_title"]
            unit_sub_count = len(unit["sub_units"])

            print(f"\n📚 Unit {unit_id}: {unit_title} ({unit_sub_count} exercises)")
            print("   " + "-" * 50)

            for sub_unit in unit["sub_units"]:
                current += 1
                print(f"\n   [{current}/{total_sub_units}]")

                exercise = self.generate_exercise(sub_unit, unit_title, unit_id)

                if exercise:
                    self.results.append(exercise)
                    word_count = exercise["metadata"].get("model_answer_word_count", 0)
                    print(f"    ✅ Success ({word_count} words)")
                else:
                    print(f"    ❌ Failed - will be recorded in errors")

                if current < total_sub_units:
                    time.sleep(self.config.RATE_LIMIT_DELAY)

        return self.results

    def save_results(self):
        """Sauvegarde les résultats dans le fichier JSON de sortie."""
        output_path = self.config.OUTPUT_DIR / self.config.OUTPUT_FILE

        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model": self.config.MODEL,
                "total_exercises": len(self.results),
                "expected_count": 69,
                "failed_count": len(self.errors),
                "cefr_level": "A1",
                "exercise_type": "paragraph_writing",
                "target_word_count": "60-80 words per answer (3-4 lines)"
            },
            "exercises": self.results,
            "errors": self.errors if self.errors else None
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        separator = ":" * 60
        print(f"\n{separator}")
        print(f"💾 Results saved to: {output_path}")
        print(f"   Total exercises generated: {len(self.results)}/69")
        print(f"   Failed: {len(self.errors)}")
        print(f"{separator}")

        return output_path


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def validate_output_file(filepath: Path) -> bool:
    """Valide le fichier de sortie généré."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        exercises = data.get("exercises", [])
        expected = data.get("metadata", {}).get("expected_count", 69)

        print(f"\n🔍 Validation Report:")
        print(f"   - File is valid JSON: ✅")
        print(f"   - Contains {len(exercises)}/{expected} exercises")

        required_keys = {"exercise", "model_answer", "metadata"}
        valid_count = 0
        short_answers = 0

        for i, ex in enumerate(exercises):
            if all(k in ex for k in required_keys):
                valid_count += 1
                text = ex.get("model_answer", {}).get("text", "")
                word_count = len(text.split())
                if word_count < 40:
                    short_answers += 1
            else:
                missing = required_keys - set(ex.keys())
                print(f"   - Exercise {i}: Missing keys {missing}")

        print(f"   - Valid structure: {valid_count}/{len(exercises)}")
        if short_answers > 0:
            print(f"   ⚠️ Short answers (< 40 words): {short_answers}")

        sub_unit_ids = [ex["metadata"]["sub_unit_id"] for ex in exercises]
        unique_ids = set(sub_unit_ids)
        if len(sub_unit_ids) != len(unique_ids):
            print(f"   ⚠️ Warning: Duplicate sub_unit_ids detected!")

        return valid_count == len(exercises) and len(exercises) == expected

    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return False


def generate_summary_report(filepath: Path):
    """Génère un rapport récapitulatif des exercices."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    exercises = data.get("exercises", [])

    word_counts = []
    for ex in exercises:
        text = ex.get("model_answer", {}).get("text", "")
        word_counts.append(len(text.split()))

    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    min_words = min(word_counts) if word_counts else 0
    max_words = max(word_counts) if word_counts else 0

    separator = "=" * 60
    print(f"\n{separator}")
    print(f"📊 EXERCISE SUMMARY REPORT")
    print(f"{separator}")
    print(f"\n📏 Word Count Statistics:")
    print(f"   - Average: {avg_words:.1f} words")
    print(f"   - Min: {min_words} words")
    print(f"   - Max: {max_words} words")
    print(f"   - Target: 60-80 words (3-4 lines)")

    by_unit = {}
    for ex in exercises:
        unit_id = ex["metadata"]["unit_id"]
        if unit_id not in by_unit:
            by_unit[unit_id] = []
        by_unit[unit_id].append(ex)

    for unit_id in sorted(by_unit.keys()):
        unit_exercises = by_unit[unit_id]
        unit_title = unit_exercises[0]["metadata"]["unit_title"]

        print(f"\n📖 Unit {unit_id}: {unit_title} ({len(unit_exercises)} exercises)")
        for ex in sorted(unit_exercises, key=lambda x: x["metadata"]["sub_unit_id"]):
            meta = ex["metadata"]
            word_count = meta.get("model_answer_word_count", 0)
            print(f"   • {meta['sub_unit_id']}: {meta['sub_unit_title']} ({word_count} words)")

    print(f"\n{separator}")
    print(f"Total: {len(exercises)} exercises across {len(by_unit)} units")
    print(f"{separator}")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée principal."""
    print(f"\n🔧 Configuration:")
    print(f"   Backend dir: {BACKEND_DIR}")
    print(f"   .env file: {ENV_FILE}")
    print(f"   Output dir: {DATA_DIR}")

    if not ENV_FILE.exists():
        print(f"\n❌ ERROR: .env file not found at {ENV_FILE}")
        print(f"\nPlease create the .env file with your API key:")
        print(f"   GROQ_API_KEY=gsk_your_api_key_here")
        sys.exit(1)

    config = Config()

    if not config.API_KEY:
        print(f"\n❌ ERROR: GROQ_API_KEY not found in {ENV_FILE} or environment variables!")
        print(f"\nPlease add to {ENV_FILE}:")
        print(f"   GROQ_API_KEY=gsk_your_api_key_here")
        print(f"\nGet your API key from: https://console.groq.com/keys")
        sys.exit(1)

    print(f"   API Key: {'✅ Found (masked)' if config.API_KEY else '❌ Missing'}")

    try:
        generator = WritingExerciseGenerator(config)
        generator.generate_all()
        output_path = generator.save_results()

        if validate_output_file(output_path):
            print(f"\n✅ All validations passed!")
        else:
            print(f"\n⚠️ Some validations failed - check output manually")

        generate_summary_report(output_path)
        print(f"\n🎉 Generation complete!")

    except KeyboardInterrupt:
        print(f"\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()