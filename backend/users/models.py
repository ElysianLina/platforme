import re
import traceback

from django.db import models
import uuid
from django.utils import timezone

class Learner(models.Model):
    CEFR_CHOICES = [
        ('A1', 'A1 - Débutant'),
        ('A2', 'A2 - Élémentaire'),
        ('B1', 'B1 - Intermédiaire'),
        ('B2', 'B2 - Avancé'),
        ('C1', 'C1 - Autonome'),
       
    ]
    
    learner_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Stockera le hash
    phone = models.CharField(max_length=20, null=True, blank=True)
    cefr_level = models.CharField(
        max_length=2, 
        choices=CEFR_CHOICES, 
        default='A1',
        db_column='cefrlevel'
    )
    progress = models.IntegerField(default=0)
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    picture = models.URLField(max_length=500, null=True, blank=True)
    class Meta:
        db_table = 'learner'

    def __str__(self):
        return f"{self.name} ({self.email})"
    
#  PRÉFÉRENCES LEARNER
# ─────────────────────────────────────────────
 
class LearnerPreferences(models.Model):
    """
    Préférences collectées lors du quiz d'onboarding (preferences.html).
    Liées au Learner via OneToOneField.
    Créées ou mises à jour via update_or_create dans save_preferences_api.
    """
 
    REASON_CHOICES = [
        ('voyage',         'Travel'),
        ('travail',        'Work'),
        ('etudes',         'Studies'),
        ('culture',        'Culture'),
        ('communication',  'Communication'),
        ('Défi personnel', 'Personal challenge'),
    ]
 
    STYLE_CHOICES = [
        ('video', 'Video'),
        ('texte', 'Text'),
        ('audio', 'Audio'),
        ('autre', 'Other'),
    ]
 
    GOAL_CHOICES = [
        ('5min',  '5 min/day'),
        ('10min', '10 min/day'),
        ('15min', '15 min/day'),
        ('25min', '25 min/day'),
    ]
 
    learner = models.OneToOneField(
        Learner,
        on_delete=models.CASCADE,
        related_name='preferences',
        primary_key=True
    )
    # Étape 1 : Raison d'apprentissage
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        blank=True,
        help_text="Pourquoi l'apprenant veut apprendre l'anglais"
    )
    # Étape 2 : Centres d'intérêt (liste JSON)
    interests = models.JSONField(
        default=list,
        help_text="Ex: ['voyage-tourisme', 'sport', 'business']"
    )
    other_interest = models.CharField(
        max_length=200,
        blank=True,
        help_text="Intérêt personnalisé saisi dans le champ 'Other'"
    )
    # Étape 3 : Style d'apprentissage
    learning_style = models.CharField(
        max_length=20,
        choices=STYLE_CHOICES,
        blank=True,
        help_text="Style préféré : video, texte, audio ou autre"
    )
    other_style = models.CharField(
        max_length=200,
        blank=True,
        help_text="Style personnalisé saisi dans le champ 'Other'"
    )
    # Étape 4 : Objectif journalier
    daily_goal = models.CharField(
        max_length=10,
        choices=GOAL_CHOICES,
        blank=True,
        help_text="Temps quotidien choisi : 5min, 10min, 15min ou 25min"
    )
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = 'learner_preferences'
 
    def __str__(self):
        return f"Prefs of {self.learner.name} | {self.reason} | {self.daily_goal}"
#  STRUCTURE : UNIT → SUBUNIT
# ─────────────────────────────────────────────
 
class Unit(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'),
        ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'),
    ]
 
    title = models.CharField(max_length=200)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    order = models.PositiveIntegerField(default=0)
 
    class Meta:
        db_table = 'unit'
        ordering = ['level', 'order']
 
    def __str__(self):
        return f"[{self.level}] {self.title}"
 
 
class SubUnit(models.Model):
    unit  = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='subunits'
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
 
    class Meta:
        db_table = 'subunit'
        ordering = ['order']
 
    def __str__(self):
        return f"{self.unit.title} / {self.title}"
 
 
# ─────────────────────────────────────────────
#  READING ACTIVITY
# ─────────────────────────────────────────────
 
class ReadingText(models.Model):
    """
    Plusieurs textes stockés par SubUnit (ForeignKey).
    → Tous stockés en base
    → 1 seul affiché à l'apprenant (le premier is_valid=True)
    Plus tard : grammar, vocabulary... aussi liés à SubUnit.
    """
    sub_unit       = models.ForeignKey(
        SubUnit,
        on_delete=models.CASCADE,
        related_name='reading_texts'   # subunit.reading_texts.all()
    )
    topic          = models.CharField(max_length=300)
    content        = models.TextField()
    is_valid       = models.BooleanField(default=False)
    coverage_score = models.FloatField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'reading_text'
 
    def __str__(self):
        return f"{self.topic} ({self.sub_unit})"
 
    @property
    def level(self):
        return self.sub_unit.unit.level
 
 
class ReadingQuestion(models.Model):
    """
    Questions générées pour un ReadingText.
    Générées une seule fois, stockées et réutilisées.
    """
    QUESTION_TYPES = [
        ('true_false',      'True / False'),
        ('multiple_choice', 'Multiple Choice'),
        ('fill_blank',      'Fill in the Blank'),
    ]
 
    text     = models.ForeignKey(
        ReadingText,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question = models.TextField()
    type     = models.CharField(max_length=20, choices=QUESTION_TYPES)
 
    # true_false      → ["True", "False"]
    # multiple_choice → ["apple", "car", "book", "run"]
    # fill_blank      → null
    choices  = models.JSONField(null=True, blank=True)
    answer   = models.CharField(max_length=255)
 
    class Meta:
        db_table = 'reading_question'
 
    def __str__(self):
        return f"[{self.type}] {self.question[:60]}"
    

    # ─────────────────────────────────────────────
#  TEST DE NIVEAU CEFR
# ─────────────────────────────────────────────

class Niveau(models.Model):
    """
    Les 6 niveaux CEFR avec leur seuil de réussite.
    Pré-remplis via migration : A1→C2.
    """
    NIVEAU_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'),
        ('B1', 'B1'), ('B2', 'B2'),
        ('C1', 'C1'), ('C2', 'C2'),
    ]

    id              = models.CharField(max_length=2, primary_key=True, choices=NIVEAU_CHOICES)
    nom             = models.CharField(max_length=50)
    description     = models.TextField(blank=True)
    ordre           = models.PositiveIntegerField()
    seuil_reussite  = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=0.60,
        help_text="Score minimum pour valider ce niveau (ex: 0.60 = 60%)"
    )

    class Meta:
        db_table = 'cefr_niveau'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.id} - {self.nom}"


