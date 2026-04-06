// ============================================================
// preferences.js
// ✅ Lit learner_id depuis l'URL en priorité
//    (cas Google : script.js redirige avec ?learner_id=X&name=...&email=...)
//    puis depuis localStorage en fallback (cas inscription classique)
//
// LOGIQUE DE SAUVEGARDE (2 appels) :
//   1) savePartialPreferences() → étapes 1-4 sauvegardées AVANT redirection
//      vers le test CEFR (quand l'user choisit "I need help" à l'étape 5)
//   2) saveAllPreferences()     → toutes les données + cefr_level à la fin
//      du quiz (étape 6 : niveau sélectionné manuellement ou retour du test)
// ============================================================

const API_BASE = 'http://localhost:8000';

const state = {
    currentStep: 1,
    totalSteps: 6,
    reason: '',
    interests: [],
    otherInterest: '',
    learningStyle: '',
    otherLearningStyle: '',
    dailyGoal: '',
    userName: 'User',
    otherInterestActive: false,
    otherStyleActive: false,
    levelOption: '',
    cefrLevel: '',
    learnerId: null
};

// ── Récupérer learner_id ─────────────────────────────────────
function getLearnerId() {
    const urlParams = new URLSearchParams(window.location.search);

    const idFromUrl    = urlParams.get('learner_id');
    const nameFromUrl  = urlParams.get('name');
    const emailFromUrl = urlParams.get('email');

    if (idFromUrl && idFromUrl !== 'null' && idFromUrl !== 'undefined' && idFromUrl.trim() !== '') {
        state.learnerId  = idFromUrl;
        state.userName   = nameFromUrl ? decodeURIComponent(nameFromUrl) : 'User';

        localStorage.setItem('learner_id',   idFromUrl);
        localStorage.setItem('learner_name', state.userName);
        if (emailFromUrl) {
            localStorage.setItem('learner_email', decodeURIComponent(emailFromUrl));
        }

        window.history.replaceState({}, document.title, window.location.pathname);
        console.log('✅ learner_id depuis URL:', state.learnerId);
        return state.learnerId;
    }

    const storedId   = localStorage.getItem('learner_id');
    const storedName = localStorage.getItem('learner_name');

    if (storedId && storedId !== 'null' && storedId !== 'undefined' && storedId.trim() !== '') {
        state.learnerId = storedId;
        state.userName  = storedName || 'User';
        console.log('✅ learner_id depuis localStorage:', state.learnerId);
        return state.learnerId;
    }

    console.warn('⚠️ Aucun learner_id — redirection login');
    window.location.href = `${API_BASE}/login/`;
    return null;
}

// ── Charger les préférences existantes ───────────────────────
// Appelée au DOMContentLoaded pour pré-remplir le state
// si l'user revient modifier ses préférences depuis home.html
async function loadExistingPreferences() {
    if (!state.learnerId) return;

    try {
        const response = await fetch(`${API_BASE}/api/preferences/?learner_id=${state.learnerId}`);
        const data     = await response.json();

        if (!data.success || !data.preferences) {
            console.log('ℹ️ Aucune préférence existante');
            return;
        }

        const p = data.preferences;

        // Remplir le state avec les valeurs existantes
        if (p.reason)                              state.reason             = p.reason;
        if (p.interests && p.interests.length > 0) state.interests          = p.interests;
        if (p.other_interest)                      state.otherInterest      = p.other_interest;
        if (p.learning_style)                      state.learningStyle      = p.learning_style;
        if (p.other_style)                         state.otherLearningStyle = p.other_style;
        if (p.daily_goal)                          state.dailyGoal          = p.daily_goal;

        // Récupérer le cefr_level depuis learner
        if (data.learner && data.learner.cefr_level) {
            state.cefrLevel = data.learner.cefr_level;
        }

        console.log('✅ Préférences existantes chargées:', p);

    } catch (err) {
        console.error('❌ Erreur chargement préférences:', err);
    }
}

