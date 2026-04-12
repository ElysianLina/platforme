from django.db import models
import uuid

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