// ============================================================
// startlevel.js — servi par Django :8000 via {% static %}
// ✅ FIX : récupère learner_id depuis l'URL si localStorage vide
//          (car localStorage :8080 ≠ localStorage :8000)
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    console.log('=== startlevel.js ===');
    console.log('URL:', window.location.href);

    // ✅ Récupérer learner_id depuis l'URL (?learner_id=...) 
    //    et le sauvegarder dans localStorage :8000
    const urlParams = new URLSearchParams(window.location.search);
    const learnerIdFromUrl = urlParams.get('learner_id');
    if (learnerIdFromUrl) {
        localStorage.setItem('learner_id', learnerIdFromUrl);
        console.log('✅ learner_id récupéré depuis URL et stocké:', learnerIdFromUrl);
        // Nettoyer l'URL sans recharger la page
        window.history.replaceState({}, document.title, '/start-test/');
    }

    console.log('learner_id dans localStorage:', localStorage.getItem('learner_id'));

    // ✅ Récupérer aussi name et email depuis l'URL
const nameFromUrl = urlParams.get('name');
const emailFromUrl = urlParams.get('email');

if (nameFromUrl && nameFromUrl !== 'null') {
    localStorage.setItem('learner_name', decodeURIComponent(nameFromUrl));
    console.log('✅ name récupéré depuis URL:', decodeURIComponent(nameFromUrl));
}

if (emailFromUrl && emailFromUrl !== 'null') {
    localStorage.setItem('learner_email', decodeURIComponent(emailFromUrl));
    console.log('✅ email récupéré depuis URL:', decodeURIComponent(emailFromUrl));
}


    //  Gestion de la flèche retour et modal "Quit the test?"
    // ============================================================
    
    const btnBack = document.getElementById('btn-back');
    const modalQuit = document.getElementById('modal-quit');
    const btnCloseModal = document.getElementById('btn-close-modal-start');
    const btnRestart = document.getElementById('btn-restart-start');
    const btnQuit = document.getElementById('btn-quit-start');

    // Ouvrir la modal quand on clique sur la flèche
    if (btnBack) {
        btnBack.addEventListener('click', function() {
            if (modalQuit) modalQuit.classList.remove('hidden');
        });
    }

    // Fermer la modal (bouton X)
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', function() {
            if (modalQuit) modalQuit.classList.add('hidden');
        });
    }

    // Fermer la modal si on clique en dehors
    if (modalQuit) {
        modalQuit.addEventListener('click', function(e) {
            if (e.target === modalQuit) {
                modalQuit.classList.add('hidden');
            }
        });
    }

    // Bouton "Restart test" → redirige vers preferences
    if (btnRestart) {
        btnRestart.addEventListener('click', function() {
            const learnerId = localStorage.getItem('learner_id');
            const name = localStorage.getItem('learner_name') || '';
            const email = localStorage.getItem('learner_email') || '';
            
            // Rediriger vers preferences avec les données
            window.location.href = `/start-test/?learner_id=${learnerId}&name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`;
        });
    }

    // Bouton "Quit" → redirige vers home
    if (btnQuit) {
        btnQuit.addEventListener('click', function() {
            const learnerId = localStorage.getItem('learner_id');
            const name = localStorage.getItem('learner_name') || '';
            const email = localStorage.getItem('learner_email') || '';
            const cefrLevel = localStorage.getItem('learner_cefr_level') || 'A1';
            
            // Rediriger vers home
            const redirectUrl = `/?learner_id=${learnerId}&cefr_level=${cefrLevel}&name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`;
            window.location.href = redirectUrl;
        });
    }

    // ============================================================

    const startBtn = document.getElementById('startBtn');

    startBtn.addEventListener('click', async function () {
        this.style.transform = 'scale(0.95)';
        this.disabled = true;
        this.textContent = 'Chargement...';

        setTimeout(async () => {
            this.style.transform = '';

            const learnerId = localStorage.getItem('learner_id');
            if (!learnerId) {
                alert('Vous devez être connecté pour passer le test.');
                window.location.href = '/login/';
                return;
            }

            try {
                const response = await fetch('/api/test/demarrer/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ learner_id: learnerId })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    localStorage.setItem('current_test_id', data.test_id);
                    // ✅ FIX : passer learner_id + name + email dans l'URL
                    // pour que test-cefr.js les transmette ensuite à home.js
                    const n = encodeURIComponent(localStorage.getItem('learner_name')  || '');
                    const e = encodeURIComponent(localStorage.getItem('learner_email') || '');
                    const lid = localStorage.getItem('learner_id') || '';
                    window.location.href = `/test-cefr/?test_id=${data.test_id}&learner_id=${lid}&name=${n}&email=${e}`;

                } else if (data.test_id) {
                    if (confirm('Un test est déjà en cours. Voulez-vous le reprendre ?')) {
                        localStorage.setItem('current_test_id', data.test_id);
                        const n = encodeURIComponent(localStorage.getItem('learner_name')  || '');
                        const e = encodeURIComponent(localStorage.getItem('learner_email') || '');
                        const lid = localStorage.getItem('learner_id') || '';
                        window.location.href = `/test-cefr/?test_id=${data.test_id}&learner_id=${lid}&name=${n}&email=${e}`;
                    } else {
                        startBtn.disabled = false;
                        startBtn.textContent = 'Find my level';
                    }
                } else {
                    alert('Erreur : ' + (data.message || data.error || 'Impossible de démarrer le test'));
                    startBtn.disabled = false;
                    startBtn.textContent = 'Find my level';
                }

            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur de connexion au serveur');
                startBtn.disabled = false;
                startBtn.textContent = 'Find my level';
            }
        }, 150);
    });

    // Animation flottante
    const illustration = document.querySelector('.illustration');
    if (illustration) {
        setInterval(() => {
            illustration.style.transform = `translateY(${Math.sin(Date.now() / 1000) * 5}px)`;
        }, 50);
    }
});