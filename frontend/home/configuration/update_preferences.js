const API_BASE = 'http://localhost:8000';

const state = {
    currentStep: 1,
    totalSteps: 4,
    reason: '',
    interests: [],
    otherInterest: '',
    learningStyle: '',
    otherLearningStyle: '',
    dailyGoal: '',
    userName: 'User',
    otherInterestActive: false,
    otherStyleActive: false,
    learnerId: null
};

// ── Récupérer learner_id ─────────────────────────────────────
function getLearnerId() {
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('learner_id');

    if (idFromUrl && idFromUrl !== 'null' && idFromUrl.trim() !== '') {
        state.learnerId = idFromUrl;
        localStorage.setItem('learner_id', idFromUrl);
        window.history.replaceState({}, document.title, window.location.pathname);
        console.log('✅ learner_id from URL:', state.learnerId);
        return state.learnerId;
    }

    const storedId = localStorage.getItem('learner_id');
    if (storedId && storedId !== 'null') {
        state.learnerId = storedId;
        console.log('✅ learner_id from localStorage:', state.learnerId);
        return state.learnerId;
    }

    console.warn('⚠️ No learner_id — redirecting to login');
    window.location.href = `${API_BASE}/login/`;
    return null;
}

// ── Charger les préférences existantes ───────────────────────
async function loadExistingPreferences() {
    if (!state.learnerId) return;

    try {
        const response = await fetch(`${API_BASE}/api/preferences/?learner_id=${state.learnerId}`);
        const data = await response.json();

        if (!data.success || !data.preferences) {
            console.log('ℹ️ No existing preferences');
            return;
        }

        const p = data.preferences;

        if (p.reason) state.reason = p.reason;
        if (p.interests && p.interests.length > 0) state.interests = [...p.interests];
        if (p.other_interest) {
            state.otherInterest = p.other_interest;
            state.otherInterestActive = true;
        }
        if (p.learning_style) state.learningStyle = p.learning_style;
        if (p.other_style) {
            state.otherLearningStyle = p.other_style;
            state.otherStyleActive = true;
        }
        if (p.daily_goal) state.dailyGoal = p.daily_goal;

        console.log('✅ Existing preferences loaded:', p);

    } catch (err) {
        console.error('❌ Error loading preferences:', err);
    }
}

// ── Initialisation ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    console.log('=== update_preferences.js loaded ===');

    getLearnerId();
    await loadExistingPreferences();

    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = state.userName.split(' ')[0] || 'User';
    }

    updateUI();
    restoreSelections();

    document.addEventListener('click', handleGlobalClick);
});

function handleGlobalClick(event) {
    if (state.currentStep === 2 && state.otherInterestActive) {
        const container = document.getElementById('otherInterestContainer');
        const input = document.getElementById('otherInterestText');
        if (container && !container.contains(event.target) && input.value.trim() === '') closeOtherInterest();
    }
    if (state.currentStep === 3 && state.otherStyleActive) {
        const container = document.getElementById('otherStyleContainer');
        const input = document.getElementById('otherStyleText');
        if (container && !container.contains(event.target) && input.value.trim() === '') closeOtherStyle();
    }
}

// ── Navigation ───────────────────────────────────────────────
function goBack() {
    if (state.currentStep > 1) {
        state.currentStep--;
        updateUI();
    } else {
        window.location.href = '/configuration/';
    }
}

async function handleNext() {
    console.log('handleNext — step:', state.currentStep,
        '| reason:', state.reason,
        '| interests:', state.interests,
        '| learningStyle:', state.learningStyle,
        '| dailyGoal:', state.dailyGoal);

    if (state.currentStep < state.totalSteps) {
        state.currentStep++;
        updateUI();
    } else {
        await finishUpdate();
    }
}

function updateUI() {
    const progress = (state.currentStep / state.totalSteps) * 100;
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = `${progress}%`;

    const backBtn = document.getElementById('backBtn');
    if (backBtn) backBtn.classList.add('visible');

    document.querySelectorAll('.step').forEach((step, i) => {
        step.classList.toggle('active', i + 1 === state.currentStep);
    });

    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) nextBtn.textContent = state.currentStep === state.totalSteps ? 'Save Changes' : 'Continue';

    const display = document.getElementById('currentStepDisplay');
    if (display) display.textContent = state.currentStep;

    checkCanProceed();
}

