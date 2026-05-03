/**
 * exercise_2.js — Word Order in English
 * Same pattern as exercise_1.js — fetches exercises from API,
 * renders 10 questions, submits answers, shows detailed results.
 */

const COURSE_ID = 'grammar_a1_word_order';

let exercises     = [];
let answers       = {};
let totalQ        = 0;
let answeredCount = 0;
let submitted     = false;

document.addEventListener('DOMContentLoaded', () => {
    initDropdown();
    loadUserData();
    loadExercises();
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(str) {
    return String(str || '')
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function getCookie(name) {
    for (const c of document.cookie.split(';')) {
        const [k,v] = c.trim().split('=');
        if (k === name) return decodeURIComponent(v);
    }
    return null;
}
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val || '';
}
function hideEl(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}
function showError(msg) {
    document.getElementById('loading-state').innerHTML =
        `<i class="fas fa-exclamation-circle" style="font-size:2rem;color:#ef4444"></i><p>${msg}</p>`;
}

// ── Dropdown ──────────────────────────────────────────────────────────────────
function initDropdown() {
    const trigger  = document.getElementById('profile-trigger');
    const dropdown = document.getElementById('profile-dropdown');
    if (!trigger || !dropdown) return;

    trigger.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
    });
    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && !trigger.contains(e.target))
            dropdown.classList.remove('active');
    });

    const logoutBtn = document.querySelector('[data-action="logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async e => {
            e.preventDefault();
            await fetch('/api/logout/', {
                method : 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            localStorage.clear();
            window.location.href = '/login/';
        });
    }
}

// ── Load user data ────────────────────────────────────────────────────────────
async function loadUserData() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) return;
    try {
        const res  = await fetch(`/api/learner/?learner_id=${learnerId}`);
        const data = await res.json();
        if (!data.success || !data.learner) return;
        const l = data.learner;
        const initials = l.name ? l.name.slice(0,2).toUpperCase() : '--';

        setText('avatar-initials',          initials);
        setText('dropdown-avatar-initials', initials);
        setText('dropdown-name',            l.name  || '--');
        setText('dropdown-email',           l.email || '--');

        const badge = document.getElementById('level-badge');
        if (badge) badge.textContent = `CEFR Level: ${l.cefr_level || '--'}`;

        if (l.picture) {
            ['avatar-img','dropdown-avatar-img'].forEach(id => {
                const img = document.getElementById(id);
                if (img) { img.src = l.picture; img.style.display = 'block'; }
            });
            hideEl('avatar-initials');
            hideEl('dropdown-avatar-initials');
        }
    } catch (err) { console.error('loadUserData:', err); }
}

// ── Load exercises ────────────────────────────────────────────────────────────
async function loadExercises() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) { showError('Please log in to do this exercise.'); return; }

    try {
        const res  = await fetch(`/api/grammar-course/?course_id=${COURSE_ID}&learner_id=${learnerId}`);
        const data = await res.json();

        if (!data.success) { showError(data.error || 'Exercise not found.'); return; }

        // Already done — show locked results
        if (data.already_done) {
            const exSection = data.sections.find(s => s.section_type === 'exercise');
            if (exSection) exercises = exSection.content.exercises || [];
            totalQ = exercises.length;
            showExerciseWrapper();
            renderQuestions(true);
            showResults(data.score, data.total, data.feedback, data.results);
            return;
        }

        // Fresh attempt
        const exSection = data.sections.find(s => s.section_type === 'exercise');
        if (!exSection) { showError('Exercise section not found.'); return; }

        exercises = exSection.content.exercises || [];
        totalQ    = exercises.length;

        showExerciseWrapper();
        renderQuestions(false);
        initSubmitButton(learnerId);

    } catch (err) {
        console.error('loadExercises:', err);
        showError('Failed to load exercise. Please try again.');
    }
}

function showExerciseWrapper() {
    document.getElementById('loading-state').style.display    = 'none';
    document.getElementById('exercise-wrapper').style.display = 'block';
    setText('score-denom', `/${totalQ}`);
}

// ── Render questions ──────────────────────────────────────────────────────────
function renderQuestions(locked) {
    const body = document.getElementById('questions-body');
    body.innerHTML = '';

    exercises.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'q-card';
        card.id        = `q-card-${q.exercise_id}`;
        card.style.animationDelay = `${idx * 60}ms`;

        // label for sentence_building vs error_correction
        const typeLabel = q.type === 'sentence_building'
            ? 'Sentence Building'
            : 'Error Correction';

        card.innerHTML = `
            <div class="q-num">Question ${idx + 1} of ${totalQ}</div>
            <span class="q-type-badge">${typeLabel}</span>
            <div class="q-instruction">${esc(q.instruction)}</div>
            <div class="q-sentence">${esc(q.question)}</div>
            <textarea
                class="q-input"
                id="input-${q.exercise_id}"
                rows="2"
                placeholder="${q.type === 'sentence_building'
                    ? 'Write the sentence in the correct order…'
                    : 'Type the corrected sentence here…'}"
                ${locked ? 'disabled' : ''}
            ></textarea>
            <div class="q-feedback" id="feedback-${q.exercise_id}"></div>`;

        body.appendChild(card);

        if (!locked) {
            const input = card.querySelector(`#input-${q.exercise_id}`);
            input.addEventListener('input', () => onAnswerChange(q.exercise_id, input.value));
        }
    });
}

