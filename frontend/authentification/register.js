// ============================================================
// register.js — servi par Django :8000 via {% static %}
// Toutes les requêtes API → http://localhost:8000
// Après inscription → http://localhost:8080/preferences/preferences.html
// ============================================================

const API_BASE = 'http://localhost:8000';
const GOOGLE_CLIENT_ID = '785314051038-7di17e812h2qju4cdd1c7gmv7j20enrs.apps.googleusercontent.com';
const GOOGLE_REDIRECT  = 'http://localhost:8000/api/auth/google/callback/';

document.addEventListener('DOMContentLoaded', function () {

    const registerForm         = document.getElementById('registerForm');
    const fullNameInput        = document.getElementById('fullName');
    const emailInput           = document.getElementById('email');
    const passwordInput        = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const acceptTerms          = document.getElementById('acceptTerms');
    const submitBtn            = document.getElementById('submitBtn');
    const backBtn              = document.getElementById('backBtn');
    const googleBtn            = document.getElementById('googleBtn');
    const loginLink            = document.getElementById('loginLink');

    let isLoading = false;

    // ── Validation ───────────────────────────────────────────
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function validateForm() {
        let valid = true;

        if (fullNameInput.value.trim().length < 2) {
            fullNameInput.classList.add('error'); valid = false;
        } else {
            fullNameInput.classList.remove('error'); fullNameInput.classList.add('success');
        }

        if (!validateEmail(emailInput.value)) {
            emailInput.classList.add('error'); valid = false;
        } else {
            emailInput.classList.remove('error'); emailInput.classList.add('success');
        }

        if (passwordInput.value.length < 6) {
            passwordInput.classList.add('error'); valid = false;
        } else {
            passwordInput.classList.remove('error'); passwordInput.classList.add('success');
        }

        if (confirmPasswordInput.value !== passwordInput.value || confirmPasswordInput.value === '') {
            confirmPasswordInput.classList.add('error'); valid = false;
        } else {
            confirmPasswordInput.classList.remove('error'); confirmPasswordInput.classList.add('success');
        }

        if (!acceptTerms.checked) {
            showToast("Vous devez accepter les conditions d'utilisation", 'error');
            valid = false;
        }

        return valid;
    }

    [fullNameInput, emailInput, passwordInput, confirmPasswordInput].forEach(input => {
        input.addEventListener('input', function () { this.classList.remove('error'); });
    });

    // ── Soumission ───────────────────────────────────────────
    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (isLoading) return;
        if (!validateForm()) return;

        isLoading = true;
        submitBtn.disabled = true;
        const originalContent = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading"></span>';

        try {
            const result = await registerUser({
                fullName: fullNameInput.value,
                email:    emailInput.value,
                password: passwordInput.value
            });

            // ✅ FIX : l'API retourne result.learner_id, result.name, result.email
            //          (pas result.learner.learner_id)
            const learnerId = result.learner_id;
            const name      = encodeURIComponent(result.name);
            const email     = encodeURIComponent(result.email);

            if (learnerId) {
                showToast('Compte créé avec succès !', 'success');
                setTimeout(() => {
                    
                    window.location.href = `${API_BASE}/preferences/?learner_id=${learnerId}&name=${name}&email=${email}`;
                }, 1000);
            } else {
                throw new Error('Erreur de stockage des données');
            }

        } catch (error) {
            showToast(error.message || "Erreur lors de l'inscription", 'error');
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
            isLoading = false;
        }
    });

    // ── Appel API register ───────────────────────────────────
    async function registerUser(data) {
        console.log('Envoi vers:', `${API_BASE}/api/register/`);

        const response = await fetch(`${API_BASE}/api/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name:             data.fullName,
                email:            data.email,
                password:         data.password,
                confirm_password: data.password,
                accept_terms:     true
            })
        });

        const result = await response.json();
        console.log('Réponse:', result);

        if (!response.ok || !result.success) {
            throw new Error(result.errors?.[0] || "Erreur lors de l'inscription");
        }

        // ✅ Stocker dans localStorage
        localStorage.setItem('learner_id',         result.learner_id);
        localStorage.setItem('learner_name',        result.name);
        localStorage.setItem('learner_email',       result.email);
        localStorage.setItem('learner_cefr_level',  result.cefr_level || 'A1');

        console.log('✅ Données stockées:', {
            id:    result.learner_id,
            name:  result.name,
            email: result.email
        });

        return result;
    }

    // ── Boutons ──────────────────────────────────────────────
    backBtn.addEventListener('click', () => window.history.back());

   googleBtn.addEventListener('click', function () {
    this.style.transform = 'scale(0.98)';
    setTimeout(() => {
        this.style.transform = '';
        startGoogleOAuthPopup();
    }, 150);
});

    loginLink.addEventListener('click', function (e) {
        e.preventDefault();
        window.location.href = `${API_BASE}/login/`;
    });

    // ── Toast ────────────────────────────────────────────────
    function showToast(message, type = 'info') {
        document.querySelector('.toast')?.remove();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3000);
    }

    function startGoogleOAuthPopup() {
    const params = new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID,
        redirect_uri: GOOGLE_REDIRECT,
        response_type: 'code',
        scope: 'openid email profile',
        access_type: 'online',
        prompt: 'select_account',
    });

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    const w = 500, h = 620;
    const left = Math.round((window.screen.width - w) / 2);
    const top = Math.round((window.screen.height - h) / 2);
    const opts = `width=${w},height=${h},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes`;

    console.log('🚀 Ouverture popup Google OAuth2 (inscription)...');
    const popup = window.open(authUrl, 'GoogleLogin', opts);

    if (!popup) {
        showToast('❌ Popup bloquée — autorisez les popups pour ce site', 'error');
        return;
    }

    

    const timer = setInterval(() => {
        try {
            const popupUrl = popup.location.href;
            if (popupUrl && popupUrl.startsWith(API_BASE)) {
                clearInterval(timer);
                popup.close();

                const urlParams = new URLSearchParams(popup.location.search);
                const learnerId = urlParams.get('learner_id');
                const error = urlParams.get('error');

                if (error) {
                    console.error('❌ Erreur Google:', error);
                    showToast('❌ ' + decodeURIComponent(error));
                    return;
                }

                if (learnerId) {
                    fetchAndRedirect(learnerId);
                } else {
                    showToast('❌ Échec de la connexion : learner_id manquant');
                }
            }
        } catch (e) {
            // Cross-origin : popup toujours sur accounts.google.com
        }

        if (popup.closed) {
            clearInterval(timer);
            console.log('ℹ️ Popup fermée par l\'utilisateur');
        }
    }, 300);
}

async function fetchAndRedirect(learnerId) {
    try {
        const res = await fetch(`${API_BASE}/api/learner/?learner_id=${learnerId}`);
        const data = await res.json();

        if (data.success) {
            const learner = data.learner;
            localStorage.setItem('learner_id', learner.learner_id);
            localStorage.setItem('learner_name', learner.name);
            localStorage.setItem('learner_email', learner.email);
            localStorage.setItem('learner_cefr_level', learner.cefr_level || '');
            localStorage.setItem('learner_progress', learner.progress || '0');

            showToast('✅ Connexion réussie ! Redirection...');
            setTimeout(() => {
                window.location.href = `${API_BASE}/?learner_id=${learnerId}`;
            }, 800);
        } else {
            showToast('❌ Erreur lors de la récupération du profil');
        }
    } catch (e) {
        console.error('❌ fetchAndRedirect:', e);
        showToast('❌ Erreur réseau');
    }
}

    console.log('Register Page chargée ✅');
});