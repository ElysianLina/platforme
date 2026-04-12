// ============================================
// comprehension-ecrite.js
//
// ✅ FIX 1 : le backend retourne { text, questions }
//            pas { exercise: {...} } — on construit exercise nous-mêmes
// ✅ FIX 2 : submit envoie 'text_id' (ce que le backend attend)
//            pas 'exercise_id'
// ✅FIX 3 : subunit_id lu depuis l'URL en priorité
// ============================================

let currentExercise = null;
 
let lastSubmitResult = null; 

let currentGeneratedIndex = -1; 
let originalTextId = null;
// Lire les paramètres URL
function getSubunitInfo() {
    const params = new URLSearchParams(window.location.search);
    return {
        subunit:   params.get('subunit')    || localStorage.getItem('currentSubunit')      || '1.1',
        subunitId: params.get('subunit_id') || localStorage.getItem('currentSubunitId')    || null,
        title:     params.get('title')      || localStorage.getItem('currentSubunitTitle') || 'Exercise'
    };
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {

    console.log('📖 Page loaded, URL:', window.location.href);
    console.log('📖 Search params:', window.location.search);

    const { subunit, subunitId, title } = getSubunitInfo();

    console.log('📖 Init:', { subunit, subunitId, title });

    // Titre de la page
    const pageTitleEl = document.getElementById('page-title');
    if (pageTitleEl) pageTitleEl.textContent = title;

    // Lien retour
     const backLink = document.getElementById('back-link');
    if (backLink) {
        // Construction de l'URL avec tous les paramètres nécessaires
        let backUrl = `/exercise-menu/?subunit=${encodeURIComponent(subunit)}&title=${encodeURIComponent(title)}`;
        if (subunitId && subunitId !== 'null' && subunitId !== 'undefined') {
            backUrl += `&subunit_id=${subunitId}`;
        }
        backLink.href = backUrl;
        console.log('🔙 Back link URL:', backUrl);
    }

    // Charger l'exercice
    loadExercise(subunitId, subunit);

    // Soumission
    const form = document.getElementById('exercise-form');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
});

// ============================================
// CHARGEMENT DE L'EXERCICE
// ✅ FIX 1 : data.text et data.questions (pas data.exercise)
// ============================================

