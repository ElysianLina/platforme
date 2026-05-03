#!/usr/bin/env python3
"""
Générateur TTS - Version PROCESSUS SÉPARÉS
Chaque fichier est généré dans un processus indépendant → aucun blocage possible
"""

import json
import shutil
import os
import time
import subprocess
import sys
from pathlib import Path
from multiprocessing import Process, Queue


def generate_single_in_process(sentence, mp3_path, queue):
    """Fonction exécutée dans un processus séparé"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.setProperty('volume', 0.9)
        
        # Voix anglaise
        voices = engine.getProperty('voices')
        for v in voices:
            if 'english' in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        
        engine.save_to_file(sentence, str(mp3_path))
        engine.runAndWait()
        engine.stop()
        
        # Vérifier succès
        if Path(mp3_path).exists() and Path(mp3_path).stat().st_size > 0:
            queue.put(("success", mp3_path.stat().st_size))
        else:
            queue.put(("error", "Fichier vide ou inexistant"))
            
    except Exception as e:
        queue.put(("error", str(e)))


def generate_with_processes(json_path):
    """Génère avec un processus par fichier"""
    
    try:
        import pyttsx3
    except ImportError:
        print("❌ pip install pyttsx3")
        return False
    
    json_file = Path(json_path).resolve()
    print(f"🔍 Recherche: {json_file}")
    
    if not json_file.exists():
        print(f"❌ Fichier non trouvé")
        return False
    
    out_path = json_file.parent / "audio_generated"
    out_path.mkdir(exist_ok=True)
    
    # Espace disque
    total, used, free = shutil.disk_usage(out_path.anchor)
    print(f"💾 Espace: {free // (1024*1024)} MB libre")
    
    # Charger JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        exercises = json.load(f)
    print(f"📚 {len(exercises)} exercices\n")
    
    # Générer chaque fichier dans un processus séparé
    success = 0
    failed = []
    
    for i, ex in enumerate(exercises, 1):
        sentence = ex['sentence']
        name = f"Unit{ex['unit']}_{ex['sub_unit']}_{ex['theme'].replace(' ', '_').replace('/', '_')}"
        mp3_path = out_path / f"{name}.mp3"
        
        print(f"[{i}/{len(exercises)}] {name[:40]}...")
        print(f"    📝 {sentence[:50]}...")
        
        # Skip si déjà existant
        if mp3_path.exists() and mp3_path.stat().st_size > 0:
            print(f"    ⏭️ Déjà existant ({mp3_path.stat().st_size//1024} KB)")
            success += 1
            continue
        
        # Créer processus séparé
        queue = Queue()
        p = Process(target=generate_single_in_process, 
                   args=(sentence, str(mp3_path), queue))
        p.start()
        
        # Attendre avec timeout (max 10 secondes par fichier)
        p.join(timeout=10)
        
        if p.is_alive():
            # Bloqué → tuer le processus
            print(f"    ⚠️ Timeout! Redémarrage...")
            p.terminate()
            p.join()
            failed.append((i, name, "Timeout"))
        else:
            # Vérifier résultat
            try:
                status, result = queue.get_nowait()
                if status == "success":
                    print(f"    ✅ {result//1024} KB")
                    success += 1
                else:
                    print(f"    ❌ {result}")
                    failed.append((i, name, result))
            except:
                # Vérifier fichier quand même
                if mp3_path.exists() and mp3_path.stat().st_size > 0:
                    print(f"    ✅ {mp3_path.stat().st_size//1024} KB")
                    success += 1
                else:
                    print(f"    ❌ Erreur inconnue")
                    failed.append((i, name, "Inconnue"))
        
        # Pause courte entre fichiers
        time.sleep(0.3)
    
    # Résumé
    print(f"\n{'='*50}")
    print(f"📊 RÉSUMÉ:")
    print(f"   ✅ {success}/{len(exercises)} réussis")
    if failed:
        print(f"   ❌ {len(failed)} échoués:")
        for idx, name, reason in failed[:5]:
            print(f"      [{idx}] {name[:30]}... ({reason})")
    print(f"   📂 {out_path.absolute()}")
    print(f"{'='*50}")
    
    return len(failed) == 0


def main():
    print("="*50)
    print("🎯 TTS - PROCESSUS SÉPARÉS (Anti-Blocage Total)")
    print("="*50)
    
    json_path = r"C:\Users\HP\Desktop\platform\backend\data\speaking\speaking_exercises_a1.json"
    
    generate_with_processes(json_path)
    input("\nEntrée pour fermer...")


if __name__ == "__main__":
    main()