class TestAudio(models.Model):
    """
    Fichiers audio EXCLUSIVEMENT pour le test de niveau CEFR.
    Un même audio peut être utilisé dans plusieurs questions du test.
    Le champ niveau peut être rempli manuellement (si déjà connu) sinon par cefr_detector.py.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fichier         = models.CharField(
        max_length=255,
        help_text="Ex: spontaneous-speech-en-71660.mp3"
    )
    transcription   = models.TextField(
        help_text="Texte transcrit de l'audio"
    )
    niveau_detecte  = models.ForeignKey(
        Niveau,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='test_audios',
        help_text="Peut être rempli manuellement ou automatiquement par cefr_detector.py"
    )
    duree_secondes  = models.PositiveIntegerField(null=True, blank=True)
    sujet           = models.CharField(
        max_length=200, blank=True,
        help_text="Ex: Sleep routine, Technology privacy..."
    )

    class Meta:
        db_table = 'cefr_test_audio'
        ordering = ['niveau_detecte__ordre']

    def __str__(self):
        niveau = self.niveau_detecte_id or '?'
        return f"[{niveau}] {self.sujet or self.fichier}"


class Question(models.Model):
    """
    Banque de questions du test CEFR.
    Couvre grammaire, vocabulaire et listening.
    """
    CATEGORIE_CHOICES = [
        ('grammar',    'Grammaire'),
        ('vocabulary', 'Vocabulaire'),
        ('listening',  'Listening'),
    ]
    TYPE_CHOICES = [
        ('fill_blank',   'Compléter avec propositions (1 ou 2 trous)'),
        ('manual_input', 'Saisie manuelle'),
        ('mcq',          'QCM classique'),
    ]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    niveau            = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    categorie         = models.CharField(
        max_length=20, choices=CATEGORIE_CHOICES,
        help_text="grammar | vocabulary | listening"
    )
    type              = models.CharField(
        max_length=20, choices=TYPE_CHOICES,
        help_text="fill_blank | manual_input | mcq"
    )
    enonce            = models.TextField(
        help_text="Phrase avec ___ pour les trous. Ex: He ___ the newspaper every day."
    )
    reponse_attendue  = models.TextField(
        help_text=(
            "Réponse correcte. Utiliser | comme séparateur :\n"
            "- 1 réponse       : 'reads'\n"
            "- 2 trous         : 'priest|professor'\n"
            "- synonymes       : 'information|data|info'\n"
            "- 2 bonnes rép.   : 'fake news|artificial intelligence'"
        )
    )
    options           = models.JSONField(
        null=True, blank=True,
        help_text="Propositions pour fill_blank et mcq. Ex: ['read','reads','readed','reading']"
    )
    audio             = models.ForeignKey(
        TestAudio,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='questions',
        help_text="Uniquement pour les questions listening"
    )
    ordre_dans_niveau = models.PositiveIntegerField(
        default=1,
        help_text="Ordre d'affichage dans le niveau (1, 2, 3...)"
    )
    points            = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'cefr_question'
        ordering = ['niveau__ordre', 'categorie', 'ordre_dans_niveau']

    def __str__(self):
        return f"[{self.niveau_id}][{self.categorie}] {self.enonce[:60]}"

    def corriger(self, reponse_donnee):
        """
        Correction automatique.
        Gère : réponse simple, double trou (|), synonymes acceptés.
        """
        attendues = [r.strip().lower() for r in self.reponse_attendue.split('|')]
        donnees   = [r.strip().lower() for r in reponse_donnee.split('|')]

        if self.type in ('mcq', 'fill_blank') and len(donnees) == 1:
            return donnees[0] in attendues

        return all(d in attendues for d in donnees)


class Test(models.Model):
    """
    Session de test CEFR d'un apprenant.
    scores_par_niveau stocke le % obtenu à chaque niveau.
    La logique des 60% est appliquée dans calculer_niveau_final().
    """
    STATUT_CHOICES = [
        ('en_cours',  'En cours'),
        ('termine',   'Terminé'),
        ('abandonne', 'Abandonné'),
    ]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner           = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='cefr_tests'
    )
    date_debut        = models.DateTimeField(auto_now_add=True)
    date_fin          = models.DateTimeField(null=True, blank=True)
    niveau_final      = models.ForeignKey(
        Niveau,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tests_termines',
        help_text="Résultat calculé à la fin du test"
    )
    score_final       = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Score global en %"
    )
    scores_par_niveau = models.JSONField(
        default=dict,
        help_text='Ex: {"A1": 100, "A2": 80, "B1": 60, "B2": 40, "C1": 20, "C2": 0}'
    )
    questions_ordre   = models.JSONField(
        default=list,
        help_text='Liste ordonnée des UUIDs de questions pour ce test'
    )
    statut            = models.CharField(
        max_length=20, choices=STATUT_CHOICES,
        default='en_cours'
    )

    class Meta:
        db_table = 'cefr_test'
        ordering = ['-date_debut']

    def __str__(self):
        return f"Test {self.learner.name} ({self.learner.learner_id}) → {self.niveau_final_id or 'en cours'}"

    def calculer_niveau_final(self):
        """
        Niveau final = dernier niveau où score >= seuil_reussite.
        Ex : A1=100%, A2=80%, B1=60%, B2=40% → niveau final = B1
        """
        niveaux = Niveau.objects.order_by('ordre')
        niveau_final = niveaux.first()

        for niveau in niveaux:
            score        = self.scores_par_niveau.get(niveau.id, 0)
            seuil        = float(niveau.seuil_reussite) * 100
            if score >= seuil:
                niveau_final = niveau
            else:
                break

        return niveau_final


class Reponse(models.Model):
    """
    Réponse donnée par l'apprenant pour chaque question du test.
    La correction est automatique à la sauvegarde.
    """
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test              = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='reponses')
    question          = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    reponse_donnee    = models.TextField()
    est_correcte      = models.BooleanField(default=False)
    points_obtenus    = models.PositiveIntegerField(default=0)
    temps_reponse_sec = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Temps pris pour répondre en secondes (optionnel)"
    )

    class Meta:
        db_table        = 'cefr_reponse'
        unique_together = ['test', 'question']

    def __str__(self):
        statut = '✓' if self.est_correcte else '✗'
        return f"{self.test} | {self.question.enonce[:30]} | {statut}"

    def save(self, *args, **kwargs):
        """Auto-correction à la sauvegarde."""
        self.est_correcte   = self.question.corriger(self.reponse_donnee)
        self.points_obtenus = self.question.points if self.est_correcte else 0
        super().save(*args, **kwargs)

class ReadingExerciseResult(models.Model):
    """
    Stocke le résultat de la PREMIÈRE soumission d'un exercice de lecture.
    Un learner ne peut avoir qu'un seul résultat par ReadingText (unique_together).
    Si le learner refait l'exercice après Ctrl+R, on retourne ce résultat initial.
    """

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='reading_exercise_results',
    )

    reading_text = models.ForeignKey(
        ReadingText,
        on_delete=models.CASCADE,
        related_name='results',
    )

    score = models.IntegerField()

    correct_count = models.IntegerField()

    total = models.IntegerField()

    results_json = models.JSONField()

    # ✅ NOUVEAU : Champ feedback
    feedback = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short feedback message in English (2-3 words)"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'reading_exercise_result'
        unique_together = ['learner', 'reading_text']

    def __str__(self):
        return f"{self.learner.name} | {self.reading_text.topic} | {self.score}%"

    def generate_feedback(self):
        """Génère un feedback court en anglais selon le score."""
        if self.score >= 90:
            return "Excellent work!"
        elif self.score >= 80:
            return "Very good!"
        elif self.score >= 70:
            return "Good job!"
        elif self.score >= 60:
            return "Well done!"
        elif self.score >= 50:
            return "Keep trying!"
        elif self.score >= 40:
            return "Need practice!"
        else:
            return "Try more!"

    def save(self, *args, **kwargs):
        """Auto-génère le feedback avant sauvegarde."""
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)

# ─────────────────────────────────────────────
#  TEXTES GÉNÉRÉS PAR GAI (Practice)
# ─────────────────────────────────────────────

class GeneratedReadingText(models.Model):
    """
    Texte de pratique généré par l'IA (GAI).
    Séparé de ReadingText pour ne pas polluer les contenus curatés.
    Lié au texte ORIGINAL (ReadingText) qui a déclenché la génération.
    Lié au LEARNER pour que chaque apprenant ait ses propres textes générés.
    """
    original_text = models.ForeignKey(
        ReadingText,
        on_delete=models.CASCADE,
        related_name='generated_texts',
        help_text="Le texte ReadingText original qui a inspiré ce texte généré"
    )
    sub_unit = models.ForeignKey(
        SubUnit,
        on_delete=models.CASCADE,
        related_name='generated_reading_texts'
    )
    # ✅ NOUVEAU : Lier le texte généré au learner qui l'a demandé
    learner = models.ForeignKey(
        Learner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reading_texts',
        help_text="L'apprenant qui a généré ce texte (null = anonyme)"
    )
    topic      = models.CharField(max_length=300)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'generated_reading_text'
 
    def __str__(self):
        return f"[GAI] {self.topic} ({self.sub_unit})"


class GeneratedReadingQuestion(models.Model):
    """
    Questions générées par l'IA pour un GeneratedReadingText.
    """
    QUESTION_TYPES = [
        ('true_false',      'True / False'),
        ('multiple_choice', 'Multiple Choice'),
        ('fill_blank',      'Fill in the Blank'),
    ]

    generated_text = models.ForeignKey(
        GeneratedReadingText,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question = models.TextField()
    type     = models.CharField(max_length=20, choices=QUESTION_TYPES)
    choices  = models.JSONField(null=True, blank=True)
    answer   = models.CharField(max_length=255)

    class Meta:
        db_table = 'generated_reading_question'

    def __str__(self):
        return f"[{self.type}] {self.question[:60]}"
    

# ─────────────────────────────────────────────
#  RÉSULTATS DES EXERCICES GÉNÉRÉS (GAI)
# ─────────────────────────────────────────────

class GeneratedExerciseResult(models.Model):
    """
    Stocke le résultat d'un exercice généré par IA pour un learner.
    La note sur 10 est calculée automatiquement en comparant avec les réponses correctes.
    """

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='gen_reading_exercise_results',  # ← MODIFIÉ
    )

    # Clé étrangère vers le texte original
    original_text = models.ForeignKey(
        ReadingText,
        on_delete=models.CASCADE,
        related_name='gen_results_by_original',
        help_text="Le texte ORIGINAL qui a généré cet exercice"
    )

    # Texte généré spécifique
    generated_text = models.ForeignKey(
        GeneratedReadingText,
        on_delete=models.CASCADE,
        related_name='gen_results',
        help_text="Le texte généré (GAI) que l'apprenant a pratiqué"
    )

    # Réponses détaillées de l'apprenant
    answers_json = models.JSONField(
        help_text="Réponses de l'apprenant: {question_id: 'réponse', ...}"
    )

    # Résultats de la correction automatique
    correct_count = models.IntegerField(
        help_text="Nombre de réponses correctes"
    )

    total_questions = models.IntegerField(
        help_text="Nombre total de questions"
    )

    score_percentage = models.IntegerField(
        help_text="Score en pourcentage (0-100)"
    )

    # Note sur 10 calculée automatiquement
    score_on_10 = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Note sur 10 calculée automatiquement (ex: 7.5/10)"
    )

    # Feedback en anglais avec message de pratique
    feedback = models.TextField(
        blank=True,
        help_text="Feedback in English encouraging more practice"
    )

    # Détails de chaque réponse (pour analyse)
    detailed_results_json = models.JSONField(
        default=list,
        help_text="Détail question par question avec comparaison"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generated_exercise_result'

    def __str__(self):
        score_display = f"{self.score_on_10}/10" if self.score_on_10 else "N/A"
        return f"{self.learner.name} | {self.generated_text.topic} | {score_display}"

    def calculate_score_on_10(self):
        """Calcule la note sur 10 à partir du pourcentage."""
        if self.total_questions > 0:
            score = (self.correct_count / self.total_questions) * 10
            return round(score, 1)
        return 0

    def generate_feedback(self):
        """Génère un feedback en anglais selon la note sur 10."""
        if self.score_on_10 is None:
            return ""
        
        score = float(self.score_on_10)
        
        if score >= 9:
            return "Excellent work! You have mastered this topic very well. Keep practicing to maintain this level!"
        elif score >= 8:
            return "Very good work! You understand this well. A bit more practice will help you reach excellence!"
        elif score >= 7:
            return "Good job! You have a solid understanding. Keep practicing to improve your accuracy!"
        elif score >= 6:
            return "Fair result. You understand the basics, but more practice will help you improve!"
        elif score >= 5:
            return "You are making progress, but need more practice with this type of text. Try again!"
        elif score >= 4:
            return "Keep practicing! Reading more texts like this will help you improve your comprehension."
        else:
            return "Don't give up! The more you practice reading, the better you will become. Try another exercise!"

    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement la note sur 10 et le feedback."""
        self.score_on_10 = self.calculate_score_on_10()
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)

