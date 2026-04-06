from django.core.management.base import BaseCommand
from users.models import Niveau


class Command(BaseCommand):
    help = 'Initialise les 6 niveaux CEFR (A1-C2) avec noms en anglais - À exécuter une seule fois'

    def handle(self, *args, **kwargs):
        niveaux_data = [
            ('A1', 'Beginner', 1, 0.60),
            ('A2', 'Elementary', 2, 0.60),
            ('B1', 'Intermediate', 3, 0.60),
            ('B2', 'Upper Intermediate', 4, 0.60),
            ('C1', 'Advanced', 5, 0.60),
            ('C2', 'Proficiency', 6, 0.60),
        ]

        for id_niveau, nom, ordre, seuil in niveaux_data:
            obj, created = Niveau.objects.get_or_create(
                id=id_niveau,
                defaults={'nom': nom, 'ordre': ordre, 'seuil_reussite': seuil}
            )
            if created:
                self.stdout.write(f'  ✓ Créé: {id_niveau} - {nom}')
            else:
                self.stdout.write(f'  → Existe déjà: {id_niveau}')

        self.stdout.write(self.style.SUCCESS('✓ Niveaux CEFR prêts'))