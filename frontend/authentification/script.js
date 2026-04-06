// ============================================
// EnglishLearn - Authentification (popup OAuth2)
// ============================================

const API_BASE = 'http://localhost:8000';
const GOOGLE_CLIENT_ID = '785314051038-7di17e812h2qju4cdd1c7gmv7j20enrs.apps.googleusercontent.com';
const GOOGLE_REDIRECT = 'http://localhost:8000/api/auth/google/callback/';

document.addEventListener('DOMContentLoaded', function() {
    const loginBtn    = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const googleBtn   = document.getElementById('googleBtn');

    // Navigation vers login
    loginBtn.addEventListener('click', function() {
        this.style.transform = 'scale(0.98)';
        setTimeout(() => {
            this.style.transform = '';
            window.location.href = 'http://localhost:8000/login/';
        }, 150);
    });

    // Navigation vers register
    registerBtn.addEventListener('click', function() {
        this.style.transform = 'scale(0.98)';
        setTimeout(() => {
            this.style.transform = '';
            window.location.href = 'http://localhost:8000/register/';
        }, 150);
    });

    // Google Sign-In avec popup (identique à login.js)
    googleBtn.addEventListener('click', function() {
        this.style.transform = 'scale(0.98)';
        setTimeout(() => {
            this.style.transform = '';
            startGoogleOAuthPopup();
        }, 150);
    });

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

        console.log('🚀 Ouverture popup Google OAuth2...');
        const popup = window.open(authUrl, 'GoogleLogin', opts);

        if (!popup) {
            showToast('❌ Popup bloquée — autorisez les popups pour ce site');
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
                        showToast('❌ Échec de la connexion: learner_id manquant');
                    }
                }
            } catch (e) {
                // Cross-origin → popup encore sur accounts.google.com
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

    // Effet hover sur les cartes de fonctionnalités
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
            this.style.transition = 'all 0.2s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
        });
    });

    console.log('EnglishLearn Auth Page loaded successfully! ✅');
});

// ============================================
// Toast utilitaire (identique à login.js)
// ============================================
function showToast(message) {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%) translateY(100px);
        background-color: #1f2937;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        opacity: 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        max-width: 90vw;
        text-align: center;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(100px)';
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
    }, 3500);
}