# ─────────────────────────────────────────────
#  LISTENING ACTIVITY (Audio LJSpeech)
# ─────────────────────────────────────────────

class ListeningAudio(models.Model):
    """
    Stockage des fichiers audio LJSpeech avec métadonnées pédagogiques.
    Chaque audio est lié à un SubUnit et contient 10 questions de compréhension.
    """

    CONFIDENCE_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    audio_id = models.CharField(
        max_length=20, 
        primary_key=True,
        help_text="Identifiant LJSpeech unique (ex: LJ020-0093)"
    )
    sub_unit = models.ForeignKey(
        SubUnit,
        on_delete=models.CASCADE,
        related_name='listening_audios',
        help_text="Sous-unité pédagogique associée"
    )
    unit_number = models.CharField(
        max_length=2,
        help_text="Numéro d'unité pour référence rapide (ex: 01)"
    )
    unit_title = models.CharField(
        max_length=100,
        help_text="Titre de l'unité pédagogique"
    )
    subunit_key = models.CharField(
        max_length=10,
        help_text="Clé du sous-unité (ex: A1.1)"
    )
    subunit_title = models.CharField(
        max_length=100,
        help_text="Titre du sous-unité"
    )
    transcript = models.TextField(
        help_text="Transcription textuelle complète de l'audio"
    )
    audio_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Chemin vers le fichier audio"
    )
    cefr_level = models.CharField(
        max_length=2,
        help_text="Niveau CEFR de l'audio (A1, A2, B1, B2, C1)"
    )
    match_score = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Score de correspondance avec le sous-unité"
    )
    confidence = models.CharField(
        max_length=10,
        choices=CONFIDENCE_CHOICES,
        blank=True,
        help_text="Niveau de confiance de l'appariement"
    )
    vocab_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Pourcentage de vocabulaire correspondant au niveau CEFR (à remplir ultérieurement)"
    )
    duration_seconds = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Durée de l'audio en secondes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'listening_audio'
        ordering = ['unit_number', 'subunit_key']
        indexes = [
            models.Index(fields=['unit_number']),
            models.Index(fields=['cefr_level']),
            models.Index(fields=['subunit_key']),
        ]

    def __str__(self):
        return f"[{self.audio_id}] {self.subunit_title} ({self.cefr_level})"

    @property
    def level(self):
        """Retourne le niveau CEFR pour compatibilité avec le reste du système."""
        return self.cefr_level