// ── Track answers ─────────────────────────────────────────────────────────────
function onAnswerChange(qid, value) {
    const wasFilled = answers[qid] && answers[qid].trim() !== '';
    answers[qid]    = value;
    const isFilled  = value.trim() !== '';

    if (isFilled  && !wasFilled) answeredCount++;
    if (!isFilled && wasFilled)  answeredCount--;

    const card = document.getElementById(`q-card-${qid}`);
    if (card) card.classList.toggle('answered', isFilled);

    const pct = totalQ > 0 ? Math.round((answeredCount / totalQ) * 100) : 0;
    document.getElementById('progress-fill').style.width = `${pct}%`;
    document.getElementById('progress-text').textContent  = `${answeredCount} / ${totalQ} answered`;

    const btn = document.getElementById('btn-submit');
    if (btn) btn.disabled = (answeredCount < totalQ);
}

// ── Submit ────────────────────────────────────────────────────────────────────
function initSubmitButton(learnerId) {
    const btn = document.getElementById('btn-submit');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        if (submitted) return;
        submitted    = true;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting…';

        try {
            const res = await fetch('/api/submit-grammar/', {
                method : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken' : getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    learner_id: learnerId,
                    course_id : COURSE_ID,
                    answers   : answers,
                })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Submission failed');

            // Lock inputs
            exercises.forEach(q => {
                const inp = document.getElementById(`input-${q.exercise_id}`);
                if (inp) inp.disabled = true;
            });

            document.getElementById('submit-area').style.display = 'none';
            showInlineFeedback(data.results);
            showResults(data.score, data.total, data.feedback, data.results);

        } catch (err) {
            console.error('submit:', err);
            submitted    = false;
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check-circle"></i> Submit My Answers';
            alert('Submission failed. Please try again.');
        }
    });
}

// ── Inline feedback per question ──────────────────────────────────────────────
function showInlineFeedback(results) {
    results.forEach(r => {
        const input    = document.getElementById(`input-${r.id}`);
        const feedback = document.getElementById(`feedback-${r.id}`);

        if (input)    input.classList.add(r.correct ? 'correct' : 'incorrect');
        if (feedback) {
            feedback.classList.add('show', r.correct ? 'ok' : 'ko');
            if (r.correct) {
                feedback.innerHTML = `<strong>✓ Correct!</strong>`;
            } else {
                feedback.innerHTML = `
                    <strong>✗ Incorrect</strong>
                    Correct answer: <em>${esc(r.correct_answer)}</em><br>
                    <span style="font-size:.82rem;opacity:.85">${esc(r.explanation)}</span>`;
            }
        }
    });
}

// ── Results panel ─────────────────────────────────────────────────────────────
function showResults(score, total, feedback, results) {
    const panel = document.getElementById('results-panel');
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

    setText('score-num',   score);
    setText('score-denom', `/${total}`);
    const circle = document.getElementById('score-circle');
    circle.className = `score-circle ${feedback || ''}`;

    const msgs = {
        excellent    : { title:'🎉 Excellent!',       msg:`You scored ${score}/${total}. Great understanding of English word order!` },
        good         : { title:'👍 Good Job!',         msg:`You scored ${score}/${total}. Review the questions you got wrong and keep practicing.` },
        needs_practice:{ title:'💪 Keep Practicing!', msg:`You scored ${score}/${total}. Review the lesson carefully and try again — you can do it!` },
    };
    const m = msgs[feedback] || msgs.good;
    setText('results-title', m.title);
    setText('results-msg',   m.msg);

    const detail = document.getElementById('results-detail');
    detail.innerHTML = '';

    results.forEach((r, idx) => {
        const origQ = exercises.find(e => String(e.exercise_id) === String(r.id));
        const item  = document.createElement('div');
        item.className = `rd-item ${r.correct ? 'rd-ok' : 'rd-ko'}`;
        item.innerHTML = `
            <span class="rd-icon">${r.correct ? '✓' : '✗'}</span>
            <div class="rd-num">Question ${idx + 1}</div>
            <div class="rd-q">${esc(origQ ? origQ.question : '')}</div>
            <div class="rd-given">Your answer: <em>${esc(r.given || '(no answer)')}</em></div>
            ${!r.correct ? `<div class="rd-correct">Correct: ${esc(r.correct_answer)}</div>` : ''}
            ${r.explanation ? `<div class="rd-explanation">${esc(r.explanation)}</div>` : ''}`;
        detail.appendChild(item);
    });
}