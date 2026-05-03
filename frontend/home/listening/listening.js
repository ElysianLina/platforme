// ============================================================
// listening.js
// Gère l'exercice de compréhension orale (Listening Comprehension)
// Pattern identique à comprehension-ecrite.js
// ============================================================

const API_BASE = 'http://localhost:8000';

// ── État global ──────────────────────────────────────────────
let state = {
    subunitId:    null,
    subunit:      null,
    title:        null,
    learnerId:    null,
    audioId:      null,
    questions:    [],
    answers:      {},       // { question_id: réponse_donnée }
    currentIndex: 0,
    hasListened:  false,
    submitted:    false,
    isRetrying:          false,   
    firstSubmissionData: null,
};

// ── Récupérer les paramètres URL ────────────────────────────
function getUrlParams() {
    const p = new URLSearchParams(window.location.search);
    return {
        subunit:   p.get('subunit')    || '1.1',
        title:     p.get('title')      || 'Listening',
        subunitId: p.get('subunit_id') || null,
    };
}

// ════════════════════════════════════════════════════════════
//  INIT
// ════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
    const params = getUrlParams();
    state.subunitId = params.subunitId;
    state.subunit   = params.subunit;
    state.title     = params.title;
    state.learnerId = localStorage.getItem('learner_id');

    // Mettre à jour le header
    document.getElementById('subunit-label').textContent = params.subunit;
    document.getElementById('subunit-title').textContent = params.title;

    // Bouton retour
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.href = `/exercise-menu/?subunit=${params.subunit}&title=${encodeURIComponent(params.title)}&subunit_id=${params.subunitId}`;
    }
    const errorBackBtn = document.getElementById('error-back-btn');
    if (errorBackBtn) errorBackBtn.href = backBtn?.href || '/';

    if (!state.subunitId) {
        showError('Missing sub-unit ID. Please go back and try again.');
        return;
    }

    // Charger l'exercice
    await loadExercise();
});

// ════════════════════════════════════════════════════════════
//  CHARGEMENT DE L'EXERCICE
// ════════════════════════════════════════════════════════════

// ════════════════════════════════════════════════════════════
//  CHARGEMENT DE L'EXERCICE
// ════════════════════════════════════════════════════════════

async function loadExercise() {
    showLoading(true);
    try {
        const res  = await fetch(`${API_BASE}/api/listening-exercise/?subunit_id=${state.subunitId}`);
        const data = await res.json();

        if (!data.success) {
            showError(data.error || 'No audio available for this sub-unit.');
            return;
        }

        // Stocker les données
        state.audioId   = data.audio.audio_id;
        state.questions = data.questions;

        if (data.audio.vocab_score !== null && data.audio.vocab_score !== undefined) {
            showVocabScore(data.audio.vocab_score);
        }

        // Vérifier si déjà soumis (résultat existant)
        if (state.learnerId) {
            const check = await fetch(
                `${API_BASE}/api/check-listening-result/?subunit_id=${state.subunitId}&learner_id=${state.learnerId}`
            );
            const checkData = await check.json();
            if (checkData.success && checkData.has_result) {
                // ✅ Construire l'objet data complet avec tous les champs nécessaires
                const resultData = {
                    score:         checkData.score,
                    correct_count: checkData.correct_count,
                    total:         checkData.total,
                    feedback:      checkData.feedback,
                    results:       checkData.results || [],  // ✅ Résultats détaillés du backend
                    already_done:  true,                        // ✅ Flag already_done
                };
                
                // ✅ Sauvegarder pour pouvoir réafficher via "Show Result"
                state.firstSubmissionData = resultData;
                state.isRetrying = false;  // Pas en mode retry au chargement initial
                
                showExerciseContent();
                setupAudioPlayer(data.audio);
                renderQuestions();
                showResult(resultData);  // ✅ Passer l'objet complet
                return;
            }
        }

        // Afficher l'exercice (première fois)
        showExerciseContent();
        setupAudioPlayer(data.audio);
        renderQuestions();

    } catch (err) {
        console.error('Error loading exercise:', err);
        showError('Failed to load the exercise. Please try again.');
    } finally {
        showLoading(false);
    }
}

