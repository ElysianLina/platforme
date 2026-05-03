import pandas as pd
import os

# Chemin du fichier Parquet (téléchargé)
PARQUET_PATH = r"C:\Users\HP\Downloads\train-00000-of-00001.parquet"

# Chemin de sortie JSON (dans votre projet)
OUTPUT_DIR = r"C:\Users\HP\Desktop\PLATFORM\backend\data\grammar"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "grammar_dataset.json")

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lire le Parquet
print("📖 Lecture du fichier Parquet...")
df = pd.read_parquet(PARQUET_PATH)
print(f"✅ {len(df)} lignes chargées")

# Voir la structure
print(f"\n📋 Colonnes : {df.columns.tolist()}")
print(f"🔍 Aperçu :\n{df.head(3)}")

# Convertir en JSON
print(f"\n💾 Conversion en JSON...")
df.to_json(OUTPUT_FILE, orient="records", indent=2, force_ascii=False)

print(f"\n🎉 Fait ! Fichier sauvegardé :")
print(f"   {OUTPUT_FILE}")