class ListeningQuestion(models.Model):
    """
    Questions de compréhension orale associées à un audio LJSpeech.
    10 questions par audio : true_false, mcq, word_order, fill_blank, synonym, grammar, vocabulary.
    """

    QUESTION_TYPE_CHOICES = [
        ('true_false', 'True / False'),
        ('mcq', 'Multiple Choice Question'),
        ('word_order', 'Word Ordering'),
        ('fill_blank', 'Fill in the Blank'),
        ('synonym', 'Synonym'),
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
    ]

    id = models.AutoField(primary_key=True)
    audio = models.ForeignKey(
        ListeningAudio,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="Audio LJSpeech associé"
    )
    question_order = models.PositiveIntegerField(
        help_text="Ordre de la question dans l'audio (1-10)"
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        help_text="Type de question"
    )
    question_text = models.TextField(
        help_text="Texte de la question"
    )
    choices = models.JSONField(
        null=True, 
        blank=True,
        help_text="Options pour MCQ/Fill_blank (format JSON)"
    )
    correct_answer = models.TextField(
        help_text="Réponse correcte"
    )
    target_word = models.CharField(
        max_length=50,
        blank=True,
        help_text="Mot cible (pour synonym/vocabulary)"
    )
    correct_order = models.JSONField(
        null=True, 
        blank=True,
        help_text="Ordre correct des mots (pour word_order)"
    )
    explanation = models.TextField(
        blank=True,
        help_text="Explication de la réponse (optionnel)"
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text="Points attribués pour cette question"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listening_question'
        ordering = ['audio', 'question_order']
        unique_together = ['audio', 'question_order']
        indexes = [
            models.Index(fields=['audio']),
            models.Index(fields=['question_type']),
        ]

    def __str__(self):
        return f"[{self.audio.audio_id}] Q{self.question_order}: {self.question_type}"

class ListeningExerciseResult(models.Model):
    """
    Stocke le résultat d'un exercice de listening pour un learner.
    Un learner ne peut avoir qu'un seul résultat par ListeningAudio (unique_together).
    """

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='listening_exercise_results',
    )
    audio = models.ForeignKey(
        ListeningAudio,
        on_delete=models.CASCADE,
        related_name='results',
    )
    score = models.IntegerField(
        help_text="Score en pourcentage (0-100)"
    )
    correct_count = models.IntegerField(
        help_text="Nombre de réponses correctes"
    )
    total = models.IntegerField(
        help_text="Nombre total de questions"
    )
    results_json = models.JSONField(
        help_text="Détail des réponses: {question_id: {'user_answer': '...', 'is_correct': True/False}, ...}"
    )
    feedback = models.CharField(
        max_length=50,
        blank=True,
        help_text="Feedback court en anglais (2-3 mots)"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listening_exercise_result'
        unique_together = ['learner', 'audio']

    def __str__(self):
        return f"{self.learner.name} | {self.audio.audio_id} | {self.score}%"

    def generate_feedback(self):
        """Génère un feedback court en anglais selon le score."""
        if self.score >= 90:
            return "Excellent work!"
        elif self.score >= 80:
            return "Very good!"
        elif self.score >= 70:
            return "Good job!"
        elif self.score >= 60:
            return "Well done!"
        elif self.score >= 50:
            return "Keep trying!"
        elif self.score >= 40:
            return "Need practice!"
        else:
            return "Try more!"

    def save(self, *args, **kwargs):
        """Auto-génère le feedback avant sauvegarde."""
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)




# ─────────────────────────────────────────────
#  WRITING ACTIVITY 
# ─────────────────────────────────────────────

class WritingExercise(models.Model):
    """Exercice de writing lié à un SubUnit."""
    
    id = models.AutoField(primary_key=True)
    sub_unit = models.ForeignKey(
        SubUnit,
        on_delete=models.CASCADE,
        related_name='writing_exercises'
    )
    
    instruction = models.TextField()
    guiding_points = models.JSONField(default=list)
    word_count_target = models.CharField(max_length=50, default="60-80 words")
    
    model_answer_text = models.TextField()
    model_answer_vocabulary = models.JSONField(default=list)
    model_answer_grammar = models.JSONField(default=list)
    
    # Pour l'évaluation
    key_vocabulary = models.JSONField(default=list)
    grammar_patterns = models.JSONField(default=list, help_text="Patterns grammaticaux attendus")
    forbidden_words = models.JSONField(default=list, help_text="Mots à éviter")
    
    difficulty = models.CharField(max_length=2, default='A1')
    theme = models.TextField(blank=True)
    unit_title = models.CharField(max_length=200, blank=True)
    subunit_title = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'writing_exercise'
        ordering = ['sub_unit__unit__order', 'sub_unit__order']
        unique_together = ['sub_unit']
    
    def __str__(self):
        return f"[{self.difficulty}] {self.subunit_title or self.instruction[:50]}"


