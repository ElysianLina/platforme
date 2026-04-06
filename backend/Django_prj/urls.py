from django.contrib import admin
from django.urls import path
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
    # login.html : utilise {% load static %} → doit être servi par Django
   
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('index/', TemplateView.as_view(template_name='index.html'), name='index'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('preferences/', TemplateView.as_view(template_name='preferences.html'), name='preferences'),
    path('reset-request/', TemplateView.as_view(template_name='reset-request.html'), name='reset_request'),
    # startlevel.html + test-cefr.html : utilisent {% load static %}
    path('start-test/', TemplateView.as_view(template_name='startlevel.html'), name='start_test'),
    path('test-cefr/', TemplateView.as_view(template_name='test-cefr.html'), name='test_cefr'),

    # ── APIs auth ──────────────────────────────────────────────
    path('api/login/', views.login_api, name='login_api'),
    path('api/register/', views.register_api, name='register_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/learner/', views.get_learner_api, name='get_learner_api'),
    path('api/auth/google/', views.google_auth_api, name='google_auth_api'),
    # ── APIs préférences ───────────────────────────────────────
    path('api/preferences/', views.preferences_api, name='preferences_api'),
    path('api/save-preferences/', views.save_preferences_api, name='save_preferences_api'),

    # ── APIs contenu ───────────────────────────────────────────
    path('api/units/', views.get_units_api, name='get_units_api'),
    path('api/reading-exercise/', views.get_reading_exercise_api, name='get_reading_exercise_api'),
    path('api/submit-exercise/', views.submit_exercise_api, name='submit_exercise_api'),

    # ── APIs test CEFR ─────────────────────────────────────────
    path('api/test/demarrer/', views.demarrer_test, name='demarrer_test'),
    path('api/test/<uuid:test_id>/question/<int:question_index>/', views.get_question, name='get_question'),
    path('api/test/<uuid:test_id>/question/<int:question_index>/repondre/', views.soumettre_reponse, name='soumettre_reponse'),
    path('api/test/<uuid:test_id>/progression/', views.get_progression, name='get_progression'),
    path('api/test/<uuid:test_id>/terminer/', views.terminer_test, name='terminer_test'),
    path('api/test/<uuid:test_id>/abandonner/', views.abandonner_test, name='abandonner_test'),# ✅ AJOUT : Django sert les fichiers media en développement (DEBUG=True)


    path('api/auth/google/callback/', views.google_auth_callback, name='google_auth_callback'),
# Cela permet à /media/test_audio/fichier.mp3 de fonctionner
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)