function showVocabScore(score) {
    const badge = document.getElementById('vocab-score-badge');
    const value = document.getElementById('vocab-score-value');
    
    if (badge && value) {
        value.textContent = Math.round(score);
        badge.style.display = 'inline-flex';
    }
}

// ════════════════════════════════════════════════════════════
//  AUDIO PLAYER
// ════════════════════════════════════════════════════════════

function setupAudioPlayer(audioData) {
    const audioEl = document.getElementById('audio-element');
    audioEl.src   = `${API_BASE}${audioData.audio_url}`;

    document.getElementById('audio-subunit-title').textContent = audioData.subunit_title || 'Audio Clip';
    document.getElementById('audio-unit-title').textContent    = audioData.unit_title    || '';

    // ── Play / Pause ────────────────────────────────────────
    const btnPlay  = document.getElementById('btn-play');
    const playIcon = document.getElementById('play-icon');

    btnPlay.addEventListener('click', () => {
        if (audioEl.paused) {
            audioEl.play();
            playIcon.className = 'fas fa-pause';
        } else {
            audioEl.pause();
            playIcon.className = 'fas fa-play';
        }
    });

    // ── Fin de lecture ──────────────────────────────────────
    audioEl.addEventListener('ended', () => {
        playIcon.className = 'fas fa-play';
        state.hasListened  = true;
        document.getElementById('listen-hint').innerHTML =
            '<i class="fas fa-check-circle" style="color:#1D9E75"></i> Ready to answer!';
        // Activer le bouton "Next" si une réponse existe
        updateNavButtons();
    });

    // ── Progress bar ────────────────────────────────────────
    audioEl.addEventListener('timeupdate', () => {
        if (!audioEl.duration) return;
        const pct  = (audioEl.currentTime / audioEl.duration) * 100;
        document.getElementById('progress-fill').style.width = pct + '%';

        const cur = formatTime(audioEl.currentTime);
        const dur = formatTime(audioEl.duration);
        document.getElementById('time-display').textContent = `${cur} / ${dur}`;
    });

    // ── Seek (clic sur la barre) ────────────────────────────
    document.getElementById('progress-container').addEventListener('click', (e) => {
        if (!audioEl.duration) return;
        const rect = e.currentTarget.querySelector('.progress-track').getBoundingClientRect();
        const pct  = (e.clientX - rect.left) / rect.width;
        audioEl.currentTime = pct * audioEl.duration;
    });

    // ── Replay ──────────────────────────────────────────────
    document.getElementById('btn-replay').addEventListener('click', () => {
        audioEl.currentTime = 0;
        audioEl.play();
        playIcon.className = 'fas fa-pause';
    });

    // ── Vitesse ─────────────────────────────────────────────
    document.querySelectorAll('.btn-speed').forEach(btn => {
        btn.addEventListener('click', () => {
            const speed = parseFloat(btn.dataset.speed);
            audioEl.playbackRate = speed;
            document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
    // Vitesse par défaut = 1×
    audioEl.playbackRate = 1;
}

function formatTime(secs) {
    if (isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

// ════════════════════════════════════════════════════════════
//  QUESTIONS
// ════════════════════════════════════════════════════════════

function renderQuestions() {
    buildDots();
    renderCurrentQuestion();
    setupNav();
}

// ── Dots de progression ──────────────────────────────────────
function buildDots() {
    const container = document.getElementById('question-dots');
    container.innerHTML = '';
    state.questions.forEach((_, i) => {
        const dot = document.createElement('span');
        dot.className = 'q-dot' + (i === 0 ? ' active' : '');
        dot.dataset.index = i;
        dot.addEventListener('click', () => goToQuestion(i));
        container.appendChild(dot);
    });
}

function updateDots() {
    document.querySelectorAll('.q-dot').forEach((dot, i) => {
        dot.className = 'q-dot';
        if (i === state.currentIndex) dot.classList.add('active');
        else if (state.answers[state.questions[i]?.id] !== undefined) dot.classList.add('done');
    });
    document.getElementById('question-counter').textContent =
        `${state.currentIndex + 1} / ${state.questions.length}`;
}

// ── Rendu de la question courante ────────────────────────────
function renderCurrentQuestion() {
    const q    = state.questions[state.currentIndex];
    const card = document.getElementById('question-card');
    if (!q) return;

    const saved = state.answers[q.id];
    card.innerHTML = buildQuestionHTML(q, saved, state.submitted);
    updateDots();
    updateNavButtons();
    attachAnswerListeners(q);
}

function buildQuestionHTML(q, savedAnswer, isSubmitted) {
    const num = state.currentIndex + 1;

    // ── Badge type ────────────────────────────────────────────
    const typeLabels = {
        true_false:  'True / False',
        mcq:         'Multiple Choice',
        fill_blank:  'Fill in the Blank',
        word_order:  'Word Order',
        synonym:     'Synonym',
        grammar:     'Grammar',
        vocabulary:  'Vocabulary',
    };
    const typeLabel = typeLabels[q.type] || q.type;

    let html = `
        <div class="question-header">
            <span class="question-num">Q${num}</span>
            <span class="question-type-badge">${typeLabel}</span>
        </div>
        <p class="question-text">${q.question}</p>
    `;

    // ── Corps selon le type ───────────────────────────────────
    if (q.type === 'true_false') {
        html += buildTrueFalse(q, savedAnswer, isSubmitted);

    } else if (['mcq', 'grammar', 'vocabulary'].includes(q.type)) {
        html += buildMCQ(q, savedAnswer, isSubmitted);

    } else if (q.type === 'fill_blank') {
        html += buildFillBlank(q, savedAnswer, isSubmitted);

    } else if (q.type === 'word_order') {
        html += buildWordOrder(q, savedAnswer, isSubmitted);

    } else if (q.type === 'synonym') {
        html += buildSynonym(q, savedAnswer, isSubmitted);

    } else {
        // Fallback : input texte
        html += buildTextInput(q, savedAnswer, isSubmitted);
    }

    return html;
}

// ── True / False ─────────────────────────────────────────────
function buildTrueFalse(q, saved, submitted) {
    return `
        <div class="tf-options">
            ${['True', 'False'].map(opt => {
                let cls = 'choice-btn tf-btn';
                if (saved === opt) cls += ' selected';
                return `<button class="${cls}" data-value="${opt}" ${submitted ? 'disabled' : ''}>${opt}</button>`;
            }).join('')}
        </div>
    `;
}

// ── MCQ / Grammar / Vocabulary ───────────────────────────────
function buildMCQ(q, saved, submitted) {
    if (!q.choices || !q.choices.length) return '<p class="no-choices">No choices available.</p>';
    
    // Déterminer quelle réponse est sauvegardée (lettre ou texte)
    let savedLetter = null;
    if (saved) {
        // Si saved est une lettre (A, B, C, D)
        if (saved.length === 1 && saved.toUpperCase() >= 'A' && saved.toUpperCase() <= 'Z') {
            savedLetter = saved.toUpperCase();
        } else {
            // Si saved est le texte complet, trouver la lettre correspondante
            const savedIndex = q.choices.findIndex(c => c === saved);
            if (savedIndex >= 0) {
                savedLetter = String.fromCharCode(65 + savedIndex);
            }
        }
    }
    
    return `
        <div class="mcq-options">
            ${q.choices.map((choice, i) => {
                const letter = String.fromCharCode(65 + i); // A, B, C, D
                let cls = 'choice-btn mcq-btn';
                if (savedLetter === letter) cls += ' selected';
                return `
                    <button class="${cls}" data-value="${letter}" data-text="${choice}" ${submitted ? 'disabled' : ''}>
                        <span class="choice-letter">${letter}</span>
                        <span class="choice-text">${choice}</span>
                    </button>
                `;
            }).join('')}
        </div>
    `;
}

// ── Fill in the Blank ────────────────────────────────────────
function buildFillBlank(q, saved, submitted) {
    if (q.choices && q.choices.length > 0) {
        // Choix sous forme de boutons - même logique que MCQ
        let savedValue = saved;
        
        return `
            <div class="mcq-options">
                ${q.choices.map((choice, i) => {
                    const letter = String.fromCharCode(65 + i);
                    let cls = 'choice-btn fill-btn';
                    // Comparer soit par lettre, soit par texte
                    if (saved === letter || saved === choice) cls += ' selected';
                    return `<button class="${cls}" data-value="${choice}" ${submitted ? 'disabled' : ''}>${choice}</button>`;
                }).join('')}
            </div>
        `;
    }
    // Input texte libre
    return `
        <input type="text" class="text-input" id="fill-input-${q.id}"
               placeholder="Type your answer..."
               value="${saved || ''}" ${submitted ? 'disabled' : ''}/>
    `;
}

// ── Word Order ───────────────────────────────────────────────
function buildWordOrder(q, saved, submitted) {
    const words = q.choices || [];
    const shuffled = [...words].sort(() => Math.random() - 0.5);
    return `
        <div class="word-order-section">
            <div class="word-bank" id="word-bank-${q.id}">
                ${shuffled.map(w => `
                    <button class="word-chip ${submitted ? 'disabled' : ''}"
                            data-word="${w}" ${submitted ? 'disabled' : ''}>${w}</button>
                `).join('')}
            </div>
            <div class="word-answer-area" id="word-area-${q.id}">
                <p class="word-area-placeholder">Click words to build your sentence...</p>
            </div>
            <input type="hidden" id="word-input-${q.id}" value="${saved || ''}"/>
        </div>
    `;
}

// ── Synonym ──────────────────────────────────────────────────
function buildSynonym(q, saved, submitted) {
    return `
        <input type="text" class="text-input" id="synonym-input-${q.id}"
               placeholder="Type a synonym for '${q.target_word || ''}'..."
               value="${saved || ''}" ${submitted ? 'disabled' : ''}/>
    `;
}

// ── Text input générique ─────────────────────────────────────
function buildTextInput(q, saved, submitted) {
    return `
        <input type="text" class="text-input" id="text-input-${q.id}"
               placeholder="Your answer..."
               value="${saved || ''}" ${submitted ? 'disabled' : ''}/>
    `;
}

// ════════════════════════════════════════════════════════════
//  EVENT LISTENERS DES RÉPONSES
// ════════════════════════════════════════════════════════════

// ════════════════════════════════════════════════════════════
//  EVENT LISTENERS DES RÉPONSES
// ════════════════════════════════════════════════════════════

function attachAnswerListeners(q) {
    // ── Boutons de choix (TF / MCQ / Fill) ──────────────────
    document.querySelectorAll('.choice-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (state.submitted) return;
            document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            
            // ✅ CORRECTION : Toujours envoyer le texte complet au backend
            const value = btn.dataset.value;
            const text = btn.dataset.text || value; // data-text pour MCQ, sinon value
            
            if (q.type === 'true_false') {
                // True/False : envoyer "True" ou "False"
                state.answers[q.id] = value;
            } else if (['mcq', 'grammar', 'vocabulary'].includes(q.type)) {
                // MCQ/Grammar/Vocabulary : envoyer le texte de la réponse, pas la lettre
                state.answers[q.id] = text;
            } else if (q.type === 'fill_blank') {
                // Fill_blank : envoyer le texte du choix
                state.answers[q.id] = value;
            } else {
                state.answers[q.id] = value;
            }
            
            updateNavButtons();
        });
    });

    // ── Inputs texte (fill_blank sans choix, synonym) ────────
    const textInputs = ['fill-input', 'synonym-input', 'text-input'].map(prefix =>
        document.getElementById(`${prefix}-${q.id}`)
    ).filter(Boolean);

    textInputs.forEach(input => {
        input.addEventListener('input', () => {
            state.answers[q.id] = input.value.trim();
            updateNavButtons();
        });
    });

    // ── Word Order ───────────────────────────────────────────
    if (q.type === 'word_order') {
        setupWordOrder(q);
    }
}

function setupWordOrder(q) {
    const bank   = document.getElementById(`word-bank-${q.id}`);
    const area   = document.getElementById(`word-area-${q.id}`);
    const hidden = document.getElementById(`word-input-${q.id}`);
    if (!bank || !area) return;

    let selected = [];

    bank.querySelectorAll('.word-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            if (chip.classList.contains('used')) return;
            chip.classList.add('used');
            selected.push(chip.dataset.word);

            // Créer un chip dans la zone réponse
            const placed = document.createElement('span');
            placed.className = 'placed-word';
            placed.textContent = chip.dataset.word;
            placed.dataset.word = chip.dataset.word;
            placed.addEventListener('click', () => {
                // Retirer le mot
                selected = selected.filter((_, i) => i !== selected.lastIndexOf(chip.dataset.word));
                chip.classList.remove('used');
                placed.remove();
                updateWordAnswer();
            });
            area.querySelector('.word-area-placeholder')?.remove();
            area.appendChild(placed);
            updateWordAnswer();
        });
    });

    function updateWordAnswer() {
        const sentence = area.querySelectorAll('.placed-word');
        const words    = [...sentence].map(s => s.dataset.word).join(' ');
        if (hidden) hidden.value = words;
        state.answers[q.id] = words;
        updateNavButtons();
    }
}