class WritingExerciseResult(models.Model):
    """Résultat avec évaluation détaillée et feedback structuré."""
    
    learner = models.ForeignKey(
        Learner, 
        on_delete=models.CASCADE, 
        related_name='writing_exercise_results'
    )
    writing_exercise = models.ForeignKey(
        WritingExercise, 
        on_delete=models.CASCADE, 
        related_name='results'
    )
    
    submitted_text = models.TextField()
    word_count = models.IntegerField()
    
    # Scores détaillés (0-100)
    content_score = models.IntegerField(null=True, blank=True, help_text="Respect des consignes")
    vocabulary_score = models.IntegerField(null=True, blank=True)
    grammar_score = models.IntegerField(null=True, blank=True)
    length_score = models.IntegerField(null=True, blank=True)
    
    # Score global
    overall_score = models.IntegerField(null=True, blank=True)
    
    # Feedback structuré (stocké en JSON)
    feedback_data = models.JSONField(default=dict, help_text="""
    {
        'general': 'Feedback global',
        'strengths': ['Point fort 1', 'Point fort 2'],
        'improvements': ['À améliorer 1', 'À améliorer 2'],
        'vocabulary_found': ['mot1', 'mot2'],
        'vocabulary_missing': ['mot3', 'mot4'],
        'grammar_errors': ['Erreur détectée'],
        'word_count_feedback': 'Vous avez écrit X mots',
        'topic_relevance': 'Le texte est hors-sujet / sur le sujet'
    }
    """)
    
    # Métadonnées
    status = models.CharField(
        max_length=20,
        choices=[('submitted', 'Soumis'), ('evaluated', 'Évalué'), ('pending', 'En attente')],
        default='submitted'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'writing_exercise_result'
        unique_together = ['learner', 'writing_exercise']
        ordering = ['-submitted_at']
    
    def save(self, *args, **kwargs):
        """Sauvegarde simple — l'évaluation est gérée dans views.py via Ollama."""
        if self.submitted_text and not self.word_count:
            self.word_count = len(self.submitted_text.split())
        super().save(*args, **kwargs)





# ─────────────────────────────────────────────
#  SPEAKING ACTIVITY
# ─────────────────────────────────────────────

class SpeakingExercise(models.Model):
    """
    Exercice de speaking oral (lecture à voix haute) lié à un SubUnit.
    Chaque exercice contient une phrase à lire + l'audio de référence pré-généré.

    Source JSON  : backend/data/speaking/speaking-exercise-a1-json/
    Audio source : backend/data/speaking/audio_generated/
    Exemple audio: Unit01_A1.1_Morning_Customs.mp3
    """

    id = models.AutoField(primary_key=True)

    sub_unit = models.ForeignKey(
        SubUnit,
        on_delete=models.CASCADE,
        related_name='speaking_exercises',
        help_text="Sous-unité pédagogique associée"
    )

    # ── Contenu de l'exercice ──────────────────
    theme = models.CharField(
        max_length=200,
        help_text="Thème de la sous-unité (ex: Morning Customs)"
    )
    level = models.CharField(
        max_length=2,
        default='A1',
        help_text="Niveau CEFR (A1, A2, …)"
    )
    instructions = models.TextField(
        default="Read the following sentence aloud. Practice your pronunciation.",
        help_text="Consigne affichée à l'apprenant"
    )

    # ── Phrase cible ───────────────────────────
    sentence = models.TextField(
        help_text="Phrase que l'apprenant doit lire à voix haute"
    )

    # Mots de la phrase indexés pour la correction mot à mot
    # Ex: ["Every", "morning", "I", "wake", "up", "at", "seven", "o'clock", ...]
    sentence_words = models.JSONField(
        default=list,
        help_text="Liste ordonnée des mots de la phrase (générée automatiquement)"
    )

    # Catégories de vocabulaire couvertes
    vocabulary_categories = models.JSONField(
        default=list,
        help_text="Ex: ['time', 'verbs', 'home', 'feelings']"
    )

    # ── Audio de référence (pré-généré TTS) ───
    audio_filename = models.CharField(
        max_length=255,
        help_text=(
            "Nom du fichier MP3 pré-généré. "
            "Ex: Unit01_A1.1_Morning_Customs.mp3 "
            "(stocké dans backend/data/speaking/audio_generated/)"
        )
    )
    audio_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Chemin relatif complet vers l'audio de référence"
    )

    # ── Méta ──────────────────────────────────
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'speaking_exercise'
        ordering = ['sub_unit__unit__title', 'sub_unit__order']
        unique_together = ['sub_unit']          # 1 exercice par sous-unité
        indexes = [
            models.Index(fields=['level']),
           
        ]

    def __str__(self):
         return f"[{self.level}] {self.sub_unit.unit.title} – {self.theme}"

    def save(self, *args, **kwargs):
        """
        Auto-remplit sentence_words et audio_path avant sauvegarde.
        """
        # Tokeniser la phrase en mots (conserve la casse originale)
        if self.sentence and not self.sentence_words:
            import re
            self.sentence_words = re.findall(r"\S+", self.sentence)

        # Construire le chemin audio si non fourni
        if self.audio_filename and not self.audio_path:
            self.audio_path = (
                f"backend/data/speaking/audio_generated/{self.audio_filename}"
            )

        super().save(*args, **kwargs)


# ─────────────────────────────────────────────

