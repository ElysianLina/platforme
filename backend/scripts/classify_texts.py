"""
classify_texts.py
─────────────────────────────────────────────────────────────────────
Script à lancer UNE SEULE FOIS pour classifier les 266 textes A1
en Unités et Sous-Unités via l'API Groq (gratuite, sans restriction).

Étapes :
  1. Lit tous les topics A1 depuis le dataset JSONL
  2. Appel 1 → Groq assigne chaque topic à une SubUnit nommée
  3. Appel 2 → Groq regroupe les SubUnits en Units thématiques
  4. Sauvegarde le résultat dans classification_a1.json

Lancer depuis backend/ :
  pip install groq
  python scripts/classify_texts.py
─────────────────────────────────────────────────────────────────────
"""

import json
import time
import os
from groq import Groq

# ── CONFIG ────────────────────────────────────────────────────────
GROQ_API_KEY = "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"        
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'final_english_dataset.jsonl')
OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'classification_a1.json')
TARGET_LEVEL = "A1"
MODEL_NAME   = "llama-3.3-70b-versatile"       # modèle gratuit Groq
# ──────────────────────────────────────────────────────────────────

client = Groq(api_key=GROQ_API_KEY)


def load_a1_topics(path: str) -> list[dict]:
    """Charge tous les topics A1 depuis le dataset."""
    topics = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            meta  = entry.get("scientific_metadata", {})
            if meta.get("target_level") == TARGET_LEVEL:
                topics.append({
                    "topic":      meta.get("topic", ""),
                    "vocabulary": meta.get("constraints", {}).get("target_vocabulary", [])
                })
    return topics


def call_groq(prompt: str, retries: int = 3) -> str:
    """Appel API Groq avec retry automatique."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  ⚠️  Erreur API (tentative {attempt+1}/{retries}): {e}")
            time.sleep(10)
    raise Exception("❌ Groq API inaccessible après plusieurs tentatives.")


def extract_json(text: str) -> dict | list:
    """Extrait le JSON depuis la réponse (enlève les backticks markdown)."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text  = "\n".join(lines[1:-1])
    return json.loads(text)


def step1_assign_subunits(topics: list[dict]) -> dict:
    """
    Étape 1 : Pour chaque topic, assigne un nom de SubUnit descriptif.
    Retourne : { "topic": "subunit_name", ... }
    """
    print("\n📡 Étape 1 — Attribution des SubUnits à chaque texte...")

    topics_list = "\n".join([f"- {t['topic']}" for t in topics])

    prompt = f"""You are an English language curriculum designer.

Below is a list of {len(topics)} reading passage topics for CEFR A1 (beginner) English learners.

Your task:
For each topic, assign a SHORT descriptive SubUnit name (2-5 words) that describes
the specific theme of that passage.

Rules:
- SubUnit names should be specific (not generic)
- Different topics can share the same SubUnit name if they cover the exact same theme
- Keep names simple and clear for A1 level
- Respond ONLY with a valid JSON object, no explanation, no markdown backticks

Format:
{{
  "topic name here": "SubUnit Name Here",
  ...
}}

Topics:
{topics_list}"""

    raw    = call_groq(prompt)
    result = extract_json(raw)
    print(f"  ✅ {len(result)} topics assignés à des SubUnits")
    return result


def step2_group_into_units(subunit_map: dict) -> dict:
    """
    Étape 2 : Regroupe les SubUnits en Units thématiques.
    Retourne : { "Unit Name": ["SubUnit1", "SubUnit2", ...], ... }
    """
    print("\n📡 Étape 2 — Regroupement des SubUnits en Units thématiques...")

    unique_subunits = list(set(subunit_map.values()))
    subunits_list   = "\n".join([f"- {s}" for s in unique_subunits])

    prompt = f"""You are an English language curriculum designer.

Below is a list of SubUnit names from an A1 English learning platform.

Your task:
Group these SubUnits into thematic Units. Each Unit should contain between 5 and 10 SubUnits
that share a common broad theme.

Rules:
- Create between 20 and 30 Units total
- Each Unit must have a clear, broad thematic title
- Every SubUnit must appear in exactly one Unit
- Respond ONLY with a valid JSON object, no explanation, no markdown backticks

Format:
{{
  "Unit Title Here": ["SubUnit1", "SubUnit2", "SubUnit3", ...],
  ...
}}

SubUnits to group:
{subunits_list}"""

    raw    = call_groq(prompt)
    result = extract_json(raw)
    print(f"  ✅ {len(result)} Units créées")
    return result


def build_final_structure(topics: list[dict], subunit_map: dict, unit_map: dict) -> dict:
    """
    Construit la structure finale :
    {
      "Unit Title": {
        "SubUnit Name": ["topic1", "topic2", ...],
        ...
      }
    }
    """
    subunit_to_unit = {}
    for unit_name, subunits in unit_map.items():
        for sub in subunits:
            subunit_to_unit[sub] = unit_name

    structure    = {}
    unclassified = []

    for t in topics:
        topic   = t["topic"]
        subunit = subunit_map.get(topic)

        if not subunit:
            unclassified.append(topic)
            continue

        unit = subunit_to_unit.get(subunit, "Other Topics")

        if unit not in structure:
            structure[unit] = {}
        if subunit not in structure[unit]:
            structure[unit][subunit] = []

        structure[unit][subunit].append(topic)

    if unclassified:
        print(f"  ⚠️  {len(unclassified)} topics non classifiés → ajoutés dans 'Other Topics'")
        structure.setdefault("Other Topics", {}).setdefault("Miscellaneous", []).extend(unclassified)

    return structure


def print_summary(structure: dict):
    """Affiche un résumé de la classification."""
    total_units    = len(structure)
    total_subunits = sum(len(subs) for subs in structure.values())
    total_texts    = sum(
        len(texts)
        for subs in structure.values()
        for texts in subs.values()
    )

    print("\n" + "─" * 55)
    print(f"✅  Classification terminée !")
    print(f"    Units créées     : {total_units}")
    print(f"    SubUnits créées  : {total_subunits}")
    print(f"    Textes classifiés: {total_texts}")
    print()

    for unit_name, subunits in structure.items():
        print(f"  📁 {unit_name}  ({len(subunits)} subunits)")
        for sub_name, texts in subunits.items():
            print(f"       └── {sub_name}  ({len(texts)} texte(s))")


def main():
    print("🚀  Démarrage de la classification A1 avec Groq...")

    topics = load_a1_topics(DATASET_PATH)
    print(f"📂  {len(topics)} topics A1 chargés")

    subunit_map = step1_assign_subunits(topics)
    time.sleep(3)

    unit_map = step2_group_into_units(subunit_map)

    structure = build_final_structure(topics, subunit_map, unit_map)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    print(f"\n💾  Résultat sauvegardé dans : {OUTPUT_PATH}")
    print_summary(structure)
    print()
    print("👉  Lance maintenant : python scripts/load_texts.py")


if __name__ == "__main__":
    main()