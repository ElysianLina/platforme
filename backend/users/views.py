from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
import json
import os
from .forms import RegisterForm
from .models import Learner , Unit,LearnerPreferences, SubUnit, ReadingText, ReadingQuestion,ReadingExerciseResult
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
                    'level':   reading_text.level
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
                        'results':       existing.results_json
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
            if learner:
                ReadingExerciseResult.objects.create(
                    learner=learner,
                    reading_text=reading_text,
                    score=score,
                    correct_count=correct_count,
                    total=total,
                    results_json=results
                )

            return JsonResponse({
                'success':       True,
                'already_done':  False,
                'score':         score,
                'correct_count': correct_count,
                'total':         total,
                'results':       results
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


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
    