class SpeakingExerciseResult(models.Model):
    """
    Résultat d'une tentative de speaking pour un apprenant.

    Workflow :
      1. L'apprenant enregistre sa voix  →  audio_learner_path
      2. STT transcrit l'enregistrement  →  learner_transcript
      3. Comparaison mot à mot avec sentence_words  →  word_results + scores
      4. Feedback affiché : mots erronés en rouge + audio de référence rejoué

    Un apprenant peut soumettre plusieurs tentatives (pas de unique_together strict),
    seule la dernière est affichée dans l'UI par défaut (ordering = ['-submitted_at']).
    """

    FEEDBACK_CHOICES = [
        ('excellent',  'Excellent!'),
        ('very_good',  'Very good!'),
        ('good',       'Good job!'),
        ('keep_going', 'Keep going!'),
        ('try_again',  'Try again!'),
    ]

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='speaking_exercise_results',
        help_text="Apprenant ayant soumis l'exercice"
    )
    speaking_exercise = models.ForeignKey(
        SpeakingExercise,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="Exercice de speaking concerné"
    )

    # ── Enregistrement de l'apprenant ─────────
    audio_learner_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Chemin vers l'enregistrement vocal de l'apprenant (WebM/WAV)"
    )

    # ── Transcription STT ─────────────────────
    learner_transcript = models.TextField(
        blank=True,
        help_text="Texte transcrit automatiquement depuis l'enregistrement de l'apprenant"
    )

    # ── Résultat mot à mot ────────────────────
    # Format :
    # [
    #   {"word": "Every",   "status": "correct"},
    #   {"word": "morning", "status": "correct"},
    #   {"word": "I",       "status": "wrong",   "said": "a"},
    #   {"word": "wake",    "status": "missing"},
    #   ...
    # ]
    # status ∈ { "correct", "wrong", "missing", "extra" }
    word_results = models.JSONField(
        default=list,
        help_text=(
            "Comparaison mot à mot : liste de {word, status, said?}. "
            "status ∈ correct | wrong | missing | extra"
        )
    )

    # ── Scores ────────────────────────────────
    total_words = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de mots dans la phrase de référence"
    )
    correct_words = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de mots prononcés correctement"
    )
    accuracy_score = models.IntegerField(
        default=0,
        help_text="Score de précision en % (0-100)"
    )

    # ── Feedback ──────────────────────────────
    feedback = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        blank=True,
        help_text="Feedback court généré automatiquement selon le score"
    )

    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Numéro de tentative pour cet exercice (1 = première fois)"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'speaking_exercise_result'
        ordering = ['-submitted_at']
        unique_together = ['learner', 'speaking_exercise']
        indexes = [
            models.Index(fields=['learner', 'speaking_exercise']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return (
            f"{self.learner.name} | "
            f"{self.speaking_exercise.theme} | "
            f"{self.accuracy_score}% (essai #{self.attempt_number})"
        )

    # ── Logique métier ────────────────────────

    def calculate_scores(self):
        """
        Calcule total_words, correct_words et accuracy_score
        à partir de word_results.
        """
        if not self.word_results:
            return

        ref_words = [w for w in self.word_results if w.get('status') != 'extra']
        self.total_words   = len(ref_words)
        self.correct_words = sum(1 for w in ref_words if w.get('status') == 'correct')

        if self.total_words > 0:
            self.accuracy_score = int((self.correct_words / self.total_words) * 100)

    def generate_feedback(self):
        """Feedback court selon le score de précision."""
        score = self.accuracy_score
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'very_good'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'keep_going'
        else:
            return 'try_again'

    def set_attempt_number(self):
        """Détermine le numéro de tentative pour ce learner × exercice."""
        previous = SpeakingExerciseResult.objects.filter(
            learner=self.learner,
            speaking_exercise=self.speaking_exercise,
        ).count()
        self.attempt_number = previous + 1

    def save(self, *args, **kwargs):
        """Auto-calcul des scores, feedback et numéro de tentative."""
        if self.word_results:
            self.calculate_scores()
        self.feedback = self.generate_feedback()
        if not self.pk:                     # Seulement à la création
            self.set_attempt_number()
        super().save(*args, **kwargs)


#----- GAI Speaking -----------------
class GeneratedSpeakingExercise(models.Model):
    """
    Phrase générée par l'IA (Ollama) à la demande du learner.
    """

    original_exercise = models.ForeignKey(
        'SpeakingExercise',
        on_delete=models.CASCADE,
        related_name='generated_exercises',
        help_text="L'exercice de speaking original qui a inspiré cette génération"
    )

    learner = models.ForeignKey(
        'Learner',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generated_speaking_exercises',
        help_text="L'apprenant qui a déclenché la génération"
    )

    # ── Contenu généré ─────────────────────────────────────────
    theme = models.CharField(
        max_length=200,
        help_text="Thème de la phrase générée (repris de l'exercice original)"
    )
    level = models.CharField(
        max_length=2,
        default='A1',
        help_text="Niveau CEFR (repris de l'exercice original)"
    )
    sentence = models.TextField(
        help_text="Phrase générée par l'IA que l'apprenant doit lire à voix haute"
    )
    sentence_words = models.JSONField(
        default=list,
        help_text="Liste ordonnée des mots de la phrase (générée automatiquement)"
    )
    instructions = models.TextField(
        default="Read the following sentence aloud. Practice your pronunciation.",
        help_text="Consigne affichée à l'apprenant"
    )
    
    # ✅ Champs audio
    audio_filename = models.CharField(max_length=255, blank=True)
    audio_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generated_speaking_exercise'
        ordering = ['-created_at']
        unique_together = ['original_exercise', 'learner']  # ← AJOUTER CETTE LIGNE
        indexes = [
            models.Index(fields=['original_exercise']),
            models.Index(fields=['learner']),
        ]

    def __str__(self):
        learner_name = self.learner.name if self.learner else 'Anonyme'
        return f"[GAI][{self.level}] {self.theme} — {learner_name}"

    def save(self, *args, **kwargs):
        """Auto-tokenise + génère l'audio TTS si nouveau."""
        import re
        
        # 1. Tokeniser la phrase
        if self.sentence and not self.sentence_words:
            self.sentence_words = re.findall(r'\S+', self.sentence)
        
        # 2. Sauvegarde standard (INSERT ou UPDATE)
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # 3. Générer l'audio UNIQUEMENT à la création et si pas déjà fait
        if is_new and self.sentence and not self.audio_filename:
            self._generate_audio()
            # Mettre à jour uniquement les champs audio (pas de double INSERT)
            super().save(update_fields=['audio_filename', 'audio_path'])

    def _generate_audio(self):
        """Génère le fichier audio TTS avec pyttsx3 pour cette phrase."""
        import os
        from django.conf import settings
        
        # Dossier de stockage
        audio_dir = os.path.join(
            settings.BASE_DIR,
            'data', 'speaking', 'audio_generated', 'generated'
        )
        os.makedirs(audio_dir, exist_ok=True)
        
        # Extension selon disponibilité pydub
        try:
            from pydub import AudioSegment
            ext = '.mp3'
            has_pydub = True
        except ImportError:
            ext = '.wav'
            has_pydub = False
        
        filename = f"gen_speaking_{self.id}{ext}"
        filepath = os.path.join(audio_dir, filename)
        
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Configuration voix anglaise
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower() or 'en_' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            if has_pydub:
                # WAV temporaire → MP3
                temp_wav = filepath.replace('.mp3', '.wav')
                engine.save_to_file(self.sentence, temp_wav)
                engine.runAndWait()
                
                audio = AudioSegment.from_wav(temp_wav)
                audio.export(filepath, format='mp3')
                os.remove(temp_wav)
            else:
                # WAV direct
                engine.save_to_file(self.sentence, filepath)
                engine.runAndWait()
            
            self.audio_filename = filename
            self.audio_path = os.path.join(
                'backend', 'data', 'speaking', 'audio_generated', 'generated', filename
            )
            
        except Exception as e:
            print(f"[pyttsx3] Erreur génération audio pour GeneratedSpeakingExercise {self.id}: {e}")
            import traceback
            traceback.print_exc()
            self.audio_filename = ''
            self.audio_path = ''
 
 
# ─────────────────────────────────────────────────────────────────────────────
 
class GeneratedSpeakingResult(models.Model):
    """
    Résultat d'une tentative de speaking sur une phrase GÉNÉRÉE par l'IA.
 
    Similaire à SpeakingExerciseResult mais lié à GeneratedSpeakingExercise.
    Un learner peut soumettre plusieurs tentatives sur un même exercice généré.
    """
 
    FEEDBACK_CHOICES = [
        ('excellent',  'Excellent!'),
        ('very_good',  'Very good!'),
        ('good',       'Good job!'),
        ('keep_going', 'Keep going!'),
        ('try_again',  'Try again!'),
    ]
 
    learner = models.ForeignKey(
        'Learner',
        on_delete=models.CASCADE,
        related_name='generated_speaking_results',
        help_text="Apprenant ayant soumis l'exercice"
    )
    generated_exercise = models.ForeignKey(
        GeneratedSpeakingExercise,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="L'exercice généré par IA concerné"
    )
 
    # ── Transcription STT ─────────────────────────────────────
    learner_transcript = models.TextField(
        blank=True,
        help_text="Texte transcrit automatiquement depuis l'enregistrement de l'apprenant"
    )
 
    # ── Résultat mot à mot ────────────────────────────────────
    # Format identique à SpeakingExerciseResult.word_results
    word_results = models.JSONField(
        default=list,
        help_text=(
            "Comparaison mot à mot : liste de {word, status, said?}. "
            "status ∈ correct | wrong | missing | extra"
        )
    )
 
    # ── Scores ────────────────────────────────────────────────
    total_words = models.PositiveIntegerField(default=0)
    correct_words = models.PositiveIntegerField(default=0)
    accuracy_score = models.IntegerField(
        default=0,
        help_text="Score de précision en % (0-100)"
    )
 
    # ── Feedback ──────────────────────────────────────────────
    feedback = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        blank=True,
        help_text="Feedback court généré automatiquement selon le score"
    )
 
    submitted_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'generated_speaking_result'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['learner', 'generated_exercise']),
            models.Index(fields=['submitted_at']),
        ]
 
    def __str__(self):
        return (
            f"{self.learner.name} | "
            f"{self.generated_exercise.theme} (GAI) | "
            f"{self.accuracy_score}%"
        )
 
    # ── Logique métier ────────────────────────────────────────
 
    def calculate_scores(self):
        """Calcule les scores à partir de word_results."""
        if not self.word_results:
            return
        ref_words = [w for w in self.word_results if w.get('status') != 'extra']
        self.total_words   = len(ref_words)
        self.correct_words = sum(1 for w in ref_words if w.get('status') == 'correct')
        if self.total_words > 0:
            self.accuracy_score = int((self.correct_words / self.total_words) * 100)
 
    def generate_feedback(self):
        """Feedback court selon le score de précision."""
        score = self.accuracy_score
        if score >= 90:  return 'excellent'
        if score >= 75:  return 'very_good'
        if score >= 60:  return 'good'
        if score >= 40:  return 'keep_going'
        return 'try_again'
 
    def save(self, *args, **kwargs):
        """Auto-calcul des scores et du feedback."""
        if self.word_results:
            self.calculate_scores()
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)

