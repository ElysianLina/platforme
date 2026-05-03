// ============================================================
// speaking.js — VERSION CORRIGÉE
//
// BUG CORRIGÉ : la page restait bloquée sur "Loading exercise..."
// quand learner_id était présent en localStorage.
//
// CAUSE : checkExistingResult() faisait un 2ème fetch de l'exercice
//         inutile, et le hide('loading-state') / show('exercise-container')
//         n'était pas toujours appelé.
//
// FIX   : 1 seul fetch pour l'exercice → TOUJOURS affiché.
//         fetchExistingResult() ne fait qu'un seul appel API de
//         vérification APRÈS que l'UI est déjà visible.
// ============================================================

const API_BASE = 'http://localhost:8000';

let state = {
    exerciseId:        null,
    sentenceWords:     [],
    referenceAudioUrl: null,
    learnerId:         null,
    subunitId:         null,
    subunit:           null,
    title:             null,
    mediaRecorder:     null,
    audioChunks:       [],
    isRecording:       false,
    timerInterval:     null,
    timerSeconds:      0,
    isCompleted:       false,
};

const $ = id => document.getElementById(id);
function show(id) { $(id)?.classList.remove('hidden'); }
function hide(id) { $(id)?.classList.add('hidden');    }

function getUrlParams() {
    const p = new URLSearchParams(window.location.search);
    return {
        subunit:   p.get('subunit')    || 'A1.1',
        title:     p.get('title')      || 'Speaking',
        subunitId: p.get('subunit_id') || null,
    };
}

