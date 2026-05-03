// ============================================================
// generate_speaking.js
//
// Page : /speaking/generated/
// Paramètres URL attendus :
//   gen_exercise_id      ← ID du GeneratedSpeakingExercise (déjà créé)
//   subunit              ← ex: A1.1
//   title                ← ex: Morning Customs
//   subunit_id           ← ID du SubUnit
//   original_exercise_id ← ID du SpeakingExercise original
//
// Flux :
//   1. Récupérer gen_exercise depuis l'API (via gen_exercise_id)
//   2. Afficher la phrase générée
//   3. L'apprenant enregistre → POST /api/submit-generated-speaking/
//   4. Afficher le résultat (même logique que speaking.js)
//   5. Bouton "Generate another" → POST /api/generate-speaking-exercise/
//      puis reload avec le nouveau gen_exercise_id
// ============================================================

const API_BASE = 'http://localhost:8000';

let state = {
    genExerciseId:       null,
    originalExerciseId:  null,
    sentenceWords:       [],
    referenceAudioUrl:   null,
    learnerId:           null,
    subunitId:           null,
    subunit:             null,
    title:               null,
    sentence:            null,
    theme:               null,
    level:               null,
    instructions:        null,
    mediaRecorder:       null,
    audioChunks:         [],
    isRecording:         false,
    timerInterval:       null,
    timerSeconds:        0,
    isCompleted:         false,
};

const $ = id => document.getElementById(id);
function show(id) { $(id)?.classList.remove('hidden'); }
function hide(id) { $(id)?.classList.add('hidden');    }

function getUrlParams() {
    const p = new URLSearchParams(window.location.search);
    return {
        genExerciseId:      p.get('gen_exercise_id')      || null,
        subunit:            p.get('subunit')              || 'A1.1',
        title:              p.get('title')                || 'Speaking',
        subunitId:          p.get('subunit_id')           || null,
        originalExerciseId: p.get('original_exercise_id') || null,
    };
}

// ══════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    const { genExerciseId, subunit, title, subunitId, originalExerciseId } = getUrlParams();

    state.learnerId          = localStorage.getItem('learner_id');
    state.genExerciseId      = genExerciseId;
    state.originalExerciseId = originalExerciseId;
    state.subunitId          = subunitId;
    state.subunit            = subunit;
    state.title              = title;

    // Header
    $('subunit-code').textContent  = subunit;
    $('subunit-title').textContent = title + ' — AI Exercise';

    // Sidebar
    const name  = localStorage.getItem('learner_name');
    const level = localStorage.getItem('learner_level') || 'A1';
    if (name)  $('sidebar-name').textContent  = name;
    if (level) $('sidebar-level').textContent = level;

    // Back button → retour à la page speaking originale
    const backBtn = $('back-btn');
    if (backBtn) {
        backBtn.href = `/speaking/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
    }

    // Error back button
    const errBack = $('error-back-btn');
    if (errBack) {
        errBack.href = `/speaking/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
    }

    if (!genExerciseId) {
        showError('No generated exercise ID provided in URL.');
        return;
    }

    await init(genExerciseId);
});

// ══════════════════════════════════════════════════════════════
// INIT — charge l'exercice généré depuis l'API
// ══════════════════════════════════════════════════════════════
async function init(genExerciseId) {

    // ── Récupérer les données de l'exercice généré ────────────
    let exercise;
    try {
        const res  = await fetch(
            `${API_BASE}/api/get-generated-speaking-exercise/?gen_exercise_id=${genExerciseId}`
        );
        const data = await res.json();

        if (!data.success) {
            showError(data.error || 'Generated exercise not found.');
            return;
        }
        exercise = data.exercise;

    } catch (err) {
        console.error('Fetch generated exercise failed:', err);
        showError('Network error. Please check your connection.');
        return;
    }

    // ── Peupler le state ──────────────────────────────────────
    state.sentence           = exercise.sentence;
    state.sentenceWords      = exercise.sentence_words;
    state.theme              = exercise.theme;
    state.level              = exercise.level;
    state.instructions       = exercise.instructions;
    state.referenceAudioUrl  = `${API_BASE}${exercise.reference_audio_url}`;

    // ── Peupler l'UI ──────────────────────────────────────────
    $('instruction-text').textContent = exercise.instructions;
    $('sentence-display').textContent = exercise.sentence;
    $('reference-audio').src          = state.referenceAudioUrl;

    if (exercise.theme) {
        const themeBadge = $('theme-badge');
        themeBadge.textContent = '🏷️ ' + exercise.theme;
        themeBadge.style.display = 'inline-flex';
    }

    // ── Rendre l'UI visible ───────────────────────────────────
    hide('loading-state');
    show('exercise-container');

    // ── Vérifier si déjà soumis ───────────────────────────────
    if (state.learnerId) {
        const existing = await fetchExistingResult(genExerciseId, state.learnerId);
        if (existing) {
            showCompleted(existing);
            return;
        }
    }

    // ── Mode interactif ───────────────────────────────────────
    show('record-card');
    bindRecordButton();
}

