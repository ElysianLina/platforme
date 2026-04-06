// ============================================================
// login.js — SOLUTION DÉFINITIVE Google Sign-In
//
// On abandonne complètement initTokenClient (bloqué par Chrome/FedCM).
// À la place : window.open() vers une URL OAuth2 Google classique.
// Google redirige vers /api/auth/google/callback/?code=... côté Django.
// Django échange le code, crée/trouve le learner, redirige vers /.
// ============================================================

const API_BASE         = 'http://localhost:8000';
const GOOGLE_CLIENT_ID = '785314051038-7di17e812h2qju4cdd1c7gmv7j20enrs.apps.googleusercontent.com';
// ⚠️ Cette URI doit être dans "URIs de redirection autorisés" sur Google Cloud Console
const GOOGLE_REDIRECT  = 'http://localhost:8000/api/auth/google/callback/';

document.addEventListener('DOMContentLoaded', function () {

    const loginForm      = document.getElementById('loginForm');
    const emailInput     = document.getElementById('email');
    const passwordInput  = document.getElementById('password');
    const togglePassword = document.getElementById('togglePassword');
    const rememberMe     = document.getElementById('rememberMe');
    const submitBtn      = document.getElementById('submitBtn');
    const backBtn        = document.getElementById('backBtn');
    const googleBtn      = document.getElementById('googleBtn');
    const registerLink   = document.getElementById('registerLink');
    const forgotPassword = document.querySelector('.forgot-password');
    const eyeIcon        = document.getElementById('eyeIcon');

    let isLoading = false;

    // ── Icônes œil ──────────────────────────────────────────────
    const eyeSlash = `
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94
                 M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19
                 m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>`;
    const eyeOpen = `
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle cx="12" cy="12" r="3"></circle>`;

    togglePassword.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        eyeIcon.innerHTML = type === 'password' ? eyeSlash : eyeOpen;
    });

    // ── Validation ───────────────────────────────────────────────
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function validateForm() {
        let valid = true;
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
        return valid;
    }

    [emailInput, passwordInput].forEach(i => i.addEventListener('input', function () {
        this.classList.remove('error');
    }));

    // ── Soumission formulaire classique ──────────────────────────
    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (isLoading) return;
        if (!validateForm()) { showToast('Veuillez vérifier vos informations', 'error'); return; }

        isLoading = true;
        submitBtn.disabled = true;
        const originalContent = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading"></span>';

        try {
            const response = await fetch(`${API_BASE}/api/login/`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email:    emailInput.value,
                    password: passwordInput.value
                })
            });

            const data = await response.json();

            if (data.success) {
                const learner = data.learner;
                localStorage.setItem('learner_id',         learner.learner_id);
                localStorage.setItem('learner_name',       learner.name);
                localStorage.setItem('learner_email',      learner.email);
                localStorage.setItem('learner_cefr_level', learner.cefr_level);
                localStorage.setItem('learner_progress',   learner.progress);

                if (rememberMe.checked) {
                    localStorage.setItem('rememberedEmail', learner.email);
                } else {
                    localStorage.removeItem('rememberedEmail');
                }

                showToast('Connexion réussie ! Redirection...', 'success');
                setTimeout(() => {
                    window.location.href = `${API_BASE}/?learner_id=${learner.learner_id}`;
                }, 1000);

            } else {
                showToast(data.errors?.[0] || 'Email ou mot de passe incorrect', 'error');
                submitBtn.innerHTML = originalContent;
                submitBtn.disabled  = false;
                isLoading = false;
            }

        } catch (error) {
            console.error('Erreur réseau:', error);
            showToast('Erreur de connexion au serveur', 'error');
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled  = false;
            isLoading = false;
        }
    });

    // ── Bouton retour ────────────────────────────────────────────
    backBtn.addEventListener('click', () => window.history.back());

    // ── Bouton Google — window.open() OAuth2 Authorization Code ──
    googleBtn.addEventListener('click', function () {
        // Construire l'URL OAuth2 Google
        const params = new URLSearchParams({
            client_id:     GOOGLE_CLIENT_ID,
            redirect_uri:  GOOGLE_REDIRECT,
            response_type: 'code',           // Authorization Code flow
            scope:         'openid email profile',
            access_type:   'online',
            prompt:        'select_account', // Toujours montrer le sélecteur de compte
        });

        const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;

        // Centrer la popup
        const w    = 500, h = 620;
        const left = Math.round((window.screen.width  - w) / 2);
        const top  = Math.round((window.screen.height - h) / 2);
        const opts = `width=${w},height=${h},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes`;

        console.log('🚀 Ouverture popup Google OAuth2...');
        const popup = window.open(authUrl, 'GoogleLogin', opts);

        if (!popup) {
            showToast('❌ Popup bloquée — autorisez les popups pour ce site', 'error');
            return;
        }

        

        // Surveiller la fermeture de la popup
        // Django redirige la popup vers /?learner_id=... après succès
        // On détecte ça en surveillant l'URL de la popup
        const timer = setInterval(() => {
            try {
                // Si la popup a été redirigée vers notre domaine
                const popupUrl = popup.location.href;
                if (popupUrl && popupUrl.startsWith(API_BASE)) {
                    clearInterval(timer);
                    popup.close();

                    // Extraire learner_id de l'URL de redirection
                    const urlParams = new URLSearchParams(popup.location.search);
                    const learnerId = urlParams.get('learner_id');
                    const error     = urlParams.get('error');

                    if (error) {
                        console.error('❌ Erreur Google:', error);
                        showToastGlobal('❌ ' + decodeURIComponent(error));
                        return;
                    }

                    if (learnerId) {
                        // Récupérer les infos du learner depuis Django
                        fetchAndRedirect(learnerId);
                    }
                }
            } catch (e) {
                // Cross-origin → popup encore sur accounts.google.com → normal
            }

            // Popup fermée manuellement par l'utilisateur
            if (popup.closed) {
                clearInterval(timer);
                console.log('ℹ️ Popup fermée par l\'utilisateur');
            }
        }, 300);
    });

    // ── Récupérer les infos learner après redirection ────────────
    async function fetchAndRedirect(learnerId) {
        try {
            const res  = await fetch(`${API_BASE}/api/learner/?learner_id=${learnerId}`);
            const data = await res.json();

            if (data.success) {
                const learner = data.learner;
                localStorage.setItem('learner_id',         learner.learner_id);
                localStorage.setItem('learner_name',       learner.name);
                localStorage.setItem('learner_email',      learner.email);
                localStorage.setItem('learner_cefr_level', learner.cefr_level || '');
                localStorage.setItem('learner_progress',   learner.progress   || '0');
                showToastGlobal('✅ Connexion réussie ! Redirection...');
                setTimeout(() => {
                    window.location.href = `${API_BASE}/?learner_id=${learnerId}`;
                }, 800);
            }
        } catch (e) {
            console.error('❌ fetchAndRedirect:', e);
        }
    }

    // ── Lien inscription ─────────────────────────────────────────
    registerLink.addEventListener('click', function (e) {
        e.preventDefault();
        window.location.href = `${API_BASE}/register/`;
    });

    // ── Mot de passe oublié ──────────────────────────────────────
    forgotPassword.addEventListener('click', function (e) {
        e.preventDefault();
        window.location.href = `${API_BASE}/reset-request/`;
    });

    // ── Toast interne ────────────────────────────────────────────
    function showToast(message, type = 'info') {
        document.querySelector('.toast')?.remove();
        const toast = document.createElement('div');
        toast.className   = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ── Remember me ──────────────────────────────────────────────
    const remembered = localStorage.getItem('rememberedEmail');
    if (remembered) { emailInput.value = remembered; rememberMe.checked = true; }

    // ── Focus animations ─────────────────────────────────────────
    document.querySelectorAll('.form-input').forEach(input => {
        input.addEventListener('focus', function () {
            this.parentElement.style.transform  = 'scale(1.02)';
            this.parentElement.style.transition = 'transform 0.2s';
        });
        input.addEventListener('blur', function () {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    console.log('Login Page chargée ✅');
});

// ── Toast global ─────────────────────────────────────────────
function showToastGlobal(message) {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className   = 'toast-notification';
    toast.style.cssText = `
        position: fixed; bottom: 20px; left: 50%;
        transform: translateX(-50%) translateY(100px);
        background-color: #1f2937; color: white;
        padding: 12px 24px; border-radius: 8px;
        font-size: 14px; z-index: 1000; opacity: 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 90vw; text-align: center;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity   = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity   = '0';
        toast.style.transform = 'translateX(-50%) translateY(100px)';
        setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3500);
}