// ══════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    const { subunit, title, subunitId } = getUrlParams();
    state.learnerId = localStorage.getItem('learner_id');
    state.subunitId = subunitId;
    state.subunit   = subunit;
    state.title     = title;

    // Header
    $('subunit-code').textContent  = subunit;
    $('subunit-title').textContent = title;

    // Sidebar
    const name  = localStorage.getItem('learner_name');
    const level = localStorage.getItem('learner_level') || 'A1';
    if (name)  $('sidebar-name').textContent  = name;
    if (level) $('sidebar-level').textContent = level;

    // Back button
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
        backBtn.href = `/exercise-menu/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
    }

    if (!subunitId) {
        showError('No sub-unit ID provided in URL.');
        return;
    }

    await init(subunitId);
});

// ══════════════════════════════════════════════════════════════
// INIT — flux séquentiel clair, sans imbrication
// ══════════════════════════════════════════════════════════════
async function init(subunitId) {

    // ── ÉTAPE 1 : charger l'exercice ──────────────────────────
    let exercise;
    try {
        const res  = await fetch(`${API_BASE}/api/speaking-exercise/?subunit_id=${subunitId}`);
        const data = await res.json();

        if (!data.success) {
            showError(data.error || 'Exercise not found for this sub-unit.');
            return;
        }
        exercise = data.exercise;

    } catch (err) {
        console.error('Fetch exercise failed:', err);
        showError('Network error. Please check your connection.');
        return;
    }

    // ── ÉTAPE 2 : peupler l'UI ────────────────────────────────
    state.exerciseId        = exercise.id;
    state.sentenceWords     = exercise.sentence_words;
    state.referenceAudioUrl = `${API_BASE}${exercise.audio_url}`;

    $('instruction-text').textContent = exercise.instructions;
    $('sentence-display').textContent = exercise.sentence;
    $('reference-audio').src          = state.referenceAudioUrl;

    // ── ÉTAPE 3 : rendre l'UI visible (TOUJOURS, peu importe la suite) ──
    hide('loading-state');
    show('exercise-container');

    // ── ÉTAPE 4 : vérifier résultat existant (learner connecté) ──
    if (state.learnerId) {
        const existing = await fetchExistingResult(subunitId, state.learnerId);
        if (existing) {
            // Déjà fait → afficher le résultat précédent, bloquer micro
            showCompleted(existing);
            return;
        }
    }

    // ── ÉTAPE 5 : pas encore fait → mode exercice interactif ──
    show('record-card');
    bindRecordButton();
}

// ══════════════════════════════════════════════════════════════
// FETCH EXISTING RESULT
// Retourne les données du résultat ou null si pas encore fait.
// En cas d'erreur réseau → retourne null (non bloquant).
// ══════════════════════════════════════════════════════════════
async function fetchExistingResult(subunitId, learnerId) {
    try {
        const res  = await fetch(
            `${API_BASE}/api/check-speaking-result/?subunit_id=${subunitId}&learner_id=${learnerId}`
        );
        const data = await res.json();

        if (data.success && data.has_result) {
            return data;
        }
    } catch (err) {
        // Erreur réseau non bloquante : l'apprenant peut quand même faire l'exercice
        console.warn('check-speaking-result failed (non-blocking):', err);
    }
    return null;
}

// ══════════════════════════════════════════════════════════════
// MODE "DÉJÀ COMPLÉTÉ"
// ══════════════════════════════════════════════════════════════
function showCompleted(data) {
    state.isCompleted = true;
    hide('record-card');
    hide('instruction-card');
    show('completed-card');
    renderResult(data, false);

    // ✅ Toujours afficher le bouton "Add another exercise"
    show('btn-add-exercise');
    bindAddExerciseButton();

    bindListenButton();
}



// ══════════════════════════════════════════════════════════════
// BOUTON "ADD ANOTHER EXERCISE"
// ══════════════════════════════════════════════════════════════
function bindAddExerciseButton() {
    const btn = $('btn-add-exercise');
    if (!btn) return;
 
    // Cloner pour éviter les doublons d'event listener
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
 
    clone.addEventListener('click', handleAddExercise);
}
 
async function handleAddExercise() {
    const btn = $('btn-add-exercise');
    if (!btn) return;

    btn.disabled    = true;
    btn.innerHTML   = '<i class="fas fa-spinner fa-spin"></i> Loading…';

    try {
        // 1. Vérifier si déjà généré
        const checkRes = await fetch(
            `${API_BASE}/api/check-generated-speaking-exists/?exercise_id=${state.exerciseId}&learner_id=${state.learnerId}`
        );
        const checkData = await checkRes.json();

        // 2. Si déjà généré → rediriger vers l'existant
        if (checkData.success && checkData.has_generated) {
            const genExerciseId = checkData.generated_exercise_id;
            const params = new URLSearchParams({
                gen_exercise_id:      genExerciseId,
                subunit:              state.subunit  || 'A1.1',
                title:                state.title    || 'Speaking',
                subunit_id:           state.subunitId || '',
                original_exercise_id: state.exerciseId,
            });
            window.location.href = `/speaking/generated/?${params.toString()}`;
            return;
        }

        // 3. Sinon → générer un nouvel exercice
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…';

        const res = await fetch(`${API_BASE}/api/generate-speaking-exercise/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                exercise_id: state.exerciseId,
                learner_id:  state.learnerId ? parseInt(state.learnerId) : null,
            }),
        });

        const data = await res.json();

        if (!data.success) {
            btn.disabled  = false;
            btn.innerHTML = '<i class="fas fa-plus"></i> Add another exercise';
            alert('Generation failed: ' + (data.error || 'Unknown error'));
            return;
        }

        // Rediriger vers le nouvel exercice généré
        const genExercise = data.generated_exercise;
        const params = new URLSearchParams({
            gen_exercise_id:      genExercise.id,
            subunit:              state.subunit  || 'A1.1',
            title:                state.title    || 'Speaking',
            subunit_id:           state.subunitId || '',
            original_exercise_id: state.exerciseId,
        });

        window.location.href = `/speaking/generated/?${params.toString()}`;

    } catch (err) {
        console.error('Add exercise error:', err);
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-plus"></i> Add another exercise';
        alert('Network error. Please try again.');
    }
}
// ══════════════════════════════════════════════════════════════
// RECORDING
// ══════════════════════════════════════════════════════════════
function bindRecordButton() {
    const micBtn = $('mic-btn');
    if (!micBtn) return;

    micBtn.addEventListener('click', async () => {
        if (state.isCompleted) return;
        if (!state.isRecording) await startRecording();
        else stopRecording();
    });

    $('btn-listen')?.addEventListener('click', playReference);
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.audioChunks   = [];
        state.mediaRecorder = new MediaRecorder(stream, { mimeType: getBestMimeType() });

        state.mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) state.audioChunks.push(e.data);
        };
        state.mediaRecorder.onstop = () => {
            stream.getTracks().forEach(t => t.stop());
            submitRecording();
        };

        state.mediaRecorder.start(100);
        state.isRecording = true;
        setRecordingUI(true);
        startTimer();

    } catch (err) {
        console.error('getUserMedia error:', err);
        setStatus('error', '⚠️ Microphone access denied. Please allow mic access in browser settings.');
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        stopTimer();
        setRecordingUI(false);
        setStatus('done', 'Processing your recording…');
        $('mic-btn').disabled = true;
    }
}

function getBestMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
    ];
    return types.find(t => MediaRecorder.isTypeSupported(t)) || '';
}

// ══════════════════════════════════════════════════════════════
// SUBMIT RECORDING
// ══════════════════════════════════════════════════════════════
async function submitRecording() {
    if (state.isCompleted) return;

    try {
        const mimeType  = state.mediaRecorder.mimeType || 'audio/webm';
        const extension = mimeType.includes('mp4') ? 'mp4'
                        : mimeType.includes('ogg') ? 'ogg'
                        : 'webm';

        const blob     = new Blob(state.audioChunks, { type: mimeType });
        const formData = new FormData();
        formData.append('exercise_id', state.exerciseId);
        formData.append('audio', blob, `recording.${extension}`);
        if (state.learnerId) formData.append('learner_id', state.learnerId);

        setStatus('done', 'Analysing pronunciation…');

        const res  = await fetch(`${API_BASE}/api/submit-speaking/`, {
            method: 'POST',
            body:   formData,
        });
        const data = await res.json();

        if (!data.success) {
            setStatus('error', `Error: ${data.error}`);
            $('mic-btn').disabled = false;
            return;
        }

        state.isCompleted = true;
        hide('record-card');
        renderResult(data, true);   // true = avec animation
        bindListenButton();
        bindAddExerciseButton();
    } catch (err) {
        console.error('Submit error:', err);
        setStatus('error', 'Submission failed. Please try again.');
        $('mic-btn').disabled = false;
    }
}