# ─────────────────────────────────────────────
#  GRAMMAR
# ─────────────────────────────────────────────

class GrammarCourse(models.Model):
    """
    Un cours de grammaire complet (ex: L01 — Construire une phrase en anglais).
    Importé depuis un fichier JSON via import_grammar_course.py.
    Chaque cours correspond à une leçon du catalogue A1.
    """
    LEVEL_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'),
        ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'),
    ]

    CATEGORY_CHOICES = [
        ('phrases_noms_adjectifs', 'Phrases, noms, déterminants et adjectifs'),
        ('chiffres_nombres',       'Chiffres, nombres et quantités'),
        ('phrase_interrogative',   'La phrase interrogative'),
        ('difficultes',            'Quelques difficultés'),
    ]

    course_id  = models.CharField(
        max_length=100,
        unique=True,
        help_text="Ex: grammar_a1_sentence_construction"
    )
    title      = models.CharField(max_length=200)
    subtitle   = models.CharField(max_length=300, blank=True)
    level      = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='A1')
    category   = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    order      = models.PositiveIntegerField(
        default=1,
        help_text="Ordre d'affichage dans le menu Grammar (L01=1, L02=2, …)"
    )
    is_active  = models.BooleanField(
        default=True,
        help_text="False = cours masqué sur la plateforme"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grammar_course'
        ordering = ['level', 'order']

    def __str__(self):
        return f"[{self.level}] {self.title}"


class GrammarSection(models.Model):
    """
    Une section d'un cours de grammaire.
    Un cours contient plusieurs sections ordonnées :
      - type 'lesson'   → explication + exemples + did_you_know + common_errors
      - type 'tips'     → liste de Common Mistakes à éviter
      - type 'exercise' → liste d'exercices + scoring
    Le contenu complet est stocké dans le JSONField 'content'
    (évite de fragmenter la structure en dizaines de tables).
    """
    TYPE_CHOICES = [
        ('lesson',   'Lesson'),
        ('tips',     'Tips / Common Mistakes'),
        ('exercise', 'Exercise'),
    ]

    course     = models.ForeignKey(
        GrammarCourse,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    section_id = models.CharField(
        max_length=10,
        help_text="Identifiant dans le JSON : '1', '2', … '6'"
    )
    section_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title        = models.CharField(max_length=200)
    order        = models.PositiveIntegerField(
        default=0,
        help_text="Ordre d'affichage dans le cours (= section_id converti en entier)"
    )
    content = models.JSONField(
        help_text=(
            "Contenu complet de la section stocké en jsonb PostgreSQL. "
            "lesson   → {explanation, formula, key_rules, examples, did_you_know, common_errors} "
            "tips     → {explanation, mistakes} "
            "exercise → {exercises, scoring}"
        )
    )

    class Meta:
        db_table      = 'grammar_section'
        ordering      = ['order']
        unique_together = ['course', 'section_id']

    def __str__(self):
        return f"{self.course.course_id} / section {self.section_id} [{self.section_type}]"


class GrammarExerciseResult(models.Model):
    """
    Résultat d'un apprenant pour la section exercice d'un cours de grammaire.
    Un seul résultat par (learner × cours) — unique_together comme ReadingExerciseResult.
    """
    FEEDBACK_CHOICES = [
        ('excellent',     'Excellent!'),
        ('good',          'Good job!'),
        ('needs_practice','Keep practicing!'),
    ]

    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name='grammar_results'
    )
    course = models.ForeignKey(
        GrammarCourse,
        on_delete=models.CASCADE,
        related_name='results'
    )
    score        = models.IntegerField(help_text="Nombre de bonnes réponses")
    total        = models.IntegerField(help_text="Nombre total de questions")
    results_json = models.JSONField(
        help_text=(
            "Détail par question : "
            "[{id, correct, given, correct_answer, explanation}, …]"
        )
    )
    feedback     = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        blank=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'grammar_exercise_result'
        unique_together = ['learner', 'course']
        ordering      = ['-submitted_at']

    def __str__(self):
        return f"{self.learner.name} | {self.course.title} | {self.score}/{self.total}"

    def generate_feedback(self):
        """Feedback automatique selon le pourcentage."""
        pct = (self.score / self.total * 100) if self.total > 0 else 0
        if pct >= 80:
            return 'excellent'
        elif pct >= 60:
            return 'good'
        else:
            return 'needs_practice'

    def save(self, *args, **kwargs):
        """Auto-génère le feedback avant sauvegarde."""
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)


#--------------test d'evaluation ---------------
class EvaluationTest(models.Model):
    level = models.CharField(max_length=2, primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=15)
    total_questions = models.PositiveIntegerField(default=20)
    passing_score = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evaluation_test'

    def __str__(self):
        return f"[{self.level}] {self.title}"


class EvaluationQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('true_false', 'True / False'),
    ]

    SECTIONS = [
        ('listening', 'Listening Comprehension'),
        ('reading', 'Reading Comprehension'),
        ('visual', 'Visual Comprehension'),
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
    ]

    question_id = models.CharField(max_length=20, primary_key=True)
    test = models.ForeignKey(EvaluationTest, on_delete=models.CASCADE, related_name='questions')
    section = models.CharField(max_length=20, choices=SECTIONS)
    type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    audio_path = models.CharField(max_length=500, blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    reading_text = models.TextField(blank=True)
    options = models.JSONField(null=True, blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'evaluation_question'
        ordering = ['test', 'section', 'order']

    def __str__(self):
        return f"[{self.section}] {self.question_text[:50]}"


class EvaluationAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='evaluation_attempts')
    test = models.ForeignKey(EvaluationTest, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'evaluation_attempt'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.learner.name} | {self.test.level} | {self.status}"

    @property
    def total_points(self):
        return self.test.total_questions

    @property
    def percentage(self):
        if self.total_points > 0:
            return int((self.score / self.total_points) * 100)
        return 0

    @property
    def passed(self):
        return self.percentage >= self.test.passing_score

    def calculate_results(self):
        self.score = sum(a.points_earned for a in self.answers.all())
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class EvaluationAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(EvaluationAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(EvaluationQuestion, on_delete=models.CASCADE, related_name='answers')
    given_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evaluation_answer'
        unique_together = ['attempt', 'question']

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.attempt.learner.name} | {self.question.question_id} | {status}"

    def save(self, *args, **kwargs):
        if self.question and self.given_answer is not None:
            given = str(self.given_answer).strip()
            correct = str(self.question.correct_answer).strip()
            
            given_lower = given.lower()
            correct_lower = correct.lower()
            
            is_correct = False
            
            if self.question.type == 'mcq':
                # Si correct_answer est une lettre seule (A, B, C, D)
                if re.match(r'^[a-d]$', correct_lower):
                    # Comparer directement les lettres
                    given_letter = given_lower[0] if given_lower else ''
                    is_correct = given_letter == correct_lower
                else:
                    # Nettoyer les préfixes
                    clean_correct = correct_lower
                    clean_given = given_lower
                    
                    for pattern in [r'^[a-d][\.:\)]\s*', r'^\d+[\.\)]\s*', r'^[a-d]\s+']:
                        clean_correct = re.sub(pattern, '', clean_correct, flags=re.IGNORECASE)
                        clean_given = re.sub(pattern, '', clean_given, flags=re.IGNORECASE)
                    
                    clean_correct = clean_correct.strip()
                    clean_given = clean_given.strip()
                    
                    is_correct = clean_given == clean_correct
                    
                    # Fallback: comparer par index si options existent
                    if not is_correct and self.question.options:
                        try:
                            # Trouver l'index de la réponse correcte dans options
                            correct_idx = None
                            for idx, opt in enumerate(self.question.options):
                                opt_clean = re.sub(r'^[a-d][\.:\)]\s*', '', str(opt).lower(), flags=re.IGNORECASE).strip()
                                if opt_clean == clean_correct:
                                    correct_idx = idx
                                    break
                            
                            if correct_idx is not None:
                                given_letter = given_lower[0] if given_lower else ''
                                expected_letter = chr(65 + correct_idx).lower()
                                is_correct = given_letter == expected_letter
                        except:
                            pass
                        
            elif self.question.type == 'true_false':
                true_values = ['true', '1', 'yes', 'vrai']
                false_values = ['false', '0', 'no', 'faux']
                given_bool = given_lower in true_values
                correct_bool = correct_lower in true_values
                is_correct = given_bool == correct_bool
                
            elif self.question.type == 'fill_blank':
                given_parts = [p.strip().lower() for p in given.split('|') if p.strip()]
                correct_parts = [p.strip().lower() for p in correct.split('|') if p.strip()]
                
                if len(given_parts) == len(correct_parts) and len(correct_parts) > 0:
                    is_correct = all(g == c for g, c in zip(given_parts, correct_parts))
                else:
                    is_correct = False
            else:
                is_correct = given_lower == correct_lower
                
            self.is_correct = is_correct
            self.points_earned = self.question.points if is_correct else 0
                
        super().save(*args, **kwargs)



# ─────────────────────────────────────────────
#  GAI Listening
# ─────────────────────────────────────────────


class GeneratedListeningExercise(models.Model):
    """
    Exercice de listening généré par l'IA pour un learner.

    Workflow :
      1. Ollama génère une transcription sur le même thème que l'audio original.
      2. gTTS convertit la transcription en fichier MP3.
      3. Groq génère 10 questions (même types que ListeningQuestion).
      4. Le learner écoute l'audio généré et répond aux questions.

    Contrainte : unique_together = (original_audio, learner)
    → 1 seul exercice généré par learner × audio.
    """

    original_audio = models.ForeignKey(
        'ListeningAudio',
        on_delete=models.CASCADE,
        related_name='generated_exercises',
        help_text="L'audio original qui a inspiré cette génération"
    )
    learner = models.ForeignKey(
        'Learner',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generated_listening_exercises',
        help_text="L'apprenant qui a déclenché la génération"
    )

    # ── Contenu généré ─────────────────────────────────────────
    theme = models.CharField(
        max_length=200,
        help_text="Thème repris de l'audio original (subunit_title)"
    )
    cefr_level = models.CharField(
        max_length=2,
        default='A1',
        help_text="Niveau CEFR repris de l'audio original"
    )
    transcript = models.TextField(
        blank=True,
        help_text="Transcription générée par Ollama"
    )

    # ── Audio généré ───────────────────────────────────────────
    audio_filename = models.CharField(max_length=255, blank=True)
    audio_path     = models.CharField(max_length=500, blank=True)

    # ── Statut de génération ───────────────────────────────────
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('generating', 'Generating'),
        ('ready',      'Ready'),
        ('error',      'Error'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'generated_listening_exercise'
        ordering        = ['-created_at']
        unique_together = ['original_audio', 'learner']  # 1 exercice / learner / audio
        indexes = [
            models.Index(fields=['original_audio']),
            models.Index(fields=['learner']),
        ]

    def __str__(self):
        learner_name = self.learner.name if self.learner else 'Anonyme'
        return f"[GAI-Listen][{self.cefr_level}] {self.theme} — {learner_name}"


class GeneratedListeningQuestion(models.Model):
    """
    10 questions générées par Groq pour un GeneratedListeningExercise.
    Mêmes types que ListeningQuestion.
    """

    QUESTION_TYPE_CHOICES = [
        ('true_false',  'True / False'),
        ('mcq',         'Multiple Choice Question'),
        ('word_order',  'Word Ordering'),
        ('fill_blank',  'Fill in the Blank'),
        ('synonym',     'Synonym'),
        ('grammar',     'Grammar'),
        ('vocabulary',  'Vocabulary'),
    ]

    id = models.AutoField(primary_key=True)
    generated_exercise = models.ForeignKey(
        GeneratedListeningExercise,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_order  = models.PositiveIntegerField(help_text="Ordre 1-10")
    question_type   = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_text   = models.TextField()
    choices         = models.JSONField(null=True, blank=True)
    correct_answer  = models.TextField()
    target_word     = models.CharField(max_length=50, blank=True)
    correct_order   = models.JSONField(null=True, blank=True)
    explanation     = models.TextField(blank=True)
    points          = models.PositiveIntegerField(default=1)

    class Meta:
        db_table        = 'generated_listening_question'
        ordering        = ['question_order']
        unique_together = ['generated_exercise', 'question_order']

    def __str__(self):
        return f"[GenListen] Q{self.question_order}: {self.question_type}"


class GeneratedListeningResult(models.Model):
    """
    Résultat d'un learner pour un exercice listening généré.
    Un seul résultat par (learner × generated_exercise).
    """

    learner = models.ForeignKey(
        'Learner',
        on_delete=models.CASCADE,
        related_name='generated_listening_results'
    )
    generated_exercise = models.ForeignKey(
        GeneratedListeningExercise,
        on_delete=models.CASCADE,
        related_name='results'
    )
    score           = models.IntegerField(help_text="Score en % (0-100)")
    correct_count   = models.IntegerField()
    total           = models.IntegerField()
    results_json    = models.JSONField(
        help_text="Détail par question : {q_id: {user_answer, correct_answer, is_correct, ...}}"
    )
    feedback        = models.CharField(max_length=50, blank=True)
    submitted_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'generated_listening_result'
        unique_together = ['learner', 'generated_exercise']
        ordering        = ['-submitted_at']

    def __str__(self):
        return f"{self.learner.name} | GenListen | {self.score}%"

    def generate_feedback(self):
        if self.score >= 90: return "Excellent work!"
        if self.score >= 80: return "Very good!"
        if self.score >= 70: return "Good job!"
        if self.score >= 60: return "Well done!"
        if self.score >= 50: return "Keep trying!"
        if self.score >= 40: return "Need practice!"
        return "Try more!"

    def save(self, *args, **kwargs):
        self.feedback = self.generate_feedback()
        super().save(*args, **kwargs)