// ── Initialisation ───────────────────────────────────────────
// ⚠️ async obligatoire pour awaiter loadExistingPreferences()
document.addEventListener('DOMContentLoaded', async () => {
    console.log('=== preferences.js loaded ===');

    getLearnerId();

    // Retour depuis le test de niveau avec niveau détecté
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('step') === '6') {
        state.currentStep = 6;
        const lvl = urlParams.get('level');
        if (lvl && ['A1','A2','B1','B2','C1'].includes(lvl.toUpperCase())) {
            state.cefrLevel = lvl.toUpperCase();
        }
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // ✅ Charger les préférences existantes AVANT d'afficher l'UI
    // (pré-remplit le state si l'user revient depuis home.html)
    await loadExistingPreferences();

    // Afficher le prénom dans l'étape 1
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = state.userName.split(' ')[0] || 'User';
    }

    // ✅ updateUI() appelé UNE SEULE FOIS après que le state est prêt
    updateUI();

    document.addEventListener('click', handleGlobalClick);
});

function handleGlobalClick(event) {
    if (state.currentStep === 2 && state.otherInterestActive) {
        const container = document.getElementById('otherInterestContainer');
        const input     = document.getElementById('otherInterestText');
        if (container && !container.contains(event.target) && input.value.trim() === '') closeOtherInterest();
    }
    if (state.currentStep === 3 && state.otherStyleActive) {
        const container = document.getElementById('otherStyleContainer');
        const input     = document.getElementById('otherStyleText');
        if (container && !container.contains(event.target) && input.value.trim() === '') closeOtherStyle();
    }
}

// ── Navigation ───────────────────────────────────────────────
// ⚠️ handleBack() déclaré UNE SEULE FOIS (doublon supprimé)
function handleBack() {
    if (state.currentStep > 1) { state.currentStep--; updateUI(); }
}

async function handleNext() {
    console.log('handleNext — step:', state.currentStep,
        '| reason:', state.reason,
        '| interests:', state.interests,
        '| learningStyle:', state.learningStyle,
        '| dailyGoal:', state.dailyGoal);

    if (state.currentStep === 5) {
        if (state.levelOption === 'unknown') {
            if (!state.learnerId) {
                alert('You must be logged in to take the test.');
                window.location.href = `${API_BASE}/login/`;
                return;
            }
            // ✅ Sauvegarde partielle (étapes 1-4) avant de partir vers le test
            await savePartialPreferences();

            const learnerName  = localStorage.getItem('learner_name')  || '';
            const learnerEmail = localStorage.getItem('learner_email') || '';
            window.location.href = `${API_BASE}/start-test/?learner_id=${state.learnerId}&name=${encodeURIComponent(learnerName)}&email=${encodeURIComponent(learnerEmail)}`;
            return;
        }
        if (state.levelOption === 'known') {
            state.currentStep = 6; updateUI(); return;
        }
        alert('Please select an option'); return;
    }

    if (state.currentStep < state.totalSteps) { state.currentStep++; updateUI(); }
    else if (state.currentStep === state.totalSteps) { finishQuiz(); }
}

function updateUI() {
    const progress = (state.currentStep / state.totalSteps) * 100;
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = `${progress}%`;

    const backBtn = document.getElementById('backBtn');
    if (backBtn) backBtn.classList.toggle('visible', state.currentStep > 1);

    document.querySelectorAll('.step').forEach((step, i) => {
        step.classList.toggle('active', i + 1 === state.currentStep);
    });

    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) nextBtn.textContent = state.currentStep === state.totalSteps ? 'Finish' : 'Continue';

    const display = document.getElementById('currentStepDisplay');
    if (display) display.textContent = state.currentStep;

    checkCanProceed();
    restoreSelections();
}