async function loadExercise(subunitId, subunitCode) {
    const readingContainer   = document.getElementById('reading-text');
    const questionsContainer = document.querySelector('.questions-form');
    const totalEl            = document.getElementById('total-q');

    readingContainer.innerHTML   = '<div class="loading-message"><i class="fas fa-spinner fa-spin"></i> Loading text...</div>';
    questionsContainer.innerHTML = '<div class="loading-message"><i class="fas fa-spinner fa-spin"></i> Loading questions...</div>';

    try {
        let url;
        if (subunitId && subunitId !== 'null' && subunitId !== 'undefined') {
            url = `http://localhost:8000/api/reading-exercise/?subunit_id=${subunitId}`;
        } else {
            throw new Error('subunit_id manquant. Retournez en arrière et sélectionnez un exercice.');
        }

        console.log('🔗 Fetching:', url);
        const response = await fetch(url);
        const rawText  = await response.text();
        console.log('📦 API response:', rawText);

        let data;
        try {
            data = JSON.parse(rawText);
        } catch {
            throw new Error('Réponse serveur invalide (non-JSON)');
        }

        if (!data.success) {
            throw new Error(data.error || 'Le serveur a retourné une erreur');
        }

        if (!data.text || !data.questions) {
            throw new Error('Réponse incomplète (text ou questions manquant)');
        }

        currentExercise = {
            text:            data.text,
            questions:       data.questions,
            total_questions: data.questions.length,
            coverage_score:  data.text.coverage_score  // ✅ AJOUTÉ ICI
        };

        // ✅ FIX CRITIQUE: Stocker l'ID du texte original et reset l'index
        originalTextId = data.text.id;
        currentGeneratedIndex = -1;
        console.log('📌 Original text ID stored:', originalTextId);
        console.log('📊 Coverage score:', data.text.coverage_score);  // ✅ LOG pour debug

        if (totalEl) totalEl.textContent = currentExercise.total_questions;
        renderExercise(currentExercise);

    } catch (error) {
        console.error('❌ Error loading exercise:', error);
        readingContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                Unable to load exercise.<br>
                <small>${error.message}</small><br>
                <button onclick="location.reload()" style="margin-top:10px;padding:8px 16px;cursor:pointer;">
                    Retry
                </button>
            </div>
        `;
        questionsContainer.innerHTML = '';
    }
}

// ============================================
// RENDU
// ============================================

function renderExercise(exercise) {
    const readingContainer = document.getElementById('reading-text');
    
    readingContainer.innerHTML = `
        <h3>${exercise.text.topic}</h3>
        ${exercise.text.content.split('\n\n').map(p => `<p>${p.trim()}</p>`).join('')}
    `;

    // ✅ AJOUT : Créer et insérer le badge dans le header de section
    const readingSection = document.querySelector('.reading-section');
    if (readingSection) {
        // Supprimer l'ancien badge s'il existe
        const oldBadge = readingSection.querySelector('.vocabulary-score-badge');
        if (oldBadge) oldBadge.remove();
        
        // Créer le nouveau badge si on a un score
        if (exercise.coverage_score !== null && exercise.coverage_score !== undefined) {
            const scorePercent = Math.round(exercise.coverage_score * 100);
            const badge = document.createElement('div');
            badge.className = 'vocabulary-score-badge';
            // ✅ Styles inline - LES DEUX À GAUCHE
            badge.style.cssText = `
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                white-space: nowrap;
                margin-left: 16px; /* Espace entre le titre et le badge */
            `;
            badge.innerHTML = `
                <i class="fas fa-chart-bar" style="font-size: 14px;"></i>
                <span>A1 Vocabulary Score: ${scorePercent}%</span>
            `;
            
            // Insérer dans le section-header
            const sectionHeader = readingSection.querySelector('.section-header');
            if (sectionHeader) {
                // ✅ LES DEUX ÉLÉMENTS À GAUCHE (flex-start)
                sectionHeader.style.display = 'flex';
                sectionHeader.style.justifyContent = 'flex-start'; /* CHANGÉ: space-between → flex-start */
                sectionHeader.style.alignItems = 'center';
                sectionHeader.style.flexWrap = 'wrap';
                sectionHeader.style.gap = '12px';
                
                sectionHeader.appendChild(badge);
            }
        }
    }

    const questionsContainer  = document.querySelector('.questions-form');
    const trueFalseQuestions  = exercise.questions.filter(q => q.type === 'true_false');
    const mcQuestions         = exercise.questions.filter(q => q.type === 'multiple_choice');
    const fillBlankQuestions  = exercise.questions.filter(q => q.type === 'fill_blank');

    let html = '';
    let questionCounter = 1;

    if (trueFalseQuestions.length > 0) {
        html += `
            <div class="question-group">
                <h3 class="group-title">A. True or False</h3>
                <p class="group-instruction">Read the statements and check True or False</p>
        `;
        trueFalseQuestions.forEach(q => { html += createTrueFalseQuestion(q, questionCounter++); });
        html += '</div>';
    }

    if (mcQuestions.length > 0) {
        html += `
            <div class="question-group">
                <h3 class="group-title">B. Multiple Choice</h3>
                <p class="group-instruction">Choose the correct answer</p>
        `;
        mcQuestions.forEach(q => { html += createMultipleChoiceQuestion(q, questionCounter++); });
        html += '</div>';
    }

    if (fillBlankQuestions.length > 0) {
        html += `
            <div class="question-group">
                <h3 class="group-title">C. Fill in the Blanks</h3>
                <p class="group-instruction">Write the correct answer in the empty space</p>
        `;
        fillBlankQuestions.forEach(q => { html += createFillBlankQuestion(q, questionCounter++); });
        html += '</div>';
    }

    html += `
        <div class="submit-section">
            <button type="submit" class="submit-btn">
                <i class="fas fa-check-circle"></i>
                Check my answers
            </button>
            <button type="button" class="submit-btn secondary" onclick="generateAdditionalExercise()">
                <i class="fas fa-plus-circle"></i>
                Add another exercise
            </button>
        </div>
    `;

    questionsContainer.innerHTML = html;
    trackProgress();
}

function createTrueFalseQuestion(question, number) {
    return `
        <div class="question-card" data-question="${number}" data-question-id="${question.id}">
            <div class="question-number">${number}</div>
            <div class="question-content">
                <p class="question-text">${question.question}</p>
                <div class="true-false-options">
                    <label class="tf-option">
                        <input type="radio" name="q${question.id}" value="true" data-question-id="${question.id}">
                        <span class="tf-label true">True</span>
                    </label>
                    <label class="tf-option">
                        <input type="radio" name="q${question.id}" value="false" data-question-id="${question.id}">
                        <span class="tf-label false">False</span>
                    </label>
                </div>
            </div>
        </div>
    `;
}

function createMultipleChoiceQuestion(question, number) {
    const choicesHtml = question.choices.map((choice, idx) => {
        const letter = String.fromCharCode(97 + idx);
        return `
            <label class="mc-option">
                <input type="radio" name="q${question.id}" value="${letter}" data-question-id="${question.id}">
                <span class="mc-label">${letter.toUpperCase()}. ${choice}</span>
            </label>
        `;
    }).join('');

    return `
        <div class="question-card" data-question="${number}" data-question-id="${question.id}">
            <div class="question-number">${number}</div>
            <div class="question-content">
                <p class="question-text">${question.question}</p>
                <div class="mc-options">${choicesHtml}</div>
            </div>
        </div>
    `;
}

function createFillBlankQuestion(question, number) {
    const questionText = question.question.replace(
        /_{3,}/g,
        `<input type="text" class="blank-input" name="q${question.id}" data-question-id="${question.id}" placeholder="Your answer...">`
    );

    return `
        <div class="question-card" data-question="${number}" data-question-id="${question.id}">
            <div class="question-number">${number}</div>
            <div class="question-content">
                <p class="question-text fill-blank">${questionText}</p>
            </div>
        </div>
    `;
}

// ============================================
// SUIVI DE PROGRESSION
// ============================================

function trackProgress() {
    const inputs         = document.querySelectorAll('input[type="radio"], input[type="text"]');
    const progressText   = document.getElementById('current-q');
    const progressFill   = document.getElementById('progress-fill');

    if (!currentExercise) return;
    const totalQuestions = currentExercise.questions.length;

    inputs.forEach(input => {
        input.addEventListener('change', updateProgress);
        input.addEventListener('input',  updateProgress);
    });

    function updateProgress() {
        const checkedInputs = new Set();
        inputs.forEach(input => {
            if (input.type === 'radio' && input.checked)         checkedInputs.add(input.name);
            else if (input.type === 'text' && input.value.trim()) checkedInputs.add(input.name);
        });
        const answered = checkedInputs.size;
        if (progressText) progressText.textContent = Math.min(answered + 1, totalQuestions);
        if (progressFill)  progressFill.style.width = `${(answered / totalQuestions) * 100}%`;
    }
}

// ============================================
// SOUMISSION DES RÉPONSES
// ✅ FIX 2 : envoie 'text_id' (ce que le backend attend)
//            pas 'exercise_id'
// ============================================

async function handleSubmit(e) {
    e.preventDefault();

    if (!currentExercise) {
        showNotification('Exercise not loaded');
        return;
    }

    const answers = {};
    let answeredCount = 0;

    currentExercise.questions.forEach(q => {
        let answer = null;
        if (q.type === 'true_false' || q.type === 'multiple_choice') {
            const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
            if (selected) { answer = selected.value; answeredCount++; }
        } else if (q.type === 'fill_blank') {
            const input = document.querySelector(`input[name="q${q.id}"]`);
            if (input && input.value.trim()) { answer = input.value.trim(); answeredCount++; }
        }
        if (answer !== null) answers[q.id] = answer;
    });

    if (answeredCount < currentExercise.questions.length) {
        showNotification(`Please answer all questions (${answeredCount}/${currentExercise.questions.length})`);
        return;
    }

    try {
        const learnerId = localStorage.getItem('learner_id');

        const response = await fetch('http://localhost:8000/api/submit-exercise/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text_id:    currentExercise.text.id,
                answers:    answers,
                learner_id: learnerId
            })
        });

        const result = await response.json();
        console.log('📊 Submit result:', result);

        if (result.success) {
            lastSubmitResult = result;

            if (result.already_done) {
                //  Déjà soumis en DB (résiste au Ctrl+R)
                showAlreadySubmittedModal();
            } else {
                //  Première soumission - PASSER true pour colorer les cartes
                showResults(result, true);  
            }
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('❌ Submission error:', error);
        showNotification('Error during correction: ' + error.message);
    }
}

// ============================================
// AFFICHAGE DES RÉSULTATS
// ============================================

function showResults(result, isFirstSubmit = false) {  // ✅ AJOUT paramètre isFirstSubmit
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'results-modal';

    let resultsArray = Array.isArray(result.results) ? result.results : Object.values(result.results);

    const byType = { true_false: [], multiple_choice: [], fill_blank: [] };
    currentExercise.questions.forEach((q, idx) => {
        const r = resultsArray.find(res => String(res.question_id) === String(q.id));
        if (r) byType[q.type].push({ ...r, originalOrder: idx + 1 });
    });

    const orderedResults = [...byType.true_false, ...byType.multiple_choice, ...byType.fill_blank];
    const finalResults   = orderedResults.map((r, idx) => ({ ...r, displayNum: idx + 1 }));

    const resultsHtml = finalResults.map(r => r.correct
        ? `<div class="result-item correct">
               <span class="result-num">${r.displayNum}</span>
               <span class="result-text">✓ Correct — ${r.correct_answer}</span>
           </div>`
        : `<div class="result-item incorrect">
               <span class="result-num">${r.displayNum}</span>
               <span class="result-text">✗ Incorrect — Correct answer: <strong>${r.correct_answer}</strong></span>
           </div>`
    ).join('');

    const learnerId = localStorage.getItem('learner_id');
    
    // ✅ UTILISER LE FEEDBACK DU BACKEND
    const feedbackMessage = result.feedback || '';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Results</h2>
                <button class="close-modal" onclick="closeResults()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="score-circle">
                    <span class="score-number">${result.score}</span>%
                </div>
                <p class="score-feedback" style="font-size: 20px; font-weight: 600; color: #4f46e5; margin: 12px 0; text-align: center;">
                    ${feedbackMessage}
                </p>
                <p style="text-align: center; color: #6b7280; margin-bottom: 20px;">
                    ${result.correct_count}/${result.total} correct
                </p>
                <div class="results-list">${resultsHtml}</div>
               
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    //  Ne colorer les cartes que lors du premier submit
    if (isFirstSubmit) {  
        resultsArray.forEach(r => {
            const card = document.querySelector(`[data-question-id="${r.question_id}"]`)?.closest('.question-card');
            if (card) card.classList.add(r.correct ? 'correct' : 'incorrect');
        });
    }
}

function closeResults() {
    const modal = document.getElementById('results-modal');
    if (modal) modal.remove();
}
function showAlreadySubmittedModal() {
    document.getElementById('already-submitted-modal')?.remove();

    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'already-submitted-modal';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Exercise Completed</h2>
                <button class="close-modal" onclick="closeAlreadySubmittedModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="font-size:16px; color:#4b5563; margin-bottom:28px; line-height:1.6;">
                    Exercise completed. Your progress will be based on your initial submission.
                </p>
                <div class="modal-actions" style="justify-content:center;">
                    <button class="btn-primary" onclick="closeAlreadySubmittedModal(); showResults(lastSubmitResult, false);">
                        <i class="fas fa-chart-bar"></i> Show results
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function closeAlreadySubmittedModal() {
    document.getElementById('already-submitted-modal')?.remove();
}
// ============================================
// ADDITIONAL EXERCISE — GAI
// ============================================

async function generateAdditionalExercise() {
    if (!originalTextId) {
        showNotification('Original exercise not loaded');
        return;
    }

    const { subunitId, title } = getSubunitInfo();
    
    // Redirection vers la page Django des exercices générés
    const targetUrl = `/generated_reading_ex/?` + 
        `original_id=${originalTextId}` +
        `&subunit_id=${subunitId || ''}` +
        `&title=${encodeURIComponent(title || 'Exercise')}`;

    console.log('🔄 Redirecting to generated exercise page:', targetUrl);
    window.location.href = targetUrl;
}

// ============================================
// NOTIFICATIONS
// ============================================

function showNotification(message) {
    document.querySelector('.notification')?.remove();

    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `<i class="fas fa-info-circle"></i><span>${message}</span>`;

    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}