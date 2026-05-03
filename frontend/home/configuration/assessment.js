// ============================================================
// test-cefr.js — servi par Django :8000 via {% static %}
// ✅ FIX 1 : showScreen utilise display:none (pas juste hidden)
// ✅ FIX 2 : index passé à afficherQuestion
// ============================================================

const API_BASE = '/api';

// Récupérer les paramètres de l'URL au cas où ils sont passés par preferences.js
const urlParams = new URLSearchParams(window.location.search);
const idFromUrl = urlParams.get('learner_id');
const nameFromUrl = urlParams.get('name');
const emailFromUrl = urlParams.get('email');

// Si les paramètres sont dans l'URL, les stocker dans localStorage
if (idFromUrl && idFromUrl !== 'null') {
    localStorage.setItem('learner_id', idFromUrl);
    console.log('✅ learner_id récupéré depuis URL:', idFromUrl);
}
if (nameFromUrl && nameFromUrl !== 'null') {
    localStorage.setItem('learner_name', decodeURIComponent(nameFromUrl));
    console.log('✅ name récupéré depuis URL:', decodeURIComponent(nameFromUrl));
}
if (emailFromUrl && emailFromUrl !== 'null') {
    localStorage.setItem('learner_email', decodeURIComponent(emailFromUrl));
    console.log('✅ email récupéré depuis URL:', decodeURIComponent(emailFromUrl));
}

function getLearnerId() {
    const id = localStorage.getItem('learner_id');
    // Rejeter null, undefined, "null", "undefined", chaîne vide
    if (!id || id === 'null' || id === 'undefined' || id === '') {
        // Essayer depuis l'URL
        const urlParams = new URLSearchParams(window.location.search);
        const idFromUrl = urlParams.get('learner_id');
        if (idFromUrl && idFromUrl !== 'null' && idFromUrl !== '') {
            localStorage.setItem('learner_id', idFromUrl);
            return idFromUrl;
        }
        return null;
    }
    return id;
}

// Récupérer les valeurs au moment de l'exécution, pas au chargement
const LEARNER_ID = getLearnerId();
const LEARNER_NAME = localStorage.getItem('learner_name') || '';
const LEARNER_EMAIL = localStorage.getItem('learner_email') || '';

// Debug
console.log('🔍 LEARNER_ID:', LEARNER_ID);
console.log('🔍 LEARNER_NAME:', LEARNER_NAME);
console.log('🔍 LEARNER_EMAIL:', LEARNER_EMAIL);



const TEST_ID = urlParams.get('test_id') || localStorage.getItem('current_test_id');

// ✅ FIX : récupérer name, email, learner_id depuis l'URL et les stocker dans localStorage :8000

const lidFromUrl   = urlParams.get('learner_id');
if (lidFromUrl   && lidFromUrl   !== 'null') localStorage.setItem('learner_id',    lidFromUrl);
if (nameFromUrl  && nameFromUrl  !== 'null') localStorage.setItem('learner_name',  decodeURIComponent(nameFromUrl));
if (emailFromUrl && emailFromUrl !== 'null') localStorage.setItem('learner_email', decodeURIComponent(emailFromUrl));

if (!TEST_ID) {
    alert('Aucun test détecté. Redirection...');
    window.location.href = '/start-test/';
}
if (!LEARNER_ID) {
    alert('Vous devez être connecté.');
    window.location.href = '/login/';
}


if (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) {
    const navType = performance.getEntriesByType('navigation')[0].type;
    
    if (navType === 'back_forward') {
        console.log('Détection retour arrière, rechargement...');
        window.location.reload();
    }
}

const state = {
    testId: TEST_ID,
    currentIndex: 0,
    totalQuestions: 30,
    startTime: Date.now(),
    questionStartTime: null,
    timerInterval: null,
    // AJOUT pour limiter le temps de la session
    timeLimitMs: 15 * 60 * 1000, // 15 minutes
    testEnded: false,

    globalTimeoutId: null,
    remainingTime: null, //pour stocker le temps restant quand on met en pause
};

// ── Écrans ───────────────────────────────────────────────────
const screens = {
    loading:  document.getElementById('screen-loading'),
    question: document.getElementById('screen-question'),
    results:  document.getElementById('screen-results')
};