function checkCanProceed() {
    const nextBtn = document.getElementById('nextBtn');
    let can = false;
    switch (state.currentStep) {
        case 1: can = state.reason !== ''; break;
        case 2: can = state.interests.length > 0 || state.otherInterest.trim() !== ''; break;
        case 3: can = state.learningStyle === 'autre' ? state.otherLearningStyle.trim() !== '' : state.learningStyle !== ''; break;
        case 4: can = state.dailyGoal !== ''; break;
        case 5: can = state.levelOption !== ''; break;
        case 6: can = state.cefrLevel !== ''; break;
    }
    if (nextBtn) nextBtn.disabled = !can;
}

// ── Step 1 ──────────────────────────────────────────────────
function selectReason(reason) {
    state.reason = reason;
    console.log('✅ reason:', state.reason);
    document.querySelectorAll('#step1 .option-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    checkCanProceed();
    setTimeout(() => { if (state.currentStep === 1) handleNext(); }, 400);
}

// ── Step 2 ──────────────────────────────────────────────────
function toggleInterest(interest, event) {
    if (state.otherInterestActive) closeOtherInterest();
    const idx = state.interests.indexOf(interest);
    const btn = event.currentTarget;
    if (idx > -1) { state.interests.splice(idx, 1); btn.classList.remove('selected'); }
    else          { state.interests.push(interest);  btn.classList.add('selected'); }
    console.log('✅ interests:', state.interests);
    checkCanProceed();
}
function toggleOtherInterest(event) {
    event.stopPropagation();
    state.otherInterestActive ? closeOtherInterest() : openOtherInterest();
}
function openOtherInterest() {
    state.otherInterestActive = true;
    document.getElementById('otherInterestBtn').classList.add('hidden');
    document.getElementById('otherInterestInput').classList.remove('hidden');
    document.getElementById('otherInterestText').focus();
    checkCanProceed();
}
function closeOtherInterest() {
    const input = document.getElementById('otherInterestText');
    if (input.value.trim() !== '') return;
    state.otherInterestActive = false;
    state.otherInterest       = '';
    document.getElementById('otherInterestBtn').classList.remove('hidden');
    document.getElementById('otherInterestInput').classList.add('hidden');
    checkCanProceed();
}
function updateOtherInterest(value) { state.otherInterest = value; checkCanProceed(); }

// ── Step 3 ──────────────────────────────────────────────────
function selectLearningStyle(style) {
    if (state.otherStyleActive && style !== 'autre') closeOtherStyle();
    state.learningStyle = style;
    if (style !== 'autre') state.otherLearningStyle = '';
    document.querySelectorAll('#step3 .option-row').forEach(row => {
        if (!row.classList.contains('other-btn') && !row.closest('.other-option-container')) {
            row.classList.remove('selected');
        }
    });
    if (style !== 'autre') event.currentTarget.classList.add('selected');
    checkCanProceed();
    if (style !== 'autre') {
        setTimeout(() => { if (state.currentStep === 3) handleNext(); }, 400);
    }
}
function toggleOtherStyle(event) {
    event.stopPropagation();
    state.otherStyleActive ? closeOtherStyle() : openOtherStyle();
}
function openOtherStyle() {
    state.otherStyleActive = true;
    state.learningStyle    = 'autre';
    document.getElementById('otherStyleBtn').classList.add('hidden');
    document.getElementById('otherStyleInput').classList.remove('hidden');
    document.getElementById('otherStyleText').focus();
    document.querySelectorAll('#step3 .option-row').forEach(row => {
        if (!row.classList.contains('other-btn') && !row.closest('.other-option-container')) {
            row.classList.remove('selected');
        }
    });
    checkCanProceed();
}
function closeOtherStyle() {
    const input = document.getElementById('otherStyleText');
    if (input.value.trim() !== '') return;
    state.otherStyleActive = false;
    state.learningStyle    = '';
    document.getElementById('otherStyleBtn').classList.remove('hidden');
    document.getElementById('otherStyleInput').classList.add('hidden');
    checkCanProceed();
}
function updateOtherStyle(value) { state.otherLearningStyle = value; checkCanProceed(); }

// ── Step 4 ──────────────────────────────────────────────────
function selectDailyGoal(goal) {
    state.dailyGoal = goal;
    console.log('✅ dailyGoal:', state.dailyGoal);
    document.querySelectorAll('#step4 .option-row').forEach(r => r.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    checkCanProceed();
    setTimeout(() => { if (state.currentStep === 4) handleNext(); }, 400);
}

// ── Step 5 ──────────────────────────────────────────────────
function selectLevelOption(option) {
    state.levelOption = option;
    document.querySelectorAll('#step5 .level-card').forEach(c => c.classList.remove('selected'));
    const card = option === 'known'
        ? document.querySelector('#step5 .level-card:first-child')
        : document.querySelector('#step5 .level-card:last-child');
    if (card) card.classList.add('selected');
    checkCanProceed();
}

// ── Step 6 ──────────────────────────────────────────────────
function selectCEFRLevel(level, element) {
    state.cefrLevel = level;
    console.log('✅ cefrLevel:', state.cefrLevel);
    document.querySelectorAll('#step6 .cefr-card-full').forEach(c => c.classList.remove('selected'));
    element.classList.add('selected');
    checkCanProceed();
}

// ── SAUVEGARDE PARTIELLE (étapes 1-4 uniquement) ─────────────
// Appelée AVANT la redirection vers le test CEFR.
// Pas de cefr_level → Django ne touche pas à Learner.cefr_level.
async function savePartialPreferences() {
    if (!state.learnerId) return;

     // ✅ CORRECTION : Si other_interest est rempli, interests = ["autre"]
    // Sinon, on garde les intérêts sélectionnés normalement
    let interestsToSave = [...state.interests];
    if (state.otherInterest.trim()) {
        interestsToSave = ["autre"];  // ou "other" selon ta préférence
    }

    const payload = {
        learner_id:     state.learnerId,
        reason:         state.reason,
        interests:      interestsToSave,  // ✅ ["autre"] si custom, sinon les intérêts normaux
        other_interest: state.otherInterest.trim(),  // ✅ Le texte personnalisé séparément
        learning_style: state.learningStyle === 'autre' ? 'autre' : state.learningStyle,
        other_style:    state.otherLearningStyle.trim(),
        daily_goal:     state.dailyGoal,
    };
    console.log('📤 savePartialPreferences payload:', payload);

    try {
        const response = await fetch(`${API_BASE}/api/save-preferences/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.success) {
            console.log('✅ Préférences partielles sauvegardées');
        } else {
            console.warn('⚠️ Sauvegarde partielle échouée:', result.error);
        }
    } catch (err) {
        console.error('❌ Erreur savePartialPreferences:', err);
    }
}

// ── SAUVEGARDE COMPLÈTE (étapes 1-4 + cefr_level) ────────────
// Appelée à la fin du quiz (étape 6).
async function saveAllPreferences() {
    if (!state.learnerId || !state.cefrLevel) {
        return { success: false, error: 'Missing learner_id or cefr_level' };
    }

     // MÊME CORRECTION ici
    let interestsToSave = [...state.interests];
    if (state.otherInterest.trim()) {
        interestsToSave = ["autre"];
    }

    const payload = {
        learner_id:     state.learnerId,
        cefr_level:     state.cefrLevel,
        progress:       10,
        reason:         state.reason,
        interests:      interestsToSave,  //  ["autre"] si custom
        other_interest: state.otherInterest.trim(),  // Texte séparé
        learning_style: state.learningStyle === 'autre' ? 'autre' : state.learningStyle,
        other_style:    state.otherLearningStyle.trim(),
        daily_goal:     state.dailyGoal,
    };
    console.log('📤 saveAllPreferences payload:', payload);

    try {
        const response = await fetch(`${API_BASE}/api/save-preferences/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });
        return await response.json();
    } catch (err) {
        console.error('❌ Erreur saveAllPreferences:', err);
        return { success: false, error: err.message };
    }
}

// ── Fin du quiz ──────────────────────────────────────────────
async function finishQuiz() {
    console.log('🏁 finishQuiz — state:', {
        learnerId:     state.learnerId,
        cefrLevel:     state.cefrLevel,
        reason:        state.reason,
        interests:     state.interests,
        learningStyle: state.learningStyle,
        dailyGoal:     state.dailyGoal,
    });

    if (!state.cefrLevel) {
        alert('Please select your level before finishing.');
        return;
    }

    if (state.learnerId && state.cefrLevel) {
        const result = await saveAllPreferences();
        if (result.success) {
            alert('Your level ' + result.cefr_level + ' has been saved!');
            window.location.href = `${API_BASE}/?learner_id=${state.learnerId}`;
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } else {
        window.location.href = `${API_BASE}/`;
    }
}

// ── Keyboard ─────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    const nextBtn = document.getElementById('nextBtn');
    if (e.key === 'Enter' && nextBtn && !nextBtn.disabled) {
        if (document.activeElement.tagName === 'INPUT') return;
        handleNext();
    }
    if (e.key === 'Escape') {
        if (state.otherInterestActive) closeOtherInterest();
        if (state.otherStyleActive)    closeOtherStyle();
    }
});

