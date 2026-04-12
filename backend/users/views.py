from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
import json
import os
from .forms import RegisterForm
from .models import Learner , Unit,LearnerPreferences, SubUnit, ReadingText, ReadingQuestion,ReadingExerciseResult
from .models import  GeneratedReadingText, GeneratedReadingQuestion,GeneratedExerciseResult
from django.contrib.auth.hashers import check_password
from django.db.models import Exists, OuterRef 

from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Niveau, Question, Test, Reponse, TestAudio
from django.shortcuts import render
from scripts.generate_practice_text import generate_and_save_reading_ex
from .models import ListeningAudio, ListeningQuestion, ListeningExerciseResult
# ============================================================
# Vue pour servir la page d'accueil (home.html)
# ============================================================
def home_view(request):
    return render(request, 'home.html')


@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data     = json.loads(request.body)
            email    = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({'success': False, 'errors': ['Email et mot de passe requis']}, status=400)
            
            try:
                learner = Learner.objects.get(email=email)
            except Learner.DoesNotExist:
                return JsonResponse({'success': False, 'errors': ['Email ou mot de passe incorrect']}, status=401)
            
            if not check_password(password, learner.password):
                return JsonResponse({'success': False, 'errors': ['Email ou mot de passe incorrect']}, status=401)
            
            return JsonResponse({
                'success': True,
                'message': 'Connexion réussie',
                'learner': {
                    'learner_id': str(learner.learner_id),
                    'name':       learner.name,
                    'email':      learner.email,
                    'cefr_level': learner.cefr_level,
                    'progress':   learner.progress
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': ['Données JSON invalides']}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [str(e)]}, status=500)
    
    return JsonResponse({'success': False, 'errors': ['Méthode non autorisée']}, status=405)


@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = RegisterForm({
                'name':             data.get('name'),
                'email':            data.get('email'),
                'password':         data.get('password'),
                'confirm_password': data.get('confirm_password'),
                'accept_terms':     data.get('accept_terms')
            })
            
            if form.is_valid():
                learner = form.save()
                return JsonResponse({
                    'success':    True,
                    'message':    'Compte créé avec succès',
                    'learner_id': learner.learner_id,
                    'name':       learner.name,
                    'email':      learner.email,
                    'cefr_level': learner.cefr_level,
                    'progress':   learner.progress
                })
            else:
                errors = []
                for field, error_list in form.errors.items():
                    for error in error_list:
                        errors.append(str(error))
                return JsonResponse({'success': False, 'errors': errors}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': ['Données invalides']}, status=400)
    
    return JsonResponse({'success': False, 'errors': ['Méthode non autorisée']}, status=405)


@csrf_exempt
def preferences_api(request):
    """
    GET /api/preferences/?learner_id=X
    Retourne les infos du learner ET ses préférences sauvegardées.
    Utile pour pré-remplir le quiz si le learner revient sur la page.
    """
    if request.method == 'GET':
        learner_id = request.GET.get('learner_id')
        if not learner_id:
            return JsonResponse({'success': False, 'errors': ['ID utilisateur manquant']}, status=400)
        try:
            learner = Learner.objects.get(learner_id=learner_id)
 
            # Récupérer les préférences si elles existent déjà
            prefs = None
            try:
                p = learner.preferences
                prefs = {
                    'reason':         p.reason,
                    'interests':      p.interests,
                    'other_interest': p.other_interest,
                    'learning_style': p.learning_style,
                    'other_style':    p.other_style,
                    'daily_goal':     p.daily_goal,
                }
            except LearnerPreferences.DoesNotExist:
                pass
 
            return JsonResponse({
                'success': True,
                'learner': {
                    'learner_id': learner.learner_id,
                    'name':       learner.name,
                    'email':      learner.email,
                    'cefr_level': learner.cefr_level,
                    'progress':   learner.progress
                },
                'preferences': prefs  # None si pas encore rempli
            })
        except Learner.DoesNotExist:
            return JsonResponse({'success': False, 'errors': ['Utilisateur non trouvé']}, status=404)
    
    return JsonResponse({'success': False, 'errors': ['Méthode non autorisée']}, status=405)

@csrf_exempt
def save_preferences_api(request):
    """
    POST /api/save-preferences/
 
    Appelé dans 2 situations :
 
    1) SAUVEGARDE PARTIELLE (étapes 1-4) — avant redirection vers le test CEFR
       Le frontend envoie reason/interests/style/daily_goal SANS cefr_level.
       → On crée/met à jour LearnerPreferences, on ne touche PAS à Learner.cefr_level.
 
    2) SAUVEGARDE COMPLÈTE (fin du quiz) — étape 6 (niveau connu ou retour test)
       Le frontend envoie tout + cefr_level.
       → On met à jour LearnerPreferences ET Learner.cefr_level.
 
    Dans les deux cas on utilise update_or_create donc un double appel
    est sans danger (idempotent).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
 
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
 
    # ── Champs obligatoires ──────────────────────────────────
    learner_id = data.get('learner_id')
    if not learner_id:
        return JsonResponse({'success': False, 'error': 'ID utilisateur manquant'}, status=400)
 
    # ── Champs optionnels ────────────────────────────────────
    cefr_level     = data.get('cefr_level')          # Optionnel (absent en sauvegarde partielle)
    reason         = data.get('reason', '')
    interests      = data.get('interests', [])
    other_interest = data.get('other_interest', '')
    learning_style = data.get('learning_style', '')
    other_style    = data.get('other_style', '')
    daily_goal     = data.get('daily_goal', '')
 
    # ── Récupérer le learner ─────────────────────────────────
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
 
    # ── Mettre à jour cefr_level SEULEMENT s'il est fourni ──
    # (cas 2 : fin du quiz avec niveau sélectionné ou détecté par le test)
    valid_levels = ['A1', 'A2', 'B1', 'B2', 'C1']
    if cefr_level:
        if cefr_level.upper() not in valid_levels:
            return JsonResponse({'success': False, 'error': f'Niveau CEFR invalide: {cefr_level}'}, status=400)
        learner.cefr_level = cefr_level.upper()
        learner.progress   = data.get('progress', learner.progress)
        learner.save()
 
    # ── Créer ou mettre à jour les préférences ───────────────
    # update_or_create garantit qu'un double appel est sans danger
    LearnerPreferences.objects.update_or_create(
        learner=learner,
        defaults={
            'reason':         reason,
            'interests':      interests if isinstance(interests, list) else [],
            'other_interest': other_interest,
            'learning_style': learning_style,
            'other_style':    other_style,
            'daily_goal':     daily_goal,
        }
    )
 
    return JsonResponse({
        'success':    True,
        'message':    'Préférences enregistrées avec succès',
        'learner_id': learner.learner_id,
        'cefr_level': learner.cefr_level,
    })


@csrf_exempt
def get_learner_api(request):
    if request.method == 'GET':
        learner_id = request.GET.get('learner_id')
        if not learner_id:
            return JsonResponse({'success': False, 'error': 'ID utilisateur manquant'}, status=400)
        try:
            learner = Learner.objects.get(learner_id=learner_id)
            return JsonResponse({
                'success': True,
                'learner': {
                    'learner_id': learner.learner_id,
                    'name':       learner.name,
                    'email':      learner.email,
                    'cefr_level': learner.cefr_level,
                    'progress':   learner.progress
                }
            })
        except Learner.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def logout_api(request):
    if request.method == 'POST':
        try:
            json.loads(request.body)
            return JsonResponse({'success': True, 'message': 'Déconnexion réussie'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def get_units_api(request):
    if request.method == 'GET':
        try:
            units      = Unit.objects.exclude(title__icontains='Other Topics').order_by('level', 'order')
            units_data = []
            
            for index, unit in enumerate(units, 1):
                subunits = SubUnit.objects.filter(
                    unit=unit,
                    reading_texts__is_valid=True
                ).distinct().order_by('order')
                
                seen_titles    = set()
                unique_subunits = []
                for subunit in subunits:
                    if subunit.title not in seen_titles:
                        seen_titles.add(subunit.title)
                        unique_subunits.append(subunit)

                unit_number = str(index).zfill(2)

                if len(unique_subunits) == 0:
                    continue

                if len(unique_subunits) == 1:
                    sub = unique_subunits[0]
                    units_data.append({
                        'id':                unit.id,
                        'title':             unit.title,
                        'level':             unit.level,
                        'order':             unit.order,
                        'display_number':    unit_number,
                        'is_single_subunit': True,
                        'subunit': {
                            'id':    sub.id,
                            'title': sub.title,
                            'code':  f"{unit.level}.1",
                            'order': sub.order
                        },
                        'subunits': []
                    })
                else:
                    subunits_data = []
                    for idx, subunit in enumerate(unique_subunits, 1):
                        subunits_data.append({
                            'id':    subunit.id,
                            'title': subunit.title,
                            'order': subunit.order,
                            'code':  f"{unit.level}.{idx}"
                        })
                    units_data.append({
                        'id':                unit.id,
                        'title':             unit.title,
                        'level':             unit.level,
                        'order':             unit.order,
                        'display_number':    unit_number,
                        'is_single_subunit': False,
                        'subunits':          subunits_data
                    })
            
            return JsonResponse({'success': True, 'units': units_data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def get_reading_exercise_api(request):
    if request.method == 'GET':
        try:
            subunit_id = request.GET.get('subunit_id')
            if not subunit_id:
                return JsonResponse({'success': False, 'error': 'subunit_id manquant'}, status=400)

            subunit      = get_object_or_404(SubUnit, id=subunit_id)
            reading_text = ReadingText.objects.filter(sub_unit=subunit, is_valid=True).first()

            if not reading_text:
                return JsonResponse({'success': False, 'error': 'Aucun texte valide trouvé'}, status=404)

            questions      = ReadingQuestion.objects.filter(text=reading_text)
            questions_data = []
            for q in questions:
                questions_data.append({
                    'id':       q.id,
                    'question': q.question,
                    'type':     q.type,
                    'choices':  q.choices,
                    'answer':   q.answer
                })

            return JsonResponse({
                'success': True,
                'text': {
                    'id':      reading_text.id,
                    'topic':   reading_text.topic,
                    'content': reading_text.content,
                    'level':   reading_text.level,
                    'coverage_score': reading_text.coverage_score,  
                },
                'questions': questions_data
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def submit_exercise_api(request):
    if request.method == 'POST':
        try:
            data       = json.loads(request.body)
            answers    = data.get('answers', {})
            text_id    = data.get('text_id')
            learner_id = data.get('learner_id')
            print(f'🔴 SUBMIT: text_id={text_id}, learner_id={learner_id}')
            if not text_id:
                return JsonResponse({'success': False, 'error': 'text_id manquant'}, status=400)

            reading_text = get_object_or_404(ReadingText, id=text_id)

            # ── Récupérer le learner si fourni ──────────────────────
            learner = None
            if learner_id:
                try:
                    learner = Learner.objects.get(learner_id=learner_id)
                except Learner.DoesNotExist:
                    pass

            # ── Vérifier si déjà soumis (résultat existant en DB) ──
            if learner:
                existing = ReadingExerciseResult.objects.filter(
                    learner=learner,
                    reading_text=reading_text
                ).first()

                if existing:
                    # Retourner le résultat initial sans recorriger
                    return JsonResponse({
                        'success':       True,
                        'already_done':  True,
                        'score':         existing.score,
                        'correct_count': existing.correct_count,
                        'total':         existing.total,
                        'results':       existing.results_json,
                        'feedback':      existing.feedback  # ✅ AJOUT
                    })

            # ── Correction des réponses ─────────────────────────────
            questions     = ReadingQuestion.objects.filter(text=reading_text)
            correct_count = 0
            total         = 0
            results       = []

            for question in questions:
                question_id            = str(question.id)
                user_answer            = answers.get(question_id, '').strip()
                total                 += 1
                user_answer_display    = user_answer
                correct_answer_display = question.answer

                if question.type == 'true_false':
                    correct = user_answer.lower() == question.answer.lower()

                elif question.type == 'multiple_choice':
                    correct_ans = question.answer
                    if question.choices and correct_ans in question.choices:
                        correct_index          = question.choices.index(correct_ans)
                        letter                 = chr(65 + correct_index)
                        correct_answer_display = f"{letter}. {correct_ans}"
                        if user_answer and user_answer[0].upper() in 'ABCD':
                            letter_given = user_answer[0].upper()
                            idx          = ord(letter_given) - 65
                            if idx < len(question.choices):
                                actual_answer       = question.choices[idx]
                                user_answer_display = f"{letter_given}. {actual_answer}"
                                correct             = actual_answer.lower() == correct_ans.lower()
                            else:
                                correct = False
                        else:
                            correct = user_answer.lower() == correct_ans.lower()
                    else:
                        correct = user_answer.lower() == question.answer.lower()

                else:  # fill_blank
                    correct                = user_answer.lower() == question.answer.lower()
                    correct_answer_display = question.answer

                if correct:
                    correct_count += 1

                results.append({
                    'question_id':    question_id,
                    'correct':        correct,
                    'user_answer':    user_answer_display,
                    'correct_answer': correct_answer_display
                })

            score = round((correct_count / total) * 100) if total > 0 else 0

            # ── Sauvegarder le résultat en DB (première soumission) ─
            feedback_message = ""  # ✅ AJOUT
            if learner:
                result = ReadingExerciseResult.objects.create(
                    learner=learner,
                    reading_text=reading_text,
                    score=score,
                    correct_count=correct_count,
                    total=total,
                    results_json=results
                    # feedback est auto-généré dans save()
                )
                feedback_message = result.feedback  # ✅ Récupérer le feedback généré
            else:
                # Générer le feedback même sans learner (pour les visiteurs)
                feedback_message = get_feedback_message(score)  # ✅

            return JsonResponse({
                'success':       True,
                'already_done':  False,
                'score':         score,
                'correct_count': correct_count,
                'total':         total,
                'results':       results,
                'feedback':      feedback_message  # ✅ AJOUT
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


# ✅ NOUVELLE FONCTION : Génère le feedback pour les visiteurs (sans learner)
def get_feedback_message(score):
    """Génère un feedback court en anglais selon le score."""
    if score >= 90:
        return "Excellent work!"
    elif score >= 80:
        return "Very good!"
    elif score >= 70:
        return "Good job!"
    elif score >= 60:
        return "Well done!"
    elif score >= 50:
        return "Keep trying!"
    elif score >= 40:
        return "Need practice!"
    else:
        return "Try more!"


# ============================================================
# VUES CEFR TEST
# ============================================================

def get_learner_from_request(request):
    try:
        body       = json.loads(request.body) if request.body else {}
        learner_id = body.get('learner_id') or request.GET.get('learner_id')
        if not learner_id:
            return None, JsonResponse({'error': 'learner_id manquant'}, status=400)
        learner = Learner.objects.get(learner_id=learner_id)
        return learner, None
    except Learner.DoesNotExist:
        return None, JsonResponse({'error': 'Utilisateur introuvable'}, status=404)
    except Exception as e:
        return None, JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def demarrer_test(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    learner, err = get_learner_from_request(request)
    if err:
        return err
    
    test_en_cours = Test.objects.filter(learner=learner, statut='en_cours').first()
    if test_en_cours:
        return JsonResponse({'message': 'Un test est déjà en cours', 'test_id': str(test_en_cours.id)}, status=400)
    
    test                 = Test.objects.create(learner=learner, statut='en_cours')
    questions_selection  = []
    for niveau_id in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        try:
            niveau    = Niveau.objects.get(id=niveau_id)
            questions = list(Question.objects.filter(niveau=niveau).order_by('ordre_dans_niveau')[:5])
            questions_selection.extend(questions)
        except Niveau.DoesNotExist:
            continue
    
    test.questions_ordre = [str(q.id) for q in questions_selection]
    test.save()
    
    return JsonResponse({
        'success':         True,
        'test_id':         str(test.id),
        'total_questions': len(questions_selection),
        'message':         'Test démarré'
    }, status=201)


@csrf_exempt
def get_question(request, test_id, question_index):
    learner_id = request.GET.get('learner_id')
    if not learner_id:
        return JsonResponse({'error': 'learner_id manquant'}, status=400)
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)

    test = get_object_or_404(Test, id=test_id, learner=learner)
    if test.statut != 'en_cours':
        return JsonResponse({'error': 'Test terminé ou abandonné'}, status=400)
    
    questions_ordre = test.questions_ordre
    if question_index >= len(questions_ordre):
        return JsonResponse({'error': 'Index invalide'}, status=400)
    
    question           = get_object_or_404(Question, id=questions_ordre[question_index])
    reponse_existante  = Reponse.objects.filter(test=test, question=question).first()
    
    data = {
        'index': question_index,
        'total': len(questions_ordre),
        'question': {
            'id':        str(question.id),
            'enonce':    question.enonce,
            'type':      question.type,
            'categorie': question.categorie,
            'niveau':    question.niveau_id,
            'options':   question.options,
            'points':    question.points,
        },
        'deja_repondu':       bool(reponse_existante),
        'reponse_precedente': reponse_existante.reponse_donnee if reponse_existante else None,
        'audio': None
    }
    
    if question.audio:
        data['audio'] = {
            'fichier': question.audio.fichier,
            'duree':   question.audio.duree_secondes,
            'sujet':   question.audio.sujet
        }
    
    return JsonResponse(data)


@csrf_exempt
def soumettre_reponse(request, test_id, question_index):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        body = json.loads(request.body)
    except:
        body = {}
    
    learner_id = body.get('learner_id')
    if not learner_id:
        return JsonResponse({'error': 'learner_id manquant'}, status=400)
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)
    
    test = get_object_or_404(Test, id=test_id, learner=learner)
    if test.statut != 'en_cours':
        return JsonResponse({'error': 'Test terminé'}, status=400)
    
    questions_ordre = test.questions_ordre
    if question_index >= len(questions_ordre):
        return JsonResponse({'error': 'Index invalide'}, status=400)
    
    question       = get_object_or_404(Question, id=questions_ordre[question_index])
    reponse_donnee = body.get('reponse', '').strip()
    temps_reponse  = body.get('temps_reponse_sec')
    
    reponse, _ = Reponse.objects.update_or_create(
        test=test,
        question=question,
        defaults={
            'reponse_donnee':    reponse_donnee,
            'temps_reponse_sec': temps_reponse
        }
    )
    
    return JsonResponse({
        'est_correcte':  reponse.est_correcte,
        'points_obtenus': reponse.points_obtenus,
        'est_derniere':  question_index + 1 >= len(questions_ordre)
    })


@csrf_exempt
def terminer_test(request, test_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        body = json.loads(request.body)
    except:
        body = {}

    learner_id = body.get('learner_id')
    if not learner_id:
        return JsonResponse({'error': 'learner_id manquant'}, status=400)
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)

    test = get_object_or_404(Test, id=test_id, learner=learner)
    if test.statut != 'en_cours':
        return JsonResponse({'error': 'Test déjà terminé'}, status=400)

    scores_par_niveau = {}
    for niveau_id in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        reponses  = test.reponses.filter(question__niveau_id=niveau_id)
        total     = reponses.count()
        correctes = reponses.filter(est_correcte=True).count()
        scores_par_niveau[niveau_id] = round((correctes / total) * 100, 2) if total else 0

    niveau_final = None
    for niveau in Niveau.objects.order_by('ordre'):
        if scores_par_niveau.get(niveau.id, 0) >= float(niveau.seuil_reussite) * 100:
            niveau_final = niveau
        else:
            break

    test.scores_par_niveau = scores_par_niveau
    test.niveau_final      = niveau_final
    test.score_final       = round(sum(scores_par_niveau.values()) / 6, 2)
    test.date_fin          = timezone.now()
    test.statut            = 'termine'
    test.save()

    if niveau_final:
        learner.cefr_level = niveau_final.id
        learner.save()

    total_correctes = sum(
        test.reponses.filter(question__niveau_id=n).filter(est_correcte=True).count()
        for n in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    )

    return JsonResponse({
        'success':            True,
        'niveau_final':       niveau_final.id if niveau_final else 'A1',
        'nom_niveau':         niveau_final.nom if niveau_final else 'Beginner',
        'score_global':       float(test.score_final),
        'scores_par_niveau':  scores_par_niveau,
        'reponses_correctes': total_correctes,
        'total_reponses':     test.reponses.count(),
    })


@csrf_exempt
def get_progression(request, test_id):
    learner_id = request.GET.get('learner_id')
    if not learner_id:
        return JsonResponse({'error': 'learner_id manquant'}, status=400)
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)

    test      = get_object_or_404(Test, id=test_id, learner=learner)
    total     = len(test.questions_ordre) if test.questions_ordre else 0
    repondues = test.reponses.count()

    return JsonResponse({
        'total_questions':       total,
        'repondues':             repondues,
        'progression_pourcent':  round((repondues / total) * 100, 1) if total else 0
    })


@csrf_exempt
def abandonner_test(request, test_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        body = json.loads(request.body) if request.body else {}
    except:
        body = {}

    learner_id = body.get('learner_id')
    if not learner_id or str(learner_id).lower() in ['null', 'undefined', 'none', '']:
        return JsonResponse({'error': 'learner_id manquant ou invalide'}, status=400)
    
    try:
        learner_id = int(learner_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'learner_id doit être un nombre entier'}, status=400)
    
    try:
        learner = Learner.objects.get(learner_id=learner_id)
    except Learner.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)

    try:
        test = Test.objects.get(id=test_id, learner=learner)
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Test introuvable'}, status=404)

    if test.statut != 'en_cours':
        return JsonResponse({'error': 'Test non modifiable (déjà terminé ou abandonné)'}, status=400)

    niveau_id = learner.cefr_level or 'A1'
    try:
        niveau_actuel = Niveau.objects.get(id=niveau_id)
    except Niveau.DoesNotExist:
        niveau_actuel, _ = Niveau.objects.get_or_create(
            id='A1',
            defaults={'nom': 'Beginner', 'ordre': 1, 'seuil_reussite': 0.60}
        )
    
    test.statut      = 'abandonne'
    test.niveau_final = niveau_actuel
    test.date_fin    = timezone.now()
    test.save()

    return JsonResponse({
        'success':      True,
        'message':      'Test abandonné',
        'niveau_final': niveau_actuel.id,
        'nom_niveau':   niveau_actuel.nom
    })


# ============================================================
# GOOGLE AUTHENTICATION 
# Accepte 2 formats :
#   Format 1 : { "credential": "<JWT Google>" }   ← ancien flow accounts.id
#   Format 2 : { "sub": "...", "email": "...", "name": "..." } ← nouveau flow oauth2 + userinfo
#
# Retourne is_new_user pour choisir la redirection :
#   is_new_user = True  → preferences  (nouveau compte)
#   is_new_user = False → home          (compte existant)
# ============================================================

from dotenv import load_dotenv
import os
import requests

load_dotenv()  # Charge le .env

GOOGLE_CLIENT_ID     = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')  
GOOGLE_REDIRECT_URI  = 'http://localhost:8000/api/auth/google/callback/'



@csrf_exempt
def google_auth_callback(request):
    """
    GET /api/auth/google/callback/?code=...
    
    Reçoit le code d'autorisation de Google,
    l'échange contre un access_token,
    récupère le profil utilisateur,
    crée ou trouve le learner,
    redirige vers /?learner_id=...
    """
    code  = request.GET.get('code')
    error = request.GET.get('error')
 
    if error or not code:
        print(f"❌ Google callback erreur : {error}")
        return redirect(f'/login/?error={error or "no_code"}')
 
    try:
        # ── Étape 1 : Échanger le code contre un access_token ────────
        token_res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code':          code,
                'client_id':     GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri':  GOOGLE_REDIRECT_URI,
                'grant_type':    'authorization_code',
            },
            timeout=10
        )
        token_data = token_res.json()
        print(f"🔑 Token response: {token_data}")
 
        if 'error' in token_data:
            print(f"❌ Erreur token : {token_data['error']}")
            return redirect(f'/login/?error={token_data["error"]}')
 
        access_token = token_data.get('access_token')
 
        # ── Étape 2 : Récupérer le profil Google ─────────────────────
        userinfo_res = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        userinfo = userinfo_res.json()
        print(f"👤 Profil Google : {userinfo}")
 
        email     = userinfo.get('email')
        name      = userinfo.get('name', email.split('@')[0] if email else 'User')
        google_id = userinfo.get('sub')
        picture   = userinfo.get('picture', '')
 
        if not email or not google_id:
            return redirect('/login/?error=missing_info')
 
        # ── Étape 3 : Trouver ou créer le learner ────────────────────
        import random, string
        from django.contrib.auth.hashers import make_password
 
        is_new_user = False
        learner     = None
 
        # 1. Chercher par google_id
        try:
            learner = Learner.objects.get(google_id=google_id)
            print(f"✅ Compte trouvé par google_id : {email}")
        except Learner.DoesNotExist:
            pass
 
        # 2. Chercher par email (compte classique → on lie le google_id)
        if not learner:
            try:
                learner = Learner.objects.get(email=email)
                if not learner.google_id:
                    learner.google_id = google_id
                learner.picture = picture
                learner.save()
                print(f"✅ Compte existant lié à Google : {email}")
            except Learner.DoesNotExist:
                pass
 
        # 3. Créer un nouveau compte
        if not learner:
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            learner = Learner.objects.create(
                name=name,
                email=email,
                password=make_password(random_password),
                google_id=google_id,
                picture=picture,
                cefr_level='A1',
                progress=0
            )
            is_new_user = True
            print(f"🆕 Nouveau compte Google créé : {email}")
 
        # ── Étape 4 : Rediriger la popup vers la bonne page ──────────
        if is_new_user:
            import urllib.parse
            name_enc  = urllib.parse.quote(learner.name)
            email_enc = urllib.parse.quote(learner.email)
            # Nouveau utilisateur → preferences
            return redirect(
                f'/preferences/?learner_id={learner.learner_id}&name={name_enc}&email={email_enc}&is_new=1'
            )
        else:
            # Utilisateur existant → home avec learner_id
            return redirect(f'/?learner_id={learner.learner_id}')
 
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau Google : {e}")
        return redirect('/login/?error=network_error')
 
    except Exception as e:
        import traceback
        print(f"❌ Erreur google_auth_callback :\n{traceback.format_exc()}")
        return redirect(f'/login/?error=server_error')
 
 
# ============================================================
# MODIFIE aussi google_auth_api pour accepter le format direct
# (au cas où tu veux garder l'ancienne route aussi)
# ============================================================
 
@csrf_exempt
def google_auth_api(request):
    """
    POST /api/auth/google/
    Accepte : { "sub": "...", "email": "...", "name": "...", "picture": "..." }
           OU : { "credential": "<JWT>" }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': ['Méthode non autorisée']}, status=405)
 
    try:
        data       = json.loads(request.body)
        credential = data.get('credential')
 
        if credential:
            import jwt
            try:
                user_info = jwt.decode(credential, options={"verify_signature": False})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': ['Token invalide']}, status=401)
            email     = user_info.get('email')
            name      = user_info.get('name', email.split('@')[0] if email else 'User')
            google_id = user_info.get('sub')
            picture   = user_info.get('picture', '')
        else:
            email     = data.get('email')
            name      = data.get('name', email.split('@')[0] if email else 'User')
            google_id = data.get('sub')
            picture   = data.get('picture', '')
 
        if not email or not google_id:
            return JsonResponse({'success': False, 'errors': ['email ou sub manquant']}, status=400)
 
        import random, string
        from django.contrib.auth.hashers import make_password
 
        is_new_user = False
        learner     = None
 
        try:
            learner = Learner.objects.get(google_id=google_id)
        except Learner.DoesNotExist:
            pass
 
        if not learner:
            try:
                learner = Learner.objects.get(email=email)
                if not learner.google_id:
                    learner.google_id = google_id
                learner.picture = picture
                learner.save()
            except Learner.DoesNotExist:
                pass
 
        if not learner:
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            learner = Learner.objects.create(
                name=name,
                email=email,
                password=make_password(random_password),
                google_id=google_id,
                picture=picture,
                cefr_level='A1',
                progress=0
            )
            is_new_user = True
 
        return JsonResponse({
            'success':     True,
            'message':     'Connexion Google réussie',
            'is_new_user': is_new_user,
            'learner': {
                'learner_id': str(learner.learner_id),
                'name':       learner.name,
                'email':      learner.email,
                'cefr_level': learner.cefr_level,
                'progress':   learner.progress
            }
        })
 
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': ['Body JSON invalide']}, status=400)
    except Exception as e:
        import traceback
        print(f"❌ Erreur google_auth_api :\n{traceback.format_exc()}")
        return JsonResponse({'success': False, 'errors': [str(e)]}, status=500)
    



#---------generated text------------------


MAX_GENERATED_PER_TEXT = 3

@csrf_exempt
def generate_reading_ex_api(request):
    """
    POST /api/generate-reading-ex/
    
    Génère un text non identique aux texts déja générés .
    Limite: MAX_GENERATED_PER_TEXT (3) textes non identiques maximum par texte original.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
 
    try:
        data            = json.loads(request.body)
        exercise_id     = data.get('exercise_id')
        learner_id      = data.get('learner_id')
 
        if not exercise_id:
            return JsonResponse({
                'success': False,
                'error'  : 'exercise_id manquant'
            }, status=400)
 
        # ── 1. Charger le ReadingText original ────────────────────
        try:
            original_text = ReadingText.objects.get(id=exercise_id)
        except ReadingText.DoesNotExist:
            try:
                generated = GeneratedReadingText.objects.get(id=exercise_id)
                original_text = generated.original_text
                print(f"⚠️  ID {exercise_id} était un GeneratedReadingText, utilisation de l'original {original_text.id}")
            except GeneratedReadingText.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Texte original non trouvé'
                }, status=404)
 
        # ── 2. Récupérer le learner ────────────────────────────────
        learner = None
        learner_level = original_text.sub_unit.unit.level
        if learner_id:
            try:
                learner       = Learner.objects.get(learner_id=learner_id)
                learner_level = learner.cefr_level
            except Learner.DoesNotExist:
                pass
 
        # ── 3. Récupérer les textes générés existants POUR CE LEARNER ─
        # ✅ Chaque apprenant a sa propre limite de 3 textes
        existing_filter = {'original_text': original_text}
        if learner:
            existing_filter['learner'] = learner
        else:
            existing_filter['learner__isnull'] = True
 
        existing_generated = list(GeneratedReadingText.objects.filter(
            **existing_filter
        ).order_by('created_at', 'id'))
 
        total_existing = len(existing_generated)
 
        # ✅ VÉRIFICATION STRICTE DE LA LIMITE - Bloquer si déjà 3 ou plus
        if total_existing >= MAX_GENERATED_PER_TEXT:
            return JsonResponse({
                'success': False,
                'error': f'Maximum {MAX_GENERATED_PER_TEXT} generated exercises reached for this text.',
                'limit_reached': True,
                'max_allowed': MAX_GENERATED_PER_TEXT,
                'existing_count': total_existing
            }, status=403)
 
        # ── 4. Déterminer le prochain index ───────────────────────
        # Le frontend envoie l'index qu'il veut obtenir (0, 1, ou 2)
        requested_index = data.get('generated_index', 0)
        
        # ✅ Vérifier que l'index demandé est valide
        if requested_index < 0 or requested_index >= MAX_GENERATED_PER_TEXT:
            return JsonResponse({
                'success': False,
                'error': f'Invalid index. Must be between 0 and {MAX_GENERATED_PER_TEXT - 1}',
                'limit_reached': True,
                'max_allowed': MAX_GENERATED_PER_TEXT,
                'existing_count': total_existing
            }, status=400)
 
        # ── 5. Réutiliser ou générer ──────────────────────────────
        if requested_index < total_existing:
            # ♻️ Réutiliser le texte déjà généré à cet index
            new_text = existing_generated[requested_index]
            next_index = requested_index
            is_reused = True
            print(f"♻️  Réutilisation GeneratedReadingText id={new_text.id} (index {next_index})")
        else:
            # 🤖 Générer un nouveau texte
            # Vérification supplémentaire: ne pas dépasser la limite totale
            if total_existing >= MAX_GENERATED_PER_TEXT:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot generate more than {MAX_GENERATED_PER_TEXT} exercises per text.',
                    'limit_reached': True,
                    'max_allowed': MAX_GENERATED_PER_TEXT,
                    'existing_count': total_existing
                }, status=403)
 
            print(f"🤖  Génération nouveau texte ({total_existing + 1}/{MAX_GENERATED_PER_TEXT})")
            new_generated_id = generate_and_save_reading_ex(
                original_text=original_text,
                learner_level=learner_level,
            )
            new_text = GeneratedReadingText.objects.get(id=new_generated_id)
            # ✅ Lier le texte généré au learner qui l'a demandé
            if learner:
                new_text.learner = learner
                new_text.save(update_fields=['learner'])
            next_index = total_existing  # L'index du nouveau texte
            is_reused = False
 
        # ── 6. Charger les questions ─────────────────────────────
        questions      = new_text.questions.all().order_by('id')
        questions_data = [
            {
                'id'      : q.id,
                'number'  : idx,
                'question': q.question,
                'type'    : q.type,
                'choices' : q.choices or [],
                'answer'  : q.answer,
            }
            for idx, q in enumerate(questions, 1)
        ]
 
        subunit = new_text.sub_unit
 
        return JsonResponse({
            'success'         : True,
            'generated'       : True,
            'generated_id'    : new_text.id,
            'generated_index' : next_index,
            'is_reused'       : is_reused,
            'limit_info'      : {
                'current': next_index + 1,
                'maximum': MAX_GENERATED_PER_TEXT,
                'remaining': max(0, MAX_GENERATED_PER_TEXT - (next_index + 1))
            },
            'exercise'        : {
                'subunit': {
                    'id'        : subunit.id,
                    'title'     : subunit.title,
                    'unit_title': subunit.unit.title,
                },
                'text': {
                    'id'     : new_text.id,
                    'topic'  : new_text.topic,
                    'content': new_text.content,
                },
                'questions'      : questions_data,
                'total_questions': len(questions_data),
            }
        })
 
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        print(f"❌  generate_reading_ex_api error: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@csrf_exempt
def get_generated_texts_api(request):
    """
    GET /api/generated-texts/?original_id=X&learner_id=Y
    
    Retourne les textes générés PAR CE LEARNER pour ce texte original.
    Chaque apprenant a sa propre liste de textes générés.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    original_id = request.GET.get('original_id')
    learner_id  = request.GET.get('learner_id')
 
    if not original_id:
        return JsonResponse({'success': False, 'error': 'original_id manquant'}, status=400)
    
    try:
        original_text = ReadingText.objects.get(id=original_id)
 
        # ✅ Filtrer par learner : chaque apprenant voit uniquement ses textes
        qs = GeneratedReadingText.objects.filter(original_text=original_text)
        if learner_id:
            try:
                learner = Learner.objects.get(learner_id=learner_id)
                qs = qs.filter(learner=learner)
            except Learner.DoesNotExist:
                # Learner inconnu → on ne retourne rien (0 textes, peut générer)
                qs = qs.none()
        else:
            # Visiteur anonyme → ne voir que les textes sans learner
            qs = qs.filter(learner__isnull=True)
 
        generated_texts = qs.order_by('created_at', 'id')
        
        texts_data = []
        for idx, gen_text in enumerate(generated_texts):
            questions = gen_text.questions.all().order_by('id')
            questions_data = [{
                'id': q.id,
                'question': q.question,
                'type': q.type,
                'choices': q.choices or [],
                'answer': q.answer,
            } for q in questions]
            
            texts_data.append({
                'id': gen_text.id,
                'index': idx,
                'topic': gen_text.topic,
                'content': gen_text.content,
                'created_at': gen_text.created_at.isoformat(),
                'questions': questions_data,
            })
        
        limit_info = {
            'current': len(texts_data),
            'maximum': MAX_GENERATED_PER_TEXT,
            'remaining': max(0, MAX_GENERATED_PER_TEXT - len(texts_data)),
            'can_generate': len(texts_data) < MAX_GENERATED_PER_TEXT
        }
        
        return JsonResponse({
            'success': True,
            'original_id': original_id,
            'generated_texts': texts_data,
            'limit_info': limit_info
        })
        
    except ReadingText.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Texte original non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
       
@csrf_exempt
def submit_generated_exercise_api(request):
    """
    POST /api/submit-generated-exercise/
    
    Soumission des réponses pour un texte généré avec VÉRIFICATION ANTI-DOUBLE SOUMISSION.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        generated_text_id = data.get('generated_text_id')
        answers = data.get('answers', {})
        learner_id = data.get('learner_id')
        
        if not generated_text_id:
            return JsonResponse({
                'success': False, 
                'error': 'generated_text_id is required'
            }, status=400)

        try:
            generated_text = GeneratedReadingText.objects.select_related(
                'original_text', 'sub_unit', 'sub_unit__unit'
            ).get(id=generated_text_id)
        except GeneratedReadingText.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Generated text not found'
            }, status=404)
        
        learner = None
        if learner_id:
            try:
                learner = Learner.objects.get(learner_id=learner_id)
            except Learner.DoesNotExist:
                pass

        # Vérifier si déjà complété
        existing_result = None
        if learner:
            existing_result = GeneratedExerciseResult.objects.filter(
                learner=learner,
                generated_text=generated_text
            ).select_related('generated_text').first()
        
        if existing_result:
            # IMPORTANT: Retourner les detailed_results_json stockés
            return JsonResponse({
                'success': True,
                'already_completed': True,
                'completed_at': existing_result.submitted_at.strftime('%Y-%m-%d %H:%M'),
                'score_on_10': float(existing_result.score_on_10),
                'score_percentage': existing_result.score_percentage,
                'correct_count': existing_result.correct_count,
                'total_questions': existing_result.total_questions,
                'feedback': existing_result.feedback,
                'detailed_results': existing_result.detailed_results_json,  # ← ICI
                'message': 'Exercise already completed',
                'can_retry': False
            }, status=200)

        # Première soumission - corriger et sauvegarder
        questions = GeneratedReadingQuestion.objects.filter(generated_text=generated_text)
        
        detailed_results = []  # ← LISTE À SAUVEGARDER
        correct_count = 0
        total_questions = questions.count()
        
        for question in questions:
            qid = str(question.id)
            user_answer = answers.get(qid, '').strip()
            
            # Logique de correction selon le type
            is_correct = False
            
            if question.type == 'true_false':
                user_normalized = user_answer.lower()
                correct_normalized = question.answer.lower()
                is_correct = user_normalized == correct_normalized
                correct_answer_display = question.answer
                user_answer_display = user_answer
                
            elif question.type == 'multiple_choice':
                correct_ans = question.answer
                if question.choices and correct_ans in question.choices:
                    correct_index = question.choices.index(correct_ans)
                    letter = chr(65 + correct_index)
                    correct_answer_display = f"{letter}. {correct_ans}"
                    
                    if user_answer and user_answer[0].upper() in 'ABCD':
                        letter_given = user_answer[0].upper()
                        idx = ord(letter_given) - 65
                        if idx < len(question.choices):
                            actual_answer = question.choices[idx]
                            user_answer_display = f"{letter_given}. {actual_answer}"
                            is_correct = actual_answer.lower() == correct_ans.lower()
                        else:
                            is_correct = False
                            user_answer_display = user_answer
                    else:
                        is_correct = user_answer.lower() == correct_ans.lower()
                        user_answer_display = user_answer
                else:
                    is_correct = user_answer.lower() == question.answer.lower()
                    correct_answer_display = question.answer
                    user_answer_display = user_answer
                    
            else:  # fill_blank
                user_normalized = user_answer.lower()
                correct_answers = [a.strip().lower() for a in question.answer.split('|')]
                is_correct = user_normalized in correct_answers
                correct_answer_display = question.answer
                user_answer_display = user_answer
            
            if is_correct:
                correct_count += 1
            
            # AJOUTER À LA LISTE avec le type de question
            detailed_results.append({
                'question_id': qid,
                'correct': is_correct,
                'user_answer': user_answer_display,
                'correct_answer': correct_answer_display,
                'question_type': question.type  # ← IMPORTANT pour l'ordre
            })

        # Calcul des scores
        score_percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
        score_on_10 = round((correct_count / total_questions) * 10, 1) if total_questions > 0 else 0

        # Feedback
        feedback = generate_feedback_message(score_on_10)

        # SAUVEGARDE EN BASE avec detailed_results_json
        saved_result_id = None
        evaluation_status = 'not_saved_no_learner'
        
        if learner:
            try:
                result = GeneratedExerciseResult.objects.create(
                    learner=learner,
                    original_text=generated_text.original_text,
                    generated_text=generated_text,
                    answers_json=answers,
                    correct_count=correct_count,
                    total_questions=total_questions,
                    score_percentage=score_percentage,
                    score_on_10=score_on_10,
                    feedback=feedback,
                    detailed_results_json=detailed_results  # ← SAUVEGARDE ICI
                )
                saved_result_id = result.id
                evaluation_status = 'saved'
            except Exception as e:
                evaluation_status = 'save_error'
                print(f"Error saving result: {e}")

        return JsonResponse({
            'success': True,
            'already_completed': False,
            'results': detailed_results,  # ← Retourner pour affichage immédiat
            'correct_count': correct_count,
            'total': total_questions,
            'score_percentage': score_percentage,
            'score_on_10': score_on_10,
            'feedback': feedback,
            'saved_result_id': saved_result_id,
            'evaluation_status': evaluation_status
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
        
    except Exception as e:
        print(f"❌ Error in submit_generated_exercise_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def generate_feedback_message(score_on_10):
    """
    Génère un message de feedback en anglais selon la note sur 10.
    """
    if score_on_10 >= 9:
        return "Excellent work! You have mastered this topic very well. Keep practicing to maintain this level!"
    elif score_on_10 >= 8:
        return "Very good work! You understand this well. A bit more practice will help you reach excellence!"
    elif score_on_10 >= 7:
        return "Good job! You have a solid understanding. Keep practicing to improve your accuracy!"
    elif score_on_10 >= 6:
        return "Fair result. You understand the basics, but more practice will help you improve!"
    elif score_on_10 >= 5:
        return "You are making progress, but need more practice with this type of text. Try again!"
    elif score_on_10 >= 4:
        return "Keep practicing! Reading more texts like this will help you improve your comprehension."
    else:
        return "Don't give up! The more you practice reading, the better you will become. Try another exercise!"
@csrf_exempt
def check_generated_status_api(request):
    """
    GET /api/check-generated-status/?generated_id=X&learner_id=Y
    
    Vérifie si un exercice généré a déjà été complété par le learner.
    Utile pour désactiver le bouton Submit côté client au chargement de la page.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    generated_id = request.GET.get('generated_id')
    learner_id = request.GET.get('learner_id')
    
    if not generated_id or not learner_id:
        return JsonResponse({
            'success': False,
            'error': 'generated_id and learner_id required'
        }, status=400)
    
    try:
        # Vérifier que le learner existe
        try:
            learner = Learner.objects.get(learner_id=learner_id)
        except Learner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Learner not found'
            }, status=404)
        
        # Vérifier si un résultat existe
        existing = GeneratedExerciseResult.objects.filter(
            generated_text_id=generated_id,
            learner=learner
        ).first()
        
        if existing:
            return JsonResponse({
                'success': True,
                'already_completed': True,
                'completed_at': existing.submitted_at.strftime('%Y-%m-%d %H:%M'),
                'score_on_10': float(existing.score_on_10),
                'score_percentage': existing.score_percentage,
                'correct_count': existing.correct_count,
                'total_questions': existing.total_questions
            })
        else:
            return JsonResponse({
                'success': True,
                'already_completed': False
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)  
@csrf_exempt
def get_gen_results_api(request):
    """
    GET /api/gen-results/?learner_id=X&original_id=Y
    
    Retourne les résultats d'un learner pour un texte original.
    Si learner_id seul : tous ses résultats groupés par original.
    Si original_id seul : tous les learners pour ce original.
    Si les deux : résultats spécifiques du learner pour ce original.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    learner_id = request.GET.get('learner_id')
    original_id = request.GET.get('original_id')
    
    try:
        queryset = GeneratedExerciseResult.objects.select_related(
            'learner', 'original_text', 'generated_text'
        )
        
        # Filtrer si learner_id fourni
        if learner_id:
            learner = Learner.objects.get(learner_id=learner_id)
            queryset = queryset.filter(learner=learner)
        
        # Filtrer si original_id fourni
        if original_id:
            original = ReadingText.objects.get(id=original_id)
            queryset = queryset.filter(original_text=original)
        
        # Construire la réponse
        results = []
        for r in queryset.order_by('-submitted_at'):
            results.append({
                'result_id': r.id,
                'learner': {
                    'id': r.learner.learner_id,
                    'name': r.learner.name,
                },
                'original_text': {
                    'id': r.original_text.id,
                    'topic': r.original_text.topic,
                },
                'generated_text': {
                    'id': r.generated_text.id,
                    'topic': r.generated_text.topic,
                },
                'score_on_10': float(r.score_on_10),
                'score_percentage': r.score_percentage,
                'correct_count': f"{r.correct_count}/{r.total_questions}",
                'feedback': r.feedback,
                'submitted_at': r.submitted_at.isoformat(),
                'detailed_results': r.detailed_results_json,
            })
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Learner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Apprenant non trouvé'}, status=404)
    except ReadingText.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Texte original non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

@csrf_exempt
def check_reading_result_api(request):
    """
    GET /api/check-reading-result/?text_id=X&learner_id=Y
    
    Vérifie si un learner a déjà complété un texte de lecture et retourne son score.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    text_id = request.GET.get('text_id')
    learner_id = request.GET.get('learner_id')
    
    if not text_id or not learner_id:
        return JsonResponse({
            'success': False,
            'error': 'text_id and learner_id required'
        }, status=400)
    
    try:
        learner = Learner.objects.get(learner_id=learner_id)
        reading_text = ReadingText.objects.get(id=text_id)
        
        result = ReadingExerciseResult.objects.filter(
            learner=learner,
            reading_text=reading_text
        ).first()
        
        if result:
            return JsonResponse({
                'success': True,
                'has_result': True,
                'score': result.score,  # Score en pourcentage
                'correct_count': result.correct_count,
                'total': result.total,
                'submitted_at': result.submitted_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': True,
                'has_result': False
            })
            
    except Learner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Learner not found'}, status=404)
    except ReadingText.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Text not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

# ============================================================
# LISTENING — À AJOUTER dans views.py
# ============================================================
@csrf_exempt
def get_listening_exercise_api(request):
    """
    GET /api/listening-exercise/?subunit_id=X
    Retourne l'audio + les 10 questions pour une sous-unité.
    Les réponses correctes ne sont PAS envoyées au frontend.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
 
    subunit_id = request.GET.get('subunit_id')
    if not subunit_id:
        return JsonResponse({'success': False, 'error': 'subunit_id manquant'}, status=400)
 
    try:
        subunit = get_object_or_404(SubUnit, id=subunit_id)
 
        # Récupérer l'audio lié à ce subunit
        audio = ListeningAudio.objects.filter(sub_unit=subunit).first()
        if not audio:
            return JsonResponse({'success': False, 'error': 'Aucun audio trouvé pour cette sous-unité'}, status=404)
 
        # Récupérer les 10 questions (sans les réponses)
        questions = ListeningQuestion.objects.filter(audio=audio).order_by('question_order')
        questions_data = []
        for q in questions:
            questions_data.append({
                'id':            q.id,
                'order':         q.question_order,
                'type':          q.question_type,
                'question':      q.question_text,
                'choices':       q.choices,
                'target_word':   q.target_word,
                'correct_order': q.correct_order,
                
            })
 
        return JsonResponse({
            'success': True,
            'audio': {
                'audio_id':      audio.audio_id,
                'audio_url':     f'/api/listening-audio/{audio.audio_id}/stream/',
                'transcript':    audio.transcript,
                'cefr_level':    audio.cefr_level,
                'unit_title':    audio.unit_title,
                'subunit_title': audio.subunit_title,
                'duration':      audio.duration_seconds,
                'vocab_score':   float(audio.vocab_score) if audio.vocab_score else None,
            },
            'questions': questions_data
        })
 
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
 
@csrf_exempt 
def serve_listening_audio(request, audio_id):
    """
    GET /api/listening-audio/<audio_id>/stream/
    Stream le fichier .wav vers le frontend.
    """
    import mimetypes
    from django.conf import settings
 
    try:
        audio = get_object_or_404(ListeningAudio, audio_id=audio_id)
 
        # Normaliser le chemin (Windows backslashes → forward slashes)
        audio_path = audio.audio_path.replace('\\', '/')
 
        # Essayer le chemin absolu d'abord, puis relatif à MEDIA_ROOT
        if os.path.isabs(audio_path) and os.path.exists(audio_path):
            file_path = audio_path
        else:
            file_path = os.path.join(settings.MEDIA_ROOT, audio_path)
 
        if not os.path.exists(file_path):
            return JsonResponse(
                {'success': False, 'error': f'Fichier audio introuvable : {audio_path}'},
                status=404
            )
 
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or 'audio/wav'
 
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )
        response['Accept-Ranges']  = 'bytes'
        response['Content-Length'] = os.path.getsize(file_path)
        return response
 
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
 
 
@csrf_exempt
def submit_listening_exercise_api(request):
    """
    POST /api/submit-listening/
    Reçoit les réponses du learner, corrige, calcule le score, sauvegarde.
 
    Body JSON :
    {
        "audio_id":   "LJ020-0093",
        "learner_id": 42,
        "answers": {
            "1": "True",          ← question_id : réponse donnée
            "2": "B",
            "3": "A",
            ...
        }
    }
 
    Correction par type :
      - true_false  : comparaison insensible à la casse
      - mcq         : lettre donnée (A/B/C/D) vs lettre de la réponse
      - fill_blank  : comparaison insensible à la casse
      - word_order  : comparaison de la phrase reconstituée
      - synonym     : comparaison insensible à la casse
      - grammar     : lettre donnée vs lettre de la réponse
      - vocabulary  : lettre donnée vs lettre de la réponse
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
 
    try:
        data       = json.loads(request.body)
        audio_id   = data.get('audio_id')
        learner_id = data.get('learner_id')
        answers    = data.get('answers', {})
 
        if not audio_id:
            return JsonResponse({'success': False, 'error': 'audio_id manquant'}, status=400)
 
        audio = get_object_or_404(ListeningAudio, audio_id=audio_id)
 
        # Récupérer le learner (optionnel)
        learner = None
        if learner_id:
            try:
                learner = Learner.objects.get(learner_id=learner_id)
            except Learner.DoesNotExist:
                pass
 
        # ── Si déjà soumis → retourner le résultat initial ─────
        if learner:
            existing = ListeningExerciseResult.objects.filter(
                learner=learner,
                audio=audio
            ).first()
            if existing:
                return JsonResponse({
                    'success':       True,
                    'already_done':  True,
                    'score':         existing.score,
                    'correct_count': existing.correct_count,
                    'total':         existing.total,
                    'results':       existing.results_json,
                    'feedback':      existing.feedback,
                })
 
        # ── Correction des réponses ─────────────────────────────
        questions     = ListeningQuestion.objects.filter(audio=audio).order_by('question_order')
        correct_count = 0
        total         = 0
        results       = []
 
        for q in questions:
            question_id  = str(q.id)
            user_answer  = str(answers.get(question_id, '')).strip()
            correct_ans  = q.correct_answer.strip()
            total       += 1
 
            # ── Logique de correction selon le type ────────────
            q_type = q.question_type
 
            if q_type == 'true_false':
                is_correct = user_answer.lower() == correct_ans.lower()
 
            elif q_type in ('mcq', 'grammar', 'vocabulary'):
                # Comparer la lettre (A/B/C/D) uniquement
                user_letter    = user_answer[0].upper() if user_answer else ''
                correct_letter = correct_ans[0].upper() if correct_ans else ''
                is_correct     = user_letter == correct_letter
 
            elif q_type == 'fill_blank':
                is_correct = user_answer.lower() == correct_ans.lower()
 
            elif q_type == 'word_order':
                # Comparer les phrases normalisées (sans ponctuation, minuscules)
                import re
                normalize     = lambda s: re.sub(r'[^\w\s]', '', s.lower()).strip()
                is_correct    = normalize(user_answer) == normalize(correct_ans)
 
            elif q_type == 'synonym':
                is_correct = user_answer.lower() == correct_ans.lower()
 
            else:
                is_correct = user_answer.lower() == correct_ans.lower()
 
            if is_correct:
                correct_count += 1
 
            results.append({
                'question_id':    q.id,
                'question':       q.question_text,
                'type':           q_type,
                'user_answer':    user_answer,
                'correct_answer': correct_ans,
                'is_correct':     is_correct,
            })
 
        # ── Calcul du score ─────────────────────────────────────
        score = round((correct_count / total) * 100) if total > 0 else 0
 
        # ── Sauvegarde du résultat ──────────────────────────────
        result = None
        if learner:
            result = ListeningExerciseResult.objects.create(
                learner       = learner,
                audio         = audio,
                score         = score,
                correct_count = correct_count,
                total         = total,
                results_json  = results,
                # feedback auto-généré dans save()
            )
 
        return JsonResponse({
            'success':       True,
            'already_done':  False,
            'score':         score,
            'correct_count': correct_count,
            'total':         total,
            'results':       results,
            'feedback':      result.feedback if result else '',
        })
 
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
 
@csrf_exempt
def check_listening_result_api(request):
    """
    GET /api/check-listening-result/?audio_id=LJ020-0093&learner_id=42
    Vérifie si un learner a déjà complété un exercice listening.
    Utilisé par exercise-menu.js pour afficher le badge de score.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
 
    audio_id   = request.GET.get('audio_id')
    learner_id = request.GET.get('learner_id')
    subunit_id = request.GET.get('subunit_id')  # alternative à audio_id
 
    if not learner_id:
        return JsonResponse({'success': False, 'error': 'learner_id requis'}, status=400)
 
    try:
        learner = Learner.objects.get(learner_id=learner_id)
 
        # Résoudre l'audio via audio_id ou subunit_id
        if audio_id:
            audio = ListeningAudio.objects.filter(audio_id=audio_id).first()
        elif subunit_id:
            audio = ListeningAudio.objects.filter(sub_unit_id=subunit_id).first()
        else:
            return JsonResponse({'success': False, 'error': 'audio_id ou subunit_id requis'}, status=400)
 
        if not audio:
            return JsonResponse({'success': True, 'has_result': False})
 
        result = ListeningExerciseResult.objects.filter(
            learner=learner,
            audio=audio
        ).first()
 
        if result:
            return JsonResponse({
                'success':      True,
                'has_result':   True,
                'score':        result.score,
                'correct_count': result.correct_count,
                'total':        result.total,
                'feedback':     result.feedback,
                'results':      result.results_json,  # ✅ AJOUT: résultats détaillés
                'already_done': True,                  # ✅ AJOUT: flag already_done
                'submitted_at': result.submitted_at.isoformat(),
            })
        else:
            return JsonResponse({'success': True, 'has_result': False})
 
    except Learner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Learner not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)