// ════════════════════════════════════════════════════════════
//  NAVIGATION
// ════════════════════════════════════════════════════════════

function setupNav() {
    document.getElementById('btn-prev').addEventListener('click', () => {
        if (state.currentIndex > 0) goToQuestion(state.currentIndex - 1);
    });
    document.getElementById('btn-next').addEventListener('click', () => {
        if (state.currentIndex < state.questions.length - 1) {
            goToQuestion(state.currentIndex + 1);
        } else {
            showSubmitSection();
        }
    });
    document.getElementById('btn-submit').addEventListener('click', submitAnswers);


}

function goToQuestion(index) {
    state.currentIndex = index;
    renderCurrentQuestion();
}

function updateNavButtons() {
    const q          = state.questions[state.currentIndex];
    const hasAnswer  = q && state.answers[q.id] !== undefined && state.answers[q.id] !== '';
    const isLast     = state.currentIndex === state.questions.length - 1;

    document.getElementById('btn-prev').disabled = state.currentIndex === 0;
    document.getElementById('btn-next').disabled = !hasAnswer && !state.submitted;

    if (isLast) {
        document.getElementById('btn-next').innerHTML = 'Finish <i class="fas fa-check"></i>';
    } else {
        document.getElementById('btn-next').innerHTML = 'Next <i class="fas fa-arrow-right"></i>';
    }
}