// ══════════════════════════════════════════════════════════════
// RENDER RESULT — unique fonction pour les 2 cas (nouveau + existant)
// ══════════════════════════════════════════════════════════════
function renderResult(data, animate) {
    const {
        transcript,
        word_results,
        correct_words,
        total_words,
        accuracy_score,
        feedback,
        attempt_number,
        submitted_at,
    } = data;

    const score  = accuracy_score || 0;
    const ringEl = $('ring-fill');
    const offset = 327 - (score / 100) * 327;

    // Score
    $('score-value').textContent   = score;
    $('correct-count').textContent = correct_words || 0;
    $('total-count').textContent   = total_words   || 0;

    // Ring
    ringEl.classList.remove('excellent', 'poor');
    if (animate) {
        setTimeout(() => {
            ringEl.style.strokeDashoffset = offset;
            if (score >= 80) ringEl.classList.add('excellent');
            if (score < 50)  ringEl.classList.add('poor');
        }, 100);
    } else {
        // Désactiver la transition CSS pour l'affichage immédiat
        ringEl.style.transition       = 'none';
        ringEl.style.strokeDashoffset = offset;
        if (score >= 80) ringEl.classList.add('excellent');
        if (score < 50)  ringEl.classList.add('poor');
        requestAnimationFrame(() => { ringEl.style.transition = ''; });
    }

    // Feedback badge
    const feedbackLabels = {
        excellent:  '🌟 Excellent!',
        very_good:  '👍 Very Good!',
        good:       '😊 Good Job!',
        keep_going: '💪 Keep Going!',
        try_again:  '🔄 Try Again!',
    };
    const badgeEl       = $('feedback-badge');
    badgeEl.textContent = feedbackLabels[feedback] || '😊 Good Job!';
    badgeEl.className   = `feedback-badge ${feedback || 'good'}`;

    // Transcript
    $('transcript-text').textContent = transcript || '(no speech detected)';

    // Word chips
    const container = $('words-display');
    container.innerHTML = '';
    if (word_results && word_results.length > 0) {
        word_results.forEach(wr => buildWordChip(wr, container));
    } else {
        container.innerHTML = '<span style="color:#aaa;font-size:14px">No word analysis available.</span>';
    }

    // Reference audio
    $('reference-audio').src = state.referenceAudioUrl;
    show('ref-audio-section');

    // Attempt / date info
    if (submitted_at) {
        const date = new Date(submitted_at).toLocaleDateString('en-GB');
        $('attempt-info').textContent = `Completed on ${date}`;
    } else if (attempt_number) {
        $('attempt-info').textContent = `Attempt #${attempt_number}`;
    }
    
    
    // Show result card
    show('result-card');

    if (animate) {
        setTimeout(() => {
            $('result-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 200);
    }
}

// ══════════════════════════════════════════════════════════════
// WORD CHIP BUILDER
// ══════════════════════════════════════════════════════════════
function buildWordChip(wr, container) {
    const chip     = document.createElement('div');
    chip.className = `word-chip ${wr.status}`;

    // Mot de référence
    const wordSpan       = document.createElement('span');
    wordSpan.textContent = wr.word;
    chip.appendChild(wordSpan);

    // Ce qui a été dit (pour les mots "wrong")
    if (wr.status === 'wrong' && wr.said) {
        const saidSpan       = document.createElement('span');
        saidSpan.className   = 'said-word';
        saidSpan.textContent = `"${wr.said}"`;
        chip.appendChild(saidSpan);
    }

    const tips = {
        correct: 'Correct!',
        wrong:   wr.said ? `You said "${wr.said}"` : 'Mispronounced',
        missing: 'Not pronounced',
        extra:   'Extra word (not in the sentence)',
    };
    chip.title = tips[wr.status] || '';

    container.appendChild(chip);
}

// ══════════════════════════════════════════════════════════════
// AUDIO REFERENCE
// ══════════════════════════════════════════════════════════════
function playReference() {
    const audio = $('reference-audio');
    show('ref-audio-section');
    audio.load();
    audio.play().catch(e => console.error('Audio play error:', e));
}

function bindListenButton() {
    const btn = $('btn-listen');
    if (!btn) return;
    // Cloner pour supprimer les anciens event listeners
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
    clone.addEventListener('click', playReference);
}

// ══════════════════════════════════════════════════════════════
// UI HELPERS
// ══════════════════════════════════════════════════════════════
function setRecordingUI(isRecording) {
    const micBtn  = $('mic-btn');
    const micIcon = $('mic-icon');
    const hint    = $('record-hint');

    if (isRecording) {
        micBtn.classList.add('active');
        micIcon.className = 'fas fa-stop';
        hint.textContent  = 'Click to stop recording';
        setStatus('recording', 'Recording… Read the sentence clearly');
        show('record-timer');
    } else {
        micBtn.classList.remove('active');
        micBtn.classList.add('done');
        micIcon.className = 'fas fa-check';
        hint.textContent  = '';
        hide('record-timer');
    }
}

function setStatus(stateName, message) {
    const dot  = $('status-dot');
    const text = $('status-text');
    if (dot)  dot.className    = `status-dot ${stateName}`;
    if (text) text.textContent = message;
}

function startTimer() {
    state.timerSeconds = 0;
    updateTimerDisplay();
    state.timerInterval = setInterval(() => {
        state.timerSeconds++;
        updateTimerDisplay();
        if (state.timerSeconds >= 30) stopRecording();   // auto-stop à 30s
    }, 1000);
}

function stopTimer() { clearInterval(state.timerInterval); }

function updateTimerDisplay() {
    const m = Math.floor(state.timerSeconds / 60);
    const s = state.timerSeconds % 60;
    $('timer-display').textContent = `${m}:${String(s).padStart(2, '0')}`;
}

function showError(message) {
    hide('loading-state');
    const el = $('error-message');
    if (el) el.textContent = message;
    show('error-state');
}