// ✅ FIX : utiliser display:none pour vraiment cacher le spinner
// classList.add('hidden') seul ne suffit pas si .hidden n'est pas défini en CSS
function showScreen(name) {
    Object.values(screens).forEach(s => {
        s.classList.add('hidden');
        s.style.display = 'none'; // ← force le masquage
    });
    screens[name].classList.remove('hidden');
    screens[name].style.display = ''; // ← laisse le CSS reprendre
}

// ── Appel API ────────────────────────────────────────────────
async function apiCall(endpoint, method = 'GET', data = null) {
    // Récupérer frais à chaque appel
    const currentLearnerId = getLearnerId();
    
    if (!currentLearnerId) {
        console.error('❌ Pas de learner_id disponible');
        throw new Error('Non authentifié');
    }
    
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (method === 'POST') {
        options.body = JSON.stringify({ ...(data || {}), learner_id: currentLearnerId });
    }
    const url = method === 'GET'
        ? `${API_BASE}${endpoint}${endpoint.includes('?') ? '&' : '?'}learner_id=${currentLearnerId}`
        : `${API_BASE}${endpoint}`;
    
    console.log('📡 API Call:', method, endpoint, 'learner_id:', currentLearnerId);
    
    const response = await fetch(url, options);
    return response.json();
}

// ── Init ─────────────────────────────────────────────────────
async function initTest() {
    try {
        const prog = await apiCall(`/test/${state.testId}/progression/`);
        state.totalQuestions = prog.total_questions || 30;
        document.getElementById('total-questions').textContent = state.totalQuestions;
        const startIndex = (prog.repondues < prog.total_questions) ? prog.repondues : 0;
        await chargerQuestion(startIndex);
    } catch (error) {
        console.error('Erreur init:', error);
        alert('Erreur de connexion au serveur');
    }
}

// ── Charger une question ─────────────────────────────────────
async function chargerQuestion(index) {
    showScreen('loading');

    

    try {

         // RÉAFFICHER le bouton X pendant le test
        const btnAbandon = document.getElementById('btn-abandon');
        if (btnAbandon) btnAbandon.style.display = '';


        const data = await apiCall(`/test/${state.testId}/question/${index}/`);
        if (data.error) { alert(data.error); return; }

        state.currentIndex = index;
        state.questionStartTime = Date.now();
        afficherQuestion(data, index); 
        mettreAJourProgression();
        demarrerTimer();
        showScreen('question');
    } catch (error) {
        console.error('Erreur chargement:', error);
    }
}