function showSubmitSection() {
    document.getElementById('submit-section').style.display = 'block';
    document.getElementById('submit-section').scrollIntoView({ behavior: 'smooth' });
}

// ════════════════════════════════════════════════════════════
//  SOUMISSION
// ════════════════════════════════════════════════════════════

async function submitAnswers() {
    const btnSubmit = document.getElementById('btn-submit');
    btnSubmit.disabled   = true;
    btnSubmit.innerHTML  = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

    try {
        const res  = await fetch(`${API_BASE}/api/submit-listening/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                audio_id:   state.audioId,
                learner_id: state.learnerId,
                answers:    state.answers,
            }),
        });
        const data = await res.json();

        if (!data.success) {
            alert('Error submitting answers. Please try again.');
            btnSubmit.disabled  = false;
            btnSubmit.innerHTML = '<i class="fas fa-check"></i> Submit Answers';
            return;
        }

        state.submitted = true;

        // Si c'est la 1ère soumission, on la sauvegarde
        if (!state.firstSubmissionData) {
            state.firstSubmissionData = data;
        }

        // Si le backend dit already_done (retry) → afficher le modal "already done"
        if (data.already_done) {
            showAlreadyDonePanel();
        } else {
            showResult(data);
        }

    } catch (err) {
        console.error('Submit error:', err);
        btnSubmit.disabled  = false;
        btnSubmit.innerHTML = '<i class="fas fa-check"></i> Submit Answers';
    }
}

// ════════════════════════════════════════════════════════════
//  RÉSULTAT
// ════════════════════════════════════════════════════════════

function showResult(data) {
    document.getElementById('questions-section').style.display = 'none';
    document.getElementById('submit-section').style.display    = 'none';
    document.getElementById('result-panel').style.display      = 'block';

    document.getElementById('result-score').textContent  = data.score;
    document.getElementById('result-feedback').textContent = data.feedback || getFeedback(data.score);
    document.getElementById('result-detail').textContent =
        `${data.correct_count} / ${data.total} correct answers`;

    // Couleur du cercle selon le score
    const circle = document.querySelector('.result-score-circle');
    circle.classList.remove('score-high', 'score-mid', 'score-low');
    if (data.score >= 80)      circle.classList.add('score-high');
    else if (data.score >= 50) circle.classList.add('score-mid');
    else                       circle.classList.add('score-low');

    const reviewEl = document.getElementById('result-review');
    const showResultBtn = document.getElementById('btn-show-result');
    const retryBtn = document.getElementById('btn-retry');
    const generateBtn = document.getElementById('btn-generate');

    if (data.already_done) {
        // Mode: Déjà complété → cacher les détails initialement, afficher le message
        reviewEl.innerHTML = '<p class="already-done-msg"><i class="fas fa-info-circle"></i> You already completed this exercise.</p>';
        
       
        
        if (showResultBtn) {
            showResultBtn.style.display = 'inline-flex';
            showResultBtn.onclick = () => {
                showDetailedResults(data);
            };
        }
        
        // ⭐ Afficher le bouton Generate Exercise
        if (generateBtn) {
            generateBtn.style.display = 'inline-flex';
            generateBtn.onclick = () => {
                generateDynamicExercise();
            };
        }
        
    } else {
        // Mode: Première soumission → afficher les détails directement
        if (data.results && data.results.length > 0) {
            reviewEl.innerHTML = data.results.map(r => `
                <div class="review-item ${r.is_correct ? 'correct' : 'incorrect'}">
                    <span class="review-icon">
                        <i class="fas ${r.is_correct ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                    </span>
                    <div class="review-content">
                        <p class="review-question">${r.question}</p>
                        ${!r.is_correct ? `<p class="review-correct">
                            Correct answer: <strong>${r.correct_answer}</strong>
                        </p>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        // Masquer les boutons Show Result et Generate en première soumission
        if (showResultBtn) {
            showResultBtn.style.display = 'none';
        }
        
        if (generateBtn) {
            generateBtn.style.display = 'none';
        }
        
        if (retryBtn) {
            retryBtn.style.display = 'inline-flex';
        }
    }
}

// Nouvelle fonction pour afficher les résultats détaillés
function showDetailedResults(data) {
    const reviewEl = document.getElementById('result-review');
    
    if (data.results && data.results.length > 0) {
        reviewEl.innerHTML = data.results.map(r => `
            <div class="review-item ${r.is_correct ? 'correct' : 'incorrect'}">
                <span class="review-icon">
                    <i class="fas ${r.is_correct ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                </span>
                <div class="review-content">
                    <p class="review-question">${r.question}</p>
                    ${!r.is_correct ? `<p class="review-correct">
                        Correct answer: <strong>${r.correct_answer}</strong>
                    </p>` : ''}
                </div>
            </div>
        `).join('');
        
        // Scroll vers la zone de review
        reviewEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    //  Cacher le bouton "Show Results" après avoir cliqué dessus
    // car les résultats sont maintenant visibles
    const showResultBtn = document.getElementById('btn-show-result');
    if (showResultBtn) {
        showResultBtn.style.display = 'none';
    }

    // CACHER le bouton Generate Exercise quand on affiche les détails
    const generateBtn = document.getElementById('btn-generate');
    if (generateBtn) {
        generateBtn.style.display = 'none';
    }

}

function getFeedback(score) {
    if (score >= 90) return 'Excellent work!';
    if (score >= 80) return 'Very good!';
    if (score >= 70) return 'Good job!';
    if (score >= 60) return 'Well done!';
    if (score >= 50) return 'Keep trying!';
    if (score >= 40) return 'Need practice!';
    return 'Try more!';
}

// ════════════════════════════════════════════════════════════
//  ÉTATS UI
// ════════════════════════════════════════════════════════════

function showLoading(show) {
    document.getElementById('loading-state').style.display    = show ? 'flex' : 'none';
    document.getElementById('exercise-content').style.display = show ? 'none' : 'block';
}

function showExerciseContent() {
    document.getElementById('loading-state').style.display    = 'none';
    document.getElementById('error-state').style.display      = 'none';
    document.getElementById('exercise-content').style.display = 'block';
}

function showError(message) {
    document.getElementById('loading-state').style.display    = 'none';
    document.getElementById('exercise-content').style.display = 'none';
    document.getElementById('error-state').style.display      = 'flex';
    document.getElementById('error-message').textContent      = message;
}

// ════════════════════════════════════════════════════════════
//  PANEL "ALREADY DONE" — affiché après un retry + re-submit
// ════════════════════════════════════════════════════════════

function showAlreadyDonePanel() {
    // Cacher tout sauf le result-panel
    document.getElementById('questions-section').style.display = 'none';
    document.getElementById('submit-section').style.display    = 'none';
    document.getElementById('result-panel').style.display      = 'block';

    // Afficher le score de la 1ère soumission
    const d = state.firstSubmissionData;
    document.getElementById('result-score').textContent    = d.score;
    document.getElementById('result-feedback').textContent = d.feedback || getFeedback(d.score);
    document.getElementById('result-detail').textContent   = `${d.correct_count} / ${d.total} correct answers`;

    // Couleur du cercle
    const circle = document.querySelector('.result-score-circle');
    circle.classList.remove('score-high', 'score-mid', 'score-low');
    if (d.score >= 80)      circle.classList.add('score-high');
    else if (d.score >= 50) circle.classList.add('score-mid');
    else                    circle.classList.add('score-low');

    // Zone review : afficher le message "already done"
    document.getElementById('result-review').innerHTML =
        '<p class="already-done-msg"><i class="fas fa-info-circle"></i> You already completed this exercise.</p>';

    const showResultBtn = document.getElementById('btn-show-result');
    const retryBtn = document.getElementById('btn-retry');
    const generateBtn = document.getElementById('btn-generate');

    // Afficher le bouton "Show Result"
    if (showResultBtn) {
        showResultBtn.style.display = 'inline-flex';
        showResultBtn.onclick = () => {
            showResult(state.firstSubmissionData);
        };
    }
    

    
    // ⭐ Afficher le bouton Generate Exercise
    if (generateBtn) {
        generateBtn.style.display = 'inline-flex';
        generateBtn.onclick = () => {
            generateDynamicExercise();
        };
    }
}