function checkCanProceed() {
    const nextBtn = document.getElementById('nextBtn');
    let can = false;
    switch (state.currentStep) {
        case 1: can = state.reason !== ''; break;
        case 2: can = state.interests.length > 0 || state.otherInterest.trim() !== ''; break;
        case 3: can = state.learningStyle === 'autre' ? state.otherLearningStyle.trim() !== '' : state.learningStyle !== ''; break;
        case 4: can = state.dailyGoal !== ''; break;
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
    else { state.interests.push(interest); btn.classList.add('selected'); }
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
    state.otherInterest = '';
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
    state.learningStyle = 'autre';
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
    state.learningStyle = '';
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

// ── Sauvegarde (PAS de cefr_level) ──────────────────────────
async function finishUpdate() {
    console.log('🏁 finishUpdate — state:', {
        learnerId: state.learnerId,
        reason: state.reason,
        interests: state.interests,
        learningStyle: state.learningStyle,
        dailyGoal: state.dailyGoal,
    });

    if (!state.learnerId) {
        alert('You must be logged in.');
        return;
    }

    let interestsToSave = [...state.interests];
    if (state.otherInterest.trim()) {
        interestsToSave = ["autre"];
    }

    const payload = {
        learner_id: state.learnerId,
        reason: state.reason,
        interests: interestsToSave,
        other_interest: state.otherInterest.trim(),
        learning_style: state.learningStyle === 'autre' ? 'autre' : state.learningStyle,
        other_style: state.otherLearningStyle.trim(),
        daily_goal: state.dailyGoal,
        // ❌ PAS de cefr_level — on ne touche pas au niveau
    };
    console.log('📤 update_preferences payload:', payload);

    try {
        const response = await fetch(`${API_BASE}/api/save-preferences/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            alert('Preferences updated successfully!');
            window.location.href = '/configuration/';
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('❌ Error savePreferences:', err);
        alert('Network error, please try again.');
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
        if (state.otherStyleActive) closeOtherStyle();
    }
});

// ── Restore selections ───────────────────────────────────────
function restoreSelections() {
    if (state.reason) {
        const map = ['voyage','travail','etudes','culture','communication','Défi personnel'];
        const i = map.indexOf(state.reason);
        const cards = document.querySelectorAll('#step1 .option-card');
        if (i > -1 && cards[i]) cards[i].classList.add('selected');
    }
    state.interests.forEach(interest => {
        const map = ['voyage-tourisme','business','cinema','musique','sport'];
        const i = map.indexOf(interest);
        const btns = document.querySelectorAll('#step2 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    });
    const oiBtn = document.getElementById('otherInterestBtn');
    const oiInp = document.getElementById('otherInterestInput');
    const oiText = document.getElementById('otherInterestText');
    if (state.otherInterestActive || state.otherInterest.trim() !== '') {
        if (oiBtn) oiBtn.classList.add('hidden');
        if (oiInp) oiInp.classList.remove('hidden');
        if (oiText) oiText.value = state.otherInterest;
        state.otherInterestActive = true;
    } else {
        if (oiBtn) oiBtn.classList.remove('hidden');
        if (oiInp) oiInp.classList.add('hidden');
        state.otherInterestActive = false;
    }
    if (state.learningStyle && state.learningStyle !== 'autre') {
        const map = ['video','texte','audio'];
        const i = map.indexOf(state.learningStyle);
        const btns = document.querySelectorAll('#step3 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    }
    const osBtn = document.getElementById('otherStyleBtn');
    const osInp = document.getElementById('otherStyleInput');
    const osText = document.getElementById('otherStyleText');
    if (state.otherStyleActive || (state.learningStyle === 'autre' && state.otherLearningStyle.trim() !== '')) {
        if (osBtn) osBtn.classList.add('hidden');
        if (osInp) osInp.classList.remove('hidden');
        if (osText) osText.value = state.otherLearningStyle;
        state.otherStyleActive = true;
    } else {
        if (osBtn) osBtn.classList.remove('hidden');
        if (osInp) osInp.classList.add('hidden');
        state.otherStyleActive = false;
    }
    if (state.dailyGoal) {
        const map = ['5min','10min','15min','25min'];
        const i = map.indexOf(state.dailyGoal);
        const btns = document.querySelectorAll('#step4 .option-row');
        if (i > -1 && btns[i]) btns[i].classList.add('selected');
    }
}