// ══════════════════════════════════════════════════════════════
// FETCH EXISTING RESULT
// ══════════════════════════════════════════════════════════════
async function fetchExistingResult(genExerciseId, learnerId) {
    try {
        const res  = await fetch(
            `${API_BASE}/api/check-generated-speaking-result/?gen_exercise_id=${genExerciseId}&learner_id=${learnerId}`
        );
        const data = await res.json();

        if (data.success && data.has_result) {
            return data;
        }
    } catch (err) {
        console.warn('check-generated-speaking-result failed (non-blocking):', err);
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
    renderResult(data, false);
    bindListenButton();
    
    bindBackOriginalButton();
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
        formData.append('generated_exercise_id', state.genExerciseId);
        formData.append('audio', blob, `recording.${extension}`);
        if (state.learnerId) formData.append('learner_id', state.learnerId);

        setStatus('done', 'Analysing pronunciation…');

        const res  = await fetch(`${API_BASE}/api/submit-generated-speaking/`, {
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
        renderResult(data, true);
        bindListenButton();       
        bindBackOriginalButton();

    } catch (err) {
        console.error('Submit error:', err);
        setStatus('error', 'Submission failed. Please try again.');
        $('mic-btn').disabled = false;
    }
}
async function handleGenerateAnother() {
    const btn = $('btn-generate-another');
    if (!btn) return;

    btn.disabled  = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…';

    try {
        const res = await fetch(`${API_BASE}/api/generate-speaking-exercise/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                exercise_id: parseInt(state.originalExerciseId),
                learner_id:  state.learnerId ? parseInt(state.learnerId) : null,
            }),
        });

        const data = await res.json();

        if (!data.success) {
            btn.disabled  = false;
            btn.innerHTML = '<i class="fas fa-robot"></i> Generate another';
            alert('Generation failed: ' + (data.error || 'Unknown error'));
            return;
        }

        // Reload la page avec le nouvel exercice généré
        const genExercise = data.generated_exercise;
        const params = new URLSearchParams({
            gen_exercise_id:      genExercise.id,
            subunit:              state.subunit             || 'A1.1',
            title:                state.title               || 'Speaking',
            subunit_id:           state.subunitId           || '',
            original_exercise_id: state.originalExerciseId  || '',
        });

        window.location.href = `/speaking/generated/?${params.toString()}`;

    } catch (err) {
        console.error('Generate another error:', err);
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-robot"></i> Generate another';
        alert('Network error. Please try again.');
    }
}

// ══════════════════════════════════════════════════════════════
// BOUTON "BACK TO ORIGINAL"
// ══════════════════════════════════════════════════════════════
function bindBackOriginalButton() {
    const btn = $('btn-back-original');
    if (!btn) return;

    btn.href = `/speaking/?subunit=${state.subunit}&title=${encodeURIComponent(state.title)}&subunit_id=${state.subunitId}`;
}

// ══════════════════════════════════════════════════════════════
// RENDER RESULT
// ══════════════════════════════════════════════════════════════
function renderResult(data, animate) {
    const {
        transcript,
        word_results,
        correct_words,
        total_words,
        accuracy_score,
        feedback,
        submitted_at,
        reference_audio_url,
    } = data;

    const score  = accuracy_score || 0;
    const ringEl = $('ring-fill');
    const offset = 327 - (score / 100) * 327;

    $('score-value').textContent   = score;
    $('correct-count').textContent = correct_words || 0;
    $('total-count').textContent   = total_words   || 0;

    ringEl.classList.remove('excellent', 'poor');
    if (animate) {
        setTimeout(() => {
            ringEl.style.strokeDashoffset = offset;
            if (score >= 80) ringEl.classList.add('excellent');
            if (score < 50)  ringEl.classList.add('poor');
        }, 100);
    } else {
        ringEl.style.transition       = 'none';
        ringEl.style.strokeDashoffset = offset;
        if (score >= 80) ringEl.classList.add('excellent');
        if (score < 50)  ringEl.classList.add('poor');
        requestAnimationFrame(() => { ringEl.style.transition = ''; });
    }

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

    $('transcript-text').textContent = transcript || '(no speech detected)';

    const container = $('words-display');
    container.innerHTML = '';
    if (word_results && word_results.length > 0) {
        word_results.forEach(wr => buildWordChip(wr, container));
    } else {
        container.innerHTML = '<span style="color:#aaa;font-size:14px">No word analysis available.</span>';
    }

    // Mettre à jour l'audio de référence si retourné par l'API
    if (reference_audio_url) {
        state.referenceAudioUrl = `${API_BASE}${reference_audio_url}`;
        $('reference-audio').src = state.referenceAudioUrl;
    }
    show('ref-audio-section');

    if (submitted_at) {
        const date = new Date(submitted_at).toLocaleDateString('en-GB');
        $('attempt-info').textContent = `Completed on ${date}`;
    }

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

    const wordSpan       = document.createElement('span');
    wordSpan.textContent = wr.word;
    chip.appendChild(wordSpan);

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
        if (listenBeforeBtn) listenBeforeBtn.style.display = 'none';
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
        if (state.timerSeconds >= 30) stopRecording();
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
    hide('ai-banner');
    const el = $('error-message');
    if (el) el.textContent = message;
    show('error-state');
}