// ── Afficher une question ────────────────────────────────────
function afficherQuestion(data, index) { // ✅ index en paramètre
    const q = data.question;

    const catLabels = { grammar: 'Grammar', vocabulary: 'Vocabulary', listening: 'Listening' };
    document.getElementById('question-category').textContent = catLabels[q.categorie] || q.categorie;
    document.getElementById('question-level').textContent = q.niveau;

    const audioSection = document.getElementById('audio-section');

    const audioEl = document.getElementById('audio-element');
const playBtn = document.getElementById('btn-play-audio');
const playIcon = document.getElementById('play-icon');
const audioText = document.getElementById('audio-text');

   if (data.audio) {
    audioSection.classList.remove('hidden');
    audioSection.style.display = '';
    
    // Reset audio element
    audioEl.src = `/media/test_audio/${data.audio.fichier}`;
    audioEl.load();
    
    // Reset button state
    updatePlayButton(false);
    
    // Fonction pour mettre à jour le bouton
    function updatePlayButton(isPlaying) {
        if (isPlaying) {
            playIcon.textContent = '⏸️';  // Icône pause
            audioText.textContent = 'Pause audio';
            playBtn.classList.add('playing');
        } else {
            playIcon.textContent = '▶️';  // Icône play
            audioText.textContent = 'Play audio';
            playBtn.classList.remove('playing');
        }
    }
    
    // Gestion du clic Play/Pause
    playBtn.onclick = () => {
        if (audioEl.paused) {
            audioEl.play();
            updatePlayButton(true);
        } else {
            audioEl.pause();
            updatePlayButton(false);
        }
    };
    
    // Quand l'audio se termine, reset le bouton
    audioEl.onended = () => {
        updatePlayButton(false);
        audioEl.currentTime = 0;  // Remettre au début
    };
    
    // Quand l'audio est en pause (automatique), mettre à jour le bouton
    audioEl.onpause = () => {
        if (!audioEl.ended) {
            updatePlayButton(false);
        }
    };
    
    // Quand l'audio joue, s'assurer que le bouton est en mode pause
    audioEl.onplay = () => {
        updatePlayButton(true);
    };
    
} else {
    audioSection.classList.add('hidden');
    audioSection.style.display = 'none';
    // Reset l'audio quand il n'y en a pas
    audioEl.pause();
    audioEl.src = '';
}

    document.getElementById('question-text').innerHTML = q.enonce.replace(/___/g,
        '<span style="border-bottom:2px solid #6366f1;min-width:60px;display:inline-block;">&nbsp;&nbsp;&nbsp;&nbsp;</span>'
    );
// ── Détection multi-réponses ─────────────────────────────────
const trouCount = (q.enonce.match(/___/g) || []).length;  // Compte les ___
const isMultiAnswer = trouCount > 1;  // Vrai si 2+ trous

// ── Création des réponses ───────────────────────────────────
    const container = document.getElementById('answers-container');
    container.innerHTML = '';
   
   if (q.type === 'mcq' || (q.type === 'fill_blank' && q.options)) {
     if (isMultiAnswer) {
        const instruction = document.createElement('div');
        instruction.className = 'multi-answer-instruction';
        instruction.textContent = `Select ${trouCount} answers (one for each blank)`;
       
        container.appendChild(instruction);
    }
    // Pour multi-réponses : utiliser des checkboxes au lieu de radio
    const inputType = isMultiAnswer ? 'checkbox' : 'radio';
    const nameAttr = isMultiAnswer ? `answer_${q.id}[]` : 'answer';
    
    q.options.forEach((opt, idx) => {
        const div = document.createElement('div');
        div.className = 'answer-option';
        div.innerHTML = `
            <input type="${inputType}" name="${nameAttr}" id="opt_${idx}" value="${opt}">
            <label for="opt_${idx}">${opt}</label>`;
        
        div.addEventListener('click', () => {
            if (isMultiAnswer) {
                // Mode multi-réponses : toggle la sélection
                const checkbox = div.querySelector('input');
                checkbox.checked = !checkbox.checked;
                div.classList.toggle('selected', checkbox.checked);
                
                // Vérifier si on a assez de réponses
                const selectedCount = container.querySelectorAll('input:checked').length;
                document.getElementById('btn-next').disabled = selectedCount !== trouCount;
            } else {
                // Mode simple : une seule réponse
                document.querySelectorAll('.answer-option').forEach(el => el.classList.remove('selected'));
                div.classList.add('selected');
                div.querySelector('input').checked = true;
                document.getElementById('btn-next').disabled = false;
            }
        });
        container.appendChild(div);
    });
} else {
    // AJOUT : Titre pour saisie manuelle

    const title = document.createElement('div');
    title.className = 'manual-input-title';
    title.textContent = trouCount > 1 ? 'Fill in the blanks' : 'Fill in the blank';
   
    container.appendChild(title);
    
    // Saisie manuelle pour multi-réponses
    if (isMultiAnswer) {
        for (let i = 1; i <= trouCount; i++) {
            // Label pour chaque trou
            const label = document.createElement('label');
            label.textContent = `Blank ${i}:`;
            label.style.cssText = 'display: block; margin: 15px 0 5px; color: #666; font-size: 13px; font-weight: 500;';
            container.appendChild(label);
            
            // Input
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'answer-input';
            input.placeholder = `Answer ${i}...`;
            input.id = `manual-answer-${i}`;
            input.dataset.index = i;
            
            input.addEventListener('input', () => {
                // Vérifier que tous les champs sont remplis
                const allFilled = Array.from({length: trouCount}, (_, j) => {
                    return document.getElementById(`manual-answer-${j+1}`)?.value.trim();
                }).every(v => v);
                
                document.getElementById('btn-next').disabled = !allFilled;
            });
            
            container.appendChild(input);
        }
    } else {
        // Saisie simple
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'answer-input';
        input.placeholder = 'Type your answer...';
        input.id = 'manual-answer';
        input.addEventListener('input', () => {
            document.getElementById('btn-next').disabled = !input.value.trim();
        });
        container.appendChild(input);
    }
}

    if (data.deja_repondu && data.reponse_precedente) {
        if (q.type === 'mcq' || q.type === 'fill_blank') {
            document.querySelectorAll('.answer-option').forEach(el => {
                if (el.querySelector('input').value === data.reponse_precedente) {
                    el.classList.add('selected');
                    el.querySelector('input').checked = true;
                }
            });
        } else {
            const inp = document.getElementById('manual-answer');
            if (inp) inp.value = data.reponse_precedente;
        }
        document.getElementById('btn-next').disabled = false;
    } else {
        document.getElementById('btn-next').disabled = true;
    }

    document.getElementById('btn-prev').disabled = index === 0; // ✅ utilise le paramètre
    document.getElementById('btn-next').textContent =
        state.currentIndex >= state.totalQuestions - 1 ? 'Finish' : 'Next →';
}

function obtenirReponse() {
    // Vérifier si c'est une question multi-réponses
    const checkboxes = document.querySelectorAll('input[name^="answer_"]:checked');
    if (checkboxes.length > 0) {
        // Multi-réponses : retourner un tableau
        return Array.from(checkboxes).map(cb => cb.value).join(' | ');
    }
    
    // Réponse simple (radio ou texte)
    const checked = document.querySelector('input[name="answer"]:checked');
    if (checked) return checked.value;
    
    const manual = document.getElementById('manual-answer');
    if (manual) return manual.value.trim();
    
    // Multi-réponses manuelles
    const multiInputs = document.querySelectorAll('[id^="manual-answer-"]');
    if (multiInputs.length > 0) {
        return Array.from(multiInputs).map(inp => inp.value.trim()).join(' | ');
    }
    
    return '';
}

// ── Soumettre ────────────────────────────────────────────────
async function soumettreEtAvancer() {
    const reponse = obtenirReponse();
    if (!reponse) return;
    const temps = Math.round((Date.now() - state.questionStartTime) / 1000);
    document.getElementById('btn-next').disabled = true;
    try {
        const data = await apiCall(
            `/test/${state.testId}/question/${state.currentIndex}/repondre/`,
            'POST',
            { reponse, temps_reponse_sec: temps }
        );
        if (data.est_derniere || state.currentIndex >= state.totalQuestions - 1) {
            await terminerTest();
        } else {
            await chargerQuestion(state.currentIndex + 1);
        }
    } catch (error) {
        console.error('Erreur soumission:', error);
        document.getElementById('btn-next').disabled = false;
    }
}

// ── Terminer ─────────────────────────────────────────────────
async function terminerTest() {
    showScreen('loading');
    clearInterval(state.timerInterval);
    
    // Annuler le timeout des 15 minutes
    if (state.globalTimeoutId) {
        clearTimeout(state.globalTimeoutId);
        state.globalTimeoutId = null;
    }
    state.testEnded = true;
    
    try {
        const data = await apiCall(`/test/${state.testId}/terminer/`, 'POST');
        afficherResultats(data);
    } catch (error) {
        console.error('Erreur terminaison:', error);
        alert('Erreur lors de la finalisation du test');
    }
}

// ── Résultats ────────────────────────────────────────────────
function afficherResultats(data) {

    document.getElementById('btn-abandon').style.display = 'none';

    showScreen('results');
    document.getElementById('final-level').textContent  = data.niveau_final || '?';
    document.getElementById('level-name').textContent   = data.nom_niveau || '';
    document.getElementById('stat-score').textContent   = data.score_global + '%';
    document.getElementById('stat-correct').textContent = `${data.reponses_correctes || 0}/${data.total_reponses || 30}`;

    // MODIFIÉ : Plafonner le temps à 15 minutes maximum
    const maxTimeMs = 15 * 60 * 1000; // 15 minutes en millisecondes
    const rawTime = Date.now() - state.startTime;
    const cappedTime = Math.min(rawTime, maxTimeMs); // Prend le minimum entre temps réel et 15 min
    
    const secs = Math.round(cappedTime / 1000);
    const minutes = Math.floor(secs / 60);
    const seconds = secs % 60;
    
    // Format MM:SS avec plafond à 15:00
    document.getElementById('stat-time').textContent =
        `${String(Math.min(minutes, 15)).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    const container = document.getElementById('breakdown-bars');
    container.innerHTML = '';
    ['A1','A2','B1','B2','C1','C2'].forEach(niv => {
        const score = data.scores_par_niveau?.[niv] ?? 0;
        const bar = document.createElement('div');
        bar.className = 'breakdown-bar';
        bar.innerHTML = `
            <span class="breakdown-label">${niv}</span>
            <div class="breakdown-track">
                <div class="breakdown-fill ${niv.toLowerCase()}" style="width:${score}%"></div>
            </div>
            <span class="breakdown-value">${score}%</span>`;
        container.appendChild(bar);
    });

    if (data.niveau_final) {
        localStorage.setItem('learner_cefr_level', data.niveau_final);
        localStorage.setItem('learner_id', LEARNER_ID);
    }
}

function mettreAJourProgression() {
    const pct = ((state.currentIndex + 1) / state.totalQuestions) * 100;
    document.getElementById('current-question').textContent = state.currentIndex + 1;
    document.getElementById('progress-fill').style.width = pct + '%';
}



function demarrerTimer() {
    if (state.timerInterval) {
        console.log('⚠️ Timer affichage existe déjà, on ne recrée pas');
        return;
    }
    
    console.log('🟢 Démarrage timer affichage');
    state.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        const timeStr = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        document.getElementById('timer').textContent = timeStr;
        
        console.log('⏱️ Affichage:', timeStr);  // Log pour debug
    }, 1000);
}



//  Terminer le test automatiquement 
async function terminerTestForce() {
    showScreen('loading');
    clearInterval(state.timerInterval);
    
    // ✅ AJOUT : Annuler le timeout (déjà en cours mais par sécurité)
    if (state.globalTimeoutId) {
        clearTimeout(state.globalTimeoutId);
        state.globalTimeoutId = null;
    }
    state.testEnded = true;
    
    try {
        const data = await apiCall(`/test/${state.testId}/terminer/`, 'POST');
        afficherResultats(data);
    } catch (error) {
        console.error('Erreur:', error);
        window.location.href = '/start-test/';
    }
}

// ── Abandon ──────────────────────────────────────────────────
function confirmerAbandon() { 
    document.getElementById('modal-abandon').classList.remove('hidden');

    console.log('🔴 Modal ouverte - Arrêt des timers');
    
    // Arrêter le timer d'affichage
    clearInterval(state.timerInterval);
    state.timerInterval = null;  // ✅ S'assurer que c'est null
    console.log('   timerInterval arrêté');
    
    state.pauseStartTime = Date.now();
    
    if (state.globalTimeoutId) {
        clearTimeout(state.globalTimeoutId);
        state.globalTimeoutId = null;
        console.log('   globalTimeoutId arrêté');
    }
    
    const elapsed = Date.now() - state.startTime;
    state.remainingTime = Math.max(0, state.timeLimitMs - elapsed);
    console.log('   Temps restant calculé:', Math.floor(state.remainingTime/1000), 's');
}
function annulerAbandon()    { 
   
   
    document.getElementById('modal-abandon').classList.add('hidden');

 }
//Fonction pour fermer la modal et reprendre le test
function fermerModalEtReprendre() {
    document.getElementById('modal-abandon').classList.add('hidden');
    
    // S'ASSURER que timerInterval est bien null avant de redémarrer
    state.timerInterval = null;
    
    // Ajuster startTime pour compenser la pause
    if (state.pauseStartTime) {
        const pauseDuration = Date.now() - state.pauseStartTime;
        state.startTime += pauseDuration;
        state.pauseStartTime = null;
    }
    
    // Redémarrer le timer d'affichage
    demarrerTimer();  // Maintenant il va bien créer un nouveau interval
    
    // Redémarrer le timer global
    if (!state.testEnded && state.remainingTime > 0) {
        state.globalTimeoutId = setTimeout(() => {
            if (!state.testEnded) {
                state.testEnded = true;
                alert('Time is up! The test will be submitted automatically.');
                terminerTestForce();
            }
        }, state.remainingTime);
    }
}

async function abandonnerTest() {
    await apiCall(`/test/${state.testId}/abandonner/`, 'POST');
    clearInterval(state.timerInterval);
    localStorage.removeItem('current_test_id');
    window.location.href = '/configuration/';
}

// ── Event Listeners ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTest();

    document.getElementById('btn-next').addEventListener('click', soumettreEtAvancer);
    document.getElementById('btn-prev').addEventListener('click', () => {
        if (state.currentIndex > 0) chargerQuestion(state.currentIndex - 1);
    });
    document.getElementById('btn-abandon').addEventListener('click', confirmerAbandon);
    
    // Event listener pour le bouton X de la modal
    document.getElementById('btn-close-modal').addEventListener('click', fermerModalEtReprendre);
      // bouton "Restart test" → abandonne le test puis redirige vers startlevel.html
document.getElementById('btn-restart-test').addEventListener('click', async () => {
    // Récupérer l'ID du test en cours depuis localStorage
    const currentTestId = localStorage.getItem('current_test_id');
    
    if (currentTestId) {
        try {
            // Abandonner le test via l'API
            await apiCall(`/test/${currentTestId}/abandonner/`, 'POST');
            console.log('Test abandonné avec succès');
        } catch (error) {
            console.error('Erreur lors de l\'abandon:', error);
            // On continue quand même la redirection même si l'API échoue
        }
        
        // Nettoyer le localStorage
        localStorage.removeItem('current_test_id');
    }
    
    // Rediriger vers startlevel.html
   window.location.href = '/assessment/';
});
    





// Bouton "Quit" → abandonne le test puis redirige vers home.html avec les données
document.getElementById('btn-quit-test').addEventListener('click', async () => {
    const currentTestId = localStorage.getItem('current_test_id');
    
    // Récupérer FRAIS le learner_id
    const currentLearnerId = getLearnerId();
    
    // Vérification CRITIQUE
    if (!currentLearnerId) {
        console.error('❌ Impossible de quitter: pas de learner_id');
        alert('Session invalide. Redirection vers login...');
        window.location.href = '/login/';
        return;
    }
    
    let niveauFinal = 'A1';
    let nomNiveau = 'Beginner';
    
    if (currentTestId) {
        try {
            // Appel API avec learner_id frais
            const result = await apiCall(`/test/${currentTestId}/abandonner/`, 'POST', {
                learner_id: currentLearnerId
            });
            console.log('✅ Test abandonné:', result);
            
            if (result.niveau_final) {
                niveauFinal = result.niveau_final;
                nomNiveau = result.nom_niveau;
            }
        } catch (error) {
            console.error('❌ Erreur abandon:', error);
        }
        
        localStorage.removeItem('current_test_id');
    }
    
    // Récupérer depuis localStorage (qui devrait être à jour maintenant)
    const learnerName = localStorage.getItem('learner_name') || '';
    const learnerEmail = localStorage.getItem('learner_email') || '';
    
    // Construire l'URL avec VÉRIFICATION
    const redirectUrl = `/?learner_id=${currentLearnerId}&cefr_level=${niveauFinal}&name=${encodeURIComponent(learnerName)}&email=${encodeURIComponent(learnerEmail)}`;
    
    console.log('🔄 Redirection vers:', redirectUrl);
    
    window.location.href = '/configuration/';
});
  










    document.getElementById('btn-start-learning').addEventListener('click', () => {
        // ✅ FIX BUG 3 : passer name + email + cefr dans l'URL pour que home.js
        // ne lise pas les données d'un ancien apprenant depuis son localStorage
        const _lid   = localStorage.getItem('learner_id')         || LEARNER_ID;
        const _name  = encodeURIComponent(localStorage.getItem('learner_name')       || '');
        const _email = encodeURIComponent(localStorage.getItem('learner_email')      || '');
        const _cefr  = encodeURIComponent(localStorage.getItem('learner_cefr_level') || '');
        window.location.href = `http://localhost:8000/?learner_id=${_lid}&name=${_name}&email=${_email}&cefr_level=${_cefr}`;
    });
    document.addEventListener('keydown', e => {
        if (!screens.question.classList.contains('hidden') &&
            e.key === 'Enter' &&
            !document.getElementById('btn-next').disabled) {
            soumettreEtAvancer();
        }
    });
});