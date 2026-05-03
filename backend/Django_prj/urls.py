from django.contrib import admin
from django.urls import path, re_path
from users import views
from django.views.generic import TemplateView

# AJOUT : pour servir les fichiers media en développement
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Pages HTML servies par Django (:8000) ──────────────────
    # home.html : servi via views.home_view (FileResponse)
    path('', views.home_view, name='home'),
    path('exercise-menu/', TemplateView.as_view(template_name='exercise-menu.html'), name='exercise_menu'),
    path('comprehension-ecrite/', TemplateView.as_view(template_name='comprehension-ecrite.html'), name='reading_exercise'),
    path('generated_reading_ex/', TemplateView.as_view(template_name='generated_reading_ex.html'), name='generated_reading_ex'),
    # ── Page Listening ───────────────────────────────────────────
    path('listening/', TemplateView.as_view(template_name='listening.html'), name='listening'),
    path('generate_listening/',TemplateView.as_view(template_name='generate_listening.html'),name='generate_listening'),

    path('writing/', TemplateView.as_view(template_name='writing/writing.html'), name='writing'),
    
    # login.html : utilise {% load static %} → doit être servi par Django
   
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('index/', TemplateView.as_view(template_name='index.html'), name='index'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('preferences/', TemplateView.as_view(template_name='preferences.html'), name='preferences'),
    path('reset-request/', TemplateView.as_view(template_name='reset-request.html'), name='reset_request'),
    # startlevel.html + test-cefr.html : utilisent {% load static %}
    path('start-test/', TemplateView.as_view(template_name='startlevel.html'), name='start_test'),
    path('test-cefr/', TemplateView.as_view(template_name='test-cefr.html'), name='test_cefr'),


    path('configuration/', TemplateView.as_view(template_name='configuration.html'), name='configuration'),
    path('assessment/', TemplateView.as_view(template_name='assessment.html'), name='assessment'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('update-preferences/', TemplateView.as_view(template_name='update_preferences.html'), name='update_preferences'),
    # ── Pages Grammar ───────────────────────────────────────────
    path('grammar/', TemplateView.as_view(template_name='courses-menu.html'), name='courses_menu'),

    # ── APIs auth ──────────────────────────────────────────────
    path('api/login/', views.login_api, name='login_api'),
    path('api/register/', views.register_api, name='register_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/learner/', views.get_learner_api, name='get_learner_api'),
    path('api/auth/google/', views.google_auth_api, name='google_auth_api'),
    path('api/account/update/', views.update_account_api, name='update_account'),
    path('api/account/delete/', views.delete_account_api, name='delete_account'),
    
    # ── APIs préférences ───────────────────────────────────────
    path('api/preferences/', views.preferences_api, name='preferences_api'),
    path('api/save-preferences/', views.save_preferences_api, name='save_preferences_api'),

    # ── APIs contenu ───────────────────────────────────────────
    path('api/units/', views.get_units_api, name='get_units_api'),
    path('api/reading-exercise/', views.get_reading_exercise_api, name='get_reading_exercise_api'),
    path('api/submit-exercise/', views.submit_exercise_api, name='submit_exercise_api'),
    path('api/generate-reading-ex/', views.generate_reading_ex_api),
    path('api/generated-texts/', views.get_generated_texts_api, name='get_generated_texts'),
    path('api/submit-generated-exercise/', views.submit_generated_exercise_api, name='submit_generated_exercise'),
    path('api/check-generated-status/', views.check_generated_status_api, name='check_generated_status'),
    path('api/gen-results/', views.get_gen_results_api, name='gen_results'),
    path('api/check-reading-result/', views.check_reading_result_api, name='check_reading_result'),

    # ── APIs Listening ─────────────────────────────────────────
   
    path('api/listening-exercise/', views.get_listening_exercise_api, name='listening_exercise'),
    path('api/listening-audio/<str:audio_id>/stream/', views.serve_listening_audio, name='listening_audio_stream'),
    path('api/submit-listening/', views.submit_listening_exercise_api, name='submit_listening'),
    path('api/check-listening-result/', views.check_listening_result_api, name='check_listening_result'),
    # ── APIs Generated Listening (IA) ──────────────────────────────────────
    path('api/generate-listening-exercise/',views.generate_listening_exercise_api,name='generate_listening_exercise'),
    path('api/check-generated-listening-status/',views.check_generated_listening_status_api,name='check_generated_listening_status'),
    path('api/generated-listening-audio/<int:exercise_id>/stream/',views.serve_generated_listening_audio,name='serve_generated_listening_audio'),
    path('api/submit-generated-listening/',views.submit_generated_listening_api,name='submit_generated_listening'),
    path('api/check-generated-listening-result/', views.check_generated_listening_result_api,name='check_generated_listening_result'),
    # ── APIs Writing ───────────────────────────────────────────
    path('api/writing-exercise/', views.get_writing_exercise_api, name='writing_exercise'),
    path('api/submit-writing-exercise/', views.submit_writing_exercise_api, name='submit_writing'),
    path('api/check-writing-result/', views.check_writing_result_api, name='check_writing_result'),

    # ── pages Speaking ───────────────────────────────────────────
    path('speaking/', TemplateView.as_view(template_name='speaking/speaking.html'), name='speaking'),
    path('speaking/generated/', TemplateView.as_view(template_name='speaking/generate_speaking.html'), name='speaking_generated'),
    # ── APIs Speaking ───────────────────────────────────────────
    path('api/speaking-exercise/', views.get_speaking_exercise_api, name='speaking_exercise'),
    path('api/speaking-audio/<int:exercise_id>/stream/', views.serve_speaking_audio, name='speaking_audio_stream'),
    path('api/submit-speaking/', views.submit_speaking_exercise_api, name='submit_speaking'),
    path('api/check-speaking-result/', views.check_speaking_result_api, name='check_speaking_result'),
    # ── APIs Speaking Généré (IA) ──────────────────────────────
    path('api/generate-speaking-exercise/',        views.generate_speaking_exercise_api,        name='generate_speaking_exercise'),
    path('api/submit-generated-speaking/',         views.submit_generated_speaking_api,         name='submit_generated_speaking'),
    path('api/check-generated-speaking-result/',   views.check_generated_speaking_result_api,   name='check_generated_speaking_result'),
    path('api/get-generated-speaking-exercise/',  views.get_generated_speaking_exercise_api, name='get_generated_speaking_exercise'),
    path('api/speaking-audio-generated/<int:gen_exercise_id>/stream/', views.serve_generated_speaking_audio, name='serve_generated_speaking_audio'),
    path('api/check-generated-speaking-exists/', views.check_generated_speaking_exists_api, name='check_generated_speaking_exists'),
    # ── APIs test CEFR ─────────────────────────────────────────
    path('api/test/demarrer/', views.demarrer_test, name='demarrer_test'),
    path('api/test/<uuid:test_id>/question/<int:question_index>/', views.get_question, name='get_question'),
    path('api/test/<uuid:test_id>/question/<int:question_index>/repondre/', views.soumettre_reponse, name='soumettre_reponse'),
    path('api/test/<uuid:test_id>/progression/', views.get_progression, name='get_progression'),
    path('api/test/<uuid:test_id>/terminer/', views.terminer_test, name='terminer_test'),
    path('api/test/<uuid:test_id>/abandonner/', views.abandonner_test, name='abandonner_test'),


    path('api/auth/google/callback/', views.google_auth_callback, name='google_auth_callback'),

    # ── Grammar  pages ────────────────────────────────────────────────
    path('grammar/',          TemplateView.as_view(template_name='courses-menu.html'), name='grammar_courses_menu'),
    path('grammar/course-1/', TemplateView.as_view(template_name='course_1.html'),    name='grammar_course_1'),
    path('grammar/exercise-1/', TemplateView.as_view(template_name='exercise_1.html'), name='grammar_exercise_1'),
    path('grammar/course-2/',   TemplateView.as_view(template_name='course_2.html'),     name='grammar_course_2'),
    path('grammar/exercise-2/', TemplateView.as_view(template_name='exercise_2.html'),   name='grammar_exercise_2'),
    # ── Grammar APIs ────────────────────────────────────────────
    path('api/grammar-course/',        views.get_grammar_course_api,      name='grammar_course_api'),
    path('api/submit-grammar/',        views.submit_grammar_exercise_api, name='submit_grammar'),
    path('api/check-grammar-result/',  views.check_grammar_result_api,    name='check_grammar_result'),


    path('evaluation-test/', TemplateView.as_view(template_name='welcome.html'), name='evaluation_welcome'),
    path('evaluation-test/take/', TemplateView.as_view(template_name='evaluation_test.html'), name='evaluation_test'),
    # ── APIs Test d'Évaluation ─────────────────────────────────
    path('api/evaluation-test/', views.get_evaluation_test_api, name='evaluation_test'),
    path('api/evaluation-start/', views.start_evaluation_api, name='evaluation_start'),
    path('api/evaluation-answer/', views.submit_evaluation_answer_api, name='evaluation_answer'),
    path('api/evaluation-finish/', views.finish_evaluation_api, name='evaluation_finish'),
    # Option plus simple : utiliser re_path
    re_path(r'^api/evaluation-audio/(?P<filename>.+)/?$', views.serve_evaluation_audio, name='evaluation_audio'),
    re_path(r'^api/evaluation-image/(?P<filename>.+)/?$', views.serve_evaluation_image, name='evaluation_image'),
# Cela permet à /media/test_audio/fichier.mp3 de fonctionner
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