// ── Restore selections ───────────────────────────────────────
function restoreSelections() {
    if (state.reason) {
        const map   = ['voyage','travail','etudes','culture','communication','Défi personnel'];
        const i     = map.indexOf(state.reason);
        const cards = document.querySelectorAll('#step1 .option-card');
        if (i > -1 && cards[i]) cards[i].classList.add('selected');
    }
    state.interests.forEach(interest => {
        const map  = ['voyage-tourisme','business','cinema','musique','sport'];
        const i    = map.indexOf(interest);
        const btns = document.querySelectorAll('#step2 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    });
    const oiBtn  = document.getElementById('otherInterestBtn');
    const oiInp  = document.getElementById('otherInterestInput');
    const oiText = document.getElementById('otherInterestText');
    if (state.otherInterestActive || state.otherInterest.trim() !== '') {
        if (oiBtn)  oiBtn.classList.add('hidden');
        if (oiInp)  oiInp.classList.remove('hidden');
        if (oiText) oiText.value = state.otherInterest;
        state.otherInterestActive = true;
    } else {
        if (oiBtn) oiBtn.classList.remove('hidden');
        if (oiInp) oiInp.classList.add('hidden');
        state.otherInterestActive = false;
    }
    if (state.learningStyle && state.learningStyle !== 'autre') {
        const map  = ['video','texte','audio'];
        const i    = map.indexOf(state.learningStyle);
        const btns = document.querySelectorAll('#step3 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    }
    const osBtn  = document.getElementById('otherStyleBtn');
    const osInp  = document.getElementById('otherStyleInput');
    const osText = document.getElementById('otherStyleText');
    if (state.otherStyleActive || (state.learningStyle === 'autre' && state.otherLearningStyle.trim() !== '')) {
        if (osBtn)  osBtn.classList.add('hidden');
        if (osInp)  osInp.classList.remove('hidden');
        if (osText) osText.value = state.otherLearningStyle;
        state.otherStyleActive = true;
    } else {
        if (osBtn) osBtn.classList.remove('hidden');
        if (osInp) osInp.classList.add('hidden');
        state.otherStyleActive = false;
    }
    if (state.dailyGoal) {
        const map  = ['5min','10min','15min','25min'];
        const i    = map.indexOf(state.dailyGoal);
        const btns = document.querySelectorAll('#step4 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    }
    if (state.levelOption) {
        const cards = document.querySelectorAll('#step5 .level-card');
        if (state.levelOption === 'known'   && cards[0]) cards[0].classList.add('selected');
        if (state.levelOption === 'unknown' && cards[1]) cards[1].classList.add('selected');
    }
    if (state.cefrLevel) {
        document.querySelectorAll('#step6 .cefr-card-full').forEach(c => {
            if (c.getAttribute('data-level') === state.cefrLevel) c.classList.add('selected');
        });
    }
}