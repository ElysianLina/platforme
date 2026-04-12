// ============================================
// generated-exercise.js
// Page des exercices générés par IA (max 3)
// ============================================

const MAX_GENERATED = 3;

let originalTextId = null;
let originalSubunitId = null;
let originalTitle = null;
let generatedTexts = [];
let currentIndex = 0;
let currentExercise = null;
let lastSubmitResult = null; // Pour stocker le résultat de la première soumission

// ============================================
// INITIALISATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer les paramètres URL
    const params = new URLSearchParams(window.location.search);
    originalTextId = params.get('original_id');
    originalSubunitId = params.get('subunit_id');
    originalTitle = params.get('title') || 'Exercise';
    
    if (!originalTextId) {
        showError('Missing original exercise ID');
        return;
    }

    // Configurer le lien retour
    setupBackLink();
    
    // Configurer les boutons
    document.getElementById('prev-btn').addEventListener('click', () => navigate(-1));
    document.getElementById('next-btn').addEventListener('click', () => navigate(1));
    document.getElementById('submit-btn').addEventListener('click', handleSubmit);
    document.getElementById('new-btn').addEventListener('click', generateNew);

    // Mettre à jour le badge de limite
    document.getElementById('max-count').textContent = MAX_GENERATED;

    // Charger les textes générés
    loadGeneratedTexts();
});

function setupBackLink() {
    const backLink = document.getElementById('back-link');
    if (backLink && originalSubunitId) {
        const url = `/comprehension-ecrite/?subunit_id=${originalSubunitId}&title=${encodeURIComponent(originalTitle)}`;
        backLink.href = url;
    }
}

// ============================================
// CHARGEMENT DES TEXTES GÉNÉRÉS
// ============================================

async function loadGeneratedTexts() {
    try {
        const learnerId = localStorage.getItem('learner_id');
        // ✅ Passer learner_id pour charger uniquement les textes de cet apprenant
        let url = `http://localhost:8000/api/generated-texts/?original_id=${originalTextId}`;
        if (learnerId) url += `&learner_id=${learnerId}`;
 
        const response = await fetch(url);
        const data = await response.json();
 
        if (!data.success) {
            throw new Error(data.error);
        }
 
        generatedTexts = data.generated_texts || [];
        
        // Mettre à jour le compteur
        document.getElementById('current-count').textContent = generatedTexts.length;
        
        // Vérifier si on a atteint la limite
        updateLimitDisplay();
 
        if (generatedTexts.length === 0) {
            // Aucun texte, en générer un premier
            await generateNew();
        } else {
            renderTabs();
            loadText(0);
        }
 
    } catch (error) {
        console.error('❌ Error loading:', error);
        showError('Failed to load generated exercises');
    }
}

// ============================================
// GÉNÉRATION D'UN NOUVEAU TEXTE
// ============================================

async function generateNew() {
    // ✅ Vérifier la limite
    if (generatedTexts.length >= MAX_GENERATED) {
        showNotification(`Maximum ${MAX_GENERATED} exercises reached!`);
        return;
    }

    const readingContainer = document.getElementById('reading-text');
    readingContainer.innerHTML = `
        <div class="loading-message">
            <i class="fas fa-spinner fa-spin"></i> Generating with AI...
        </div>
    `;

    // Désactiver le bouton pendant la génération
    const newBtn = document.getElementById('new-btn');
    newBtn.disabled = true;
    newBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

    try {
        const learnerId = localStorage.getItem('learner_id');

        const response = await fetch('http://localhost:8000/api/generate-reading-ex/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                exercise_id: originalTextId,
                learner_id: learnerId,
                generated_index: generatedTexts.length 
            })
        });

        const data = await response.json();

        if (!data.success) {
            if (data.limit_reached) {
                showNotification(`Maximum ${MAX_GENERATED} exercises reached!`);
                updateLimitDisplay();
                return;
            }
            throw new Error(data.error);
        }

        // Ajouter le nouveau texte
        const newText = {
            id: data.generated_id,
            index: data.generated_index,
            topic: data.exercise.text.topic,
            content: data.exercise.text.content,
            questions: data.exercise.questions,
            is_new: true
        };

        generatedTexts.push(newText);
        currentIndex = data.generated_index;

        // Mettre à jour l'affichage
        document.getElementById('current-count').textContent = generatedTexts.length;
        updateLimitDisplay();
        renderTabs();
        displayExercise(newText);

        // Message selon la limite
        if (generatedTexts.length >= MAX_GENERATED) {
            showNotification('Exercise generated! Maximum reached (3/3).');
        } else {
            showNotification(`Exercise generated! (${generatedTexts.length}/${MAX_GENERATED})`);
        }

    } catch (error) {
        console.error('❌ Generation error:', error);
        readingContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to generate.</p>
                <button onclick="generateNew()" class="submit-btn" style="margin-top: 16px;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    } finally {
        newBtn.disabled = false;
        newBtn.innerHTML = '<i class="fas fa-plus-circle"></i> Generate New';
    }
}

// ============================================
// AFFICHAGE ET NAVIGATION
// ============================================

function updateLimitDisplay() {
    const badge = document.getElementById('limit-badge');
    const newBtn = document.getElementById('new-btn');
    const submitSection = document.getElementById('submit-section');
    const limitMessage = document.getElementById('limit-message');
    
    const current = generatedTexts.length;
    
    if (current >= MAX_GENERATED) {
        // Limite atteinte
        badge.classList.add('full');
        newBtn.style.display = 'none';
        limitMessage.style.display = 'block';
    } else {
        // Encore de la place
        badge.classList.remove('full');
        newBtn.style.display = 'inline-flex';
        limitMessage.style.display = 'none';
    }
}

function renderTabs() {
    const tabsContainer = document.getElementById('generated-tabs');
    tabsContainer.innerHTML = '';

    generatedTexts.forEach((text, idx) => {
        const tab = document.createElement('button');
        tab.className = `generated-tab ${idx === currentIndex ? 'active' : ''} ${text.is_new ? 'new' : ''}`;
        tab.innerHTML = `
            <i class="fas fa-file-alt"></i>
            <div>Exercise ${idx + 1}</div>
        `;
        tab.onclick = () => loadText(idx);
        tabsContainer.appendChild(tab);
        
        // Retirer le flag "new" après affichage
        if (text.is_new) text.is_new = false;
    });

    updateNavButtons();
}

function loadText(index) {
    if (index < 0 || index >= generatedTexts.length) return;
    
    currentIndex = index;
    renderTabs();
    displayExercise(generatedTexts[index]);
}

function navigate(direction) {
    const newIndex = currentIndex + direction;
    if (newIndex >= 0 && newIndex < generatedTexts.length) {
        loadText(newIndex);
    }
}

function updateNavButtons() {
    document.getElementById('prev-btn').disabled = currentIndex === 0;
    document.getElementById('next-btn').disabled = currentIndex >= generatedTexts.length - 1;
    
    // Mettre à jour le label
    document.getElementById('generated-label').textContent = `Exercise ${currentIndex + 1}`;
}

// ============================================
// AFFICHAGE DE L'EXERCICE
// ============================================

function displayExercise(textData) {
    const readingContainer = document.getElementById('reading-text');
    const questionsContainer = document.querySelector('.questions-form');

    // Texte
    readingContainer.innerHTML = `
        <h3>${textData.topic}</h3>
        ${textData.content.split('\n\n').map(p => `<p>${p.trim()}</p>`).join('')}
    `;

    // Questions
    currentExercise = {
        text: {
            id: textData.id,
            topic: textData.topic,
            content: textData.content
        },
        questions: textData.questions,
        total_questions: textData.questions.length
    };

    renderQuestions(textData.questions);
}

function renderQuestions(questions) {
    const container = document.querySelector('.questions-form');
    
    const byType = {
        true_false: questions.filter(q => q.type === 'true_false'),
        multiple_choice: questions.filter(q => q.type === 'multiple_choice'),
        fill_blank: questions.filter(q => q.type === 'fill_blank')
    };

    let html = '';
    let counter = 1;

    // True/False
    if (byType.true_false.length > 0) {
        html += createGroup('True or False', 'check-circle', byType.true_false, counter);
        counter += byType.true_false.length;
    }

    // Multiple Choice
    if (byType.multiple_choice.length > 0) {
        html += createGroup('Multiple Choice', 'list-ul', byType.multiple_choice, counter);
        counter += byType.multiple_choice.length;
    }

    // Fill Blank
    if (byType.fill_blank.length > 0) {
        html += createGroup('Fill in the Blanks', 'pen', byType.fill_blank, counter);
    }

    container.innerHTML = html;
}

function createGroup(title, icon, questions, startCounter) {
    let html = `
        <div class="question-group">
            <h3 class="group-title"><i class="fas fa-${icon}"></i> ${title}</h3>
            <p class="group-instruction">Answer all questions</p>
    `;
    
    questions.forEach((q, idx) => {
        const num = startCounter + idx;
        if (q.type === 'true_false') {
            html += createTrueFalse(q, num);
        } else if (q.type === 'multiple_choice') {
            html += createMultipleChoice(q, num);
        } else {
            html += createFillBlank(q, num);
        }
    });
    
    html += '</div>';
    return html;
}

function createTrueFalse(q, num) {
    return `
        <div class="question-card" data-qid="${q.id}">
            <div class="question-number">${num}</div>
            <p class="question-text">${q.question}</p>
            <div class="true-false-options">
                <label class="tf-option">
                    <input type="radio" name="q${q.id}" value="true">
                    <span class="tf-label true"><i class="fas fa-check"></i> True</span>
                </label>
                <label class="tf-option">
                    <input type="radio" name="q${q.id}" value="false">
                    <span class="tf-label false"><i class="fas fa-times"></i> False</span>
                </label>
            </div>
        </div>
    `;
}

function createMultipleChoice(q, num) {
    const choices = (q.choices || []).map((choice, idx) => {
        const letter = String.fromCharCode(65 + idx);
        return `
            <label class="mc-option">
                <input type="radio" name="q${q.id}" value="${letter.toLowerCase()}">
                <span class="mc-label">${letter}. ${choice}</span>
            </label>
        `;
    }).join('');

    return `
        <div class="question-card" data-qid="${q.id}">
            <div class="question-number">${num}</div>
            <p class="question-text">${q.question}</p>
            <div class="mc-options">${choices}</div>
        </div>
    `;
}

function createFillBlank(q, num) {
    const text = q.question.replace(/_{3,}/g, 
        `<input type="text" class="blank-input" name="q${q.id}" placeholder="Answer...">`
    );
    
    return `
        <div class="question-card" data-qid="${q.id}">
            <div class="question-number">${num}</div>
            <p class="question-text fill-blank">${text}</p>
        </div>
    `;
}

// ============================================
// SOUMISSION
// ============================================

// ============================================
// SOUMISSION
// ============================================

async function handleSubmit() {
    if (!currentExercise) {
        showNotification('No exercise loaded');
        return;
    }

    const answers = {};
    let answered = 0;

    currentExercise.questions.forEach(q => {
        let answer = null;
        if (q.type === 'true_false' || q.type === 'multiple_choice') {
            const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
            if (selected) {
                answer = selected.value;
                answered++;
            }
        } else {
            const input = document.querySelector(`input[name="q${q.id}"]`);
            if (input && input.value.trim()) {
                answer = input.value.trim();
                answered++;
            }
        }
        if (answer) answers[q.id] = answer;
    });

    if (answered < currentExercise.questions.length) {
        showNotification(`Answer all questions (${answered}/${currentExercise.questions.length})`);
        return;
    }

    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';

    try {
        const learnerId = localStorage.getItem('learner_id');

        const response = await fetch('http://localhost:8000/api/submit-generated-exercise/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                generated_text_id: currentExercise.text.id,
                answers: answers,
                learner_id: learnerId
            })
        });

        const result = await response.json();

        if (result.success) {
            // CORRECTION: Stocker le résultat avec tous les détails nécessaires
            lastSubmitResult = result;

            if (result.already_completed) {
                // ⛔ Déjà soumis → Modal "Exercise Completed"
                // CORRECTION: S'assurer que detailed_results est présent dans lastSubmitResult
                showAlreadySubmittedModal();
            } else {
                // ✅ Première soumission → Modal avec score
                showResults(result);
            }
        } else {
            throw new Error(result.error);
        }

    } catch (error) {
        showNotification('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Answers';
    }
}

// ============================================
// RÉSULTATS - Deux cas: première fois vs déjà complété
// ============================================
// ============================================
// RÉSULTATS - Ordonnés par type de question
// ============================================

function showResults(result) {
    // Supprimer les modals existants
    document.getElementById('results-modal')?.remove();
    document.getElementById('already-submitted-modal')?.remove();

    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'results-modal';

    // Récupérer les valeurs
    const totalQuestions = result.total_questions || result.total || 0;
    const correctCount = result.correct_count || 0;
    const scorePercentage = result.score_percentage || 0;
    const scoreOn10 = result.score_on_10 || 0;
    
    // Récupérer les résultats détaillés
    let resultsArray = [];
    
    if (result.results && Array.isArray(result.results)) {
        resultsArray = result.results;
    }
    else if (result.detailed_results && Array.isArray(result.detailed_results)) {
        resultsArray = result.detailed_results;
    }

    console.log('DEBUG showResults:', {
        totalQuestions,
        correctCount,
        scorePercentage,
        scoreOn10,
        resultsArray
    });

    // ============================================
    // ORDONNER PAR TYPE: True/False → Multiple Choice → Fill Blank
    // ============================================
    
    // Séparer par type
    const trueFalseResults = [];
    const multipleChoiceResults = [];
    const fillBlankResults = [];
    
    for (const r of resultsArray) {
        const type = r.question_type || 'unknown';
        
        if (type === 'true_false') {
            trueFalseResults.push(r);
        } else if (type === 'multiple_choice') {
            multipleChoiceResults.push(r);
        } else if (type === 'fill_blank') {
            fillBlankResults.push(r);
        }
    }

    // Fonction pour créer le HTML d'un résultat
    function createResultItem(r, num) {
        const isCorrect = r.correct;
        const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
        const borderColor = isCorrect ? '#28a745' : '#dc3545';
        const textColor = isCorrect ? '#155724' : '#721c24';
        const icon = isCorrect ? '✓' : '✗';
        
        return `
            <div class="result-item" style="
                background: ${bgColor};
                border-left: 4px solid ${borderColor};
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span style="
                    background: ${borderColor};
                    color: white;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    flex-shrink: 0;
                ">${num}</span>
                <span style="color: ${textColor}; flex: 1;">
                    ${isCorrect 
                        ? `<strong>${icon} ${r.correct_answer}</strong>`
                        : `${icon} Your answer: <em>${r.user_answer}</em> | Correct: <strong>${r.correct_answer}</strong>`
                    }
                </span>
            </div>
        `;
    }

    // Construire le HTML dans l'ordre souhaité
    let html = '';
    let counter = 1;

    // 1. TRUE/FALSE (questions 1-3)
    if (trueFalseResults.length > 0) {
        html += `<div style="margin-bottom: 20px;">
            <h5 style="color: #667eea; margin-bottom: 10px; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">
                <i class="fas fa-check-circle"></i> True / False
            </h5>`;
        for (const r of trueFalseResults) {
            html += createResultItem(r, counter++);
        }
        html += `</div>`;
    }
    
    // 2. MULTIPLE CHOICE (questions 4-6)
    if (multipleChoiceResults.length > 0) {
        html += `<div style="margin-bottom: 20px;">
            <h5 style="color: #667eea; margin-bottom: 10px; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">
                <i class="fas fa-list-ul"></i> Multiple Choice
            </h5>`;
        for (const r of multipleChoiceResults) {
            html += createResultItem(r, counter++);
        }
        html += `</div>`;
    }
    
    // 3. FILL BLANK (questions 7-10)
    if (fillBlankResults.length > 0) {
        html += `<div style="margin-bottom: 20px;">
            <h5 style="color: #667eea; margin-bottom: 10px; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">
                <i class="fas fa-pen"></i> Fill in the Blanks
            </h5>`;
        for (const r of fillBlankResults) {
            html += createResultItem(r, counter++);
        }
        html += `</div>`;
    }

    // Si aucun résultat n'est organisé par type, afficher dans l'ordre original
    if (html === '' && resultsArray.length > 0) {
        html += `<div style="margin-bottom: 20px;">
            <h5 style="color: #667eea; margin-bottom: 10px;">Results</h5>`;
        for (let i = 0; i < resultsArray.length; i++) {
            html += createResultItem(resultsArray[i], i + 1);
        }
        html += `</div>`;
    }

    // Feedback et couleurs
    const feedback = result.feedback || '';
    
    let scoreColor = '#dc3545';
    let scoreIcon = 'fa-frown';
    let scoreBg = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
    
    if (scoreOn10 >= 9) {
        scoreColor = '#28a745';
        scoreIcon = 'fa-trophy';
        scoreBg = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
    } else if (scoreOn10 >= 7) {
        scoreColor = '#17a2b8';
        scoreIcon = 'fa-smile';
        scoreBg = 'linear-gradient(135deg, #17a2b8 0%, #138496 100%)';
    } else if (scoreOn10 >= 5) {
        scoreColor = '#ffc107';
        scoreIcon = 'fa-meh';
        scoreBg = 'linear-gradient(135deg, #ffc107 0%, #e0a800 100%)';
    }

    // Message de sauvegarde
    let saveStatusHtml = '';
    if (result.saved_result_id) {
        saveStatusHtml = `
            <div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
                <i class="fas fa-save"></i> Result saved for tracking
            </div>`;
    } else if (result.evaluation_status === 'not_saved_no_learner') {
        saveStatusHtml = `
            <div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
                <i class="fas fa-exclamation-circle"></i> Log in to save your progress
            </div>`;
    } else if (result.already_completed) {
        saveStatusHtml = `
            <div style="background: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
                <i class="fas fa-check-circle"></i> Completed on ${result.completed_at || 'previous session'}
            </div>`;
    }

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px; max-height: 80vh; overflow-y: auto;">
            <div class="modal-header" style="background: ${scoreBg}; color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0;"><i class="fas fa-chart-line"></i> Results</h2>
                <button onclick="closeResults()" style="background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer;">&times;</button>
            </div>
            <div class="modal-body" style="padding: 20px;">
                <!-- Score -->
                <div style="background: ${scoreBg}; margin-bottom: 20px; padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <div style="font-size: 1rem; margin-bottom: 8px;"><i class="fas ${scoreIcon}"></i> Your Score</div>
                    <div style="font-size: 3rem; font-weight: bold;">${scoreOn10}<span style="font-size: 1.5rem;">/10</span></div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">${correctCount}/${totalQuestions} correct (${scorePercentage}%)</div>
                </div>
                
                <!-- Feedback -->
                <div style="border-left: 4px solid ${scoreColor}; background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
                    <i class="fas fa-comment-dots" style="color: ${scoreColor};"></i> <strong>Feedback</strong>
                    <p style="margin: 8px 0 0 0; color: #555;">${feedback}</p>
                </div>
                
                ${saveStatusHtml}
                
                <!-- Answer Details -->
                <div>
                    <h4 style="margin-bottom: 16px; color: #333; text-transform: uppercase; font-size: 0.9rem;">Answer Details</h4>
                    ${html}
                </div>
            </div>
            <div class="modal-footer" style="padding: 20px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="closeResults()" style="padding: 10px 20px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer;">
                    Close
                </button>
                <button onclick="backToOriginal()" style="padding: 10px 20px; border: none; background: ${scoreBg}; color: white; border-radius: 6px; cursor: pointer;">
                    Back to Original
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// ============================================
// MODAL "EXERCISE COMPLETED" 
// ============================================

function showAlreadySubmittedModal() {
    // Supprimer le modal existant s'il y en a un
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
                <div class="modal-actions" style="text-align: center;">
                    <button class="btn-primary" onclick="closeAlreadySubmittedModalAndShowResults()" style="
                        padding: 12px 28px;
                        border: none;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border-radius: 25px;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 500;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    ">
                        <i class="fas fa-chart-bar"></i> Show results
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// CORRECTION: Nouvelle fonction pour gérer la fermeture et l'affichage des résultats
function closeAlreadySubmittedModalAndShowResults() {
    closeAlreadySubmittedModal();
    // CORRECTION: Vérifier que lastSubmitResult a les données nécessaires
    if (lastSubmitResult) {
        showResults(lastSubmitResult);
    } else {
        showNotification('Error: Could not load results');
    }
}

function closeAlreadySubmittedModal() {
    document.getElementById('already-submitted-modal')?.remove();
}

function closeResults() {
    const modal = document.getElementById('results-modal');
    if (modal) modal.remove();
}

function backToOriginal() {
    if (originalSubunitId) {
        window.location.href = `/comprehension-ecrite/?subunit_id=${originalSubunitId}&title=${encodeURIComponent(originalTitle)}`;
    } else {
        window.history.back();
    }
}

// ============================================
// UTILITAIRES
// ============================================

function showNotification(msg) {
    document.querySelector('.notification')?.remove();
    
    const n = document.createElement('div');
    n.className = 'notification';
    n.innerHTML = `<i class="fas fa-info-circle"></i><span>${msg}</span>`;
    document.body.appendChild(n);
    
    setTimeout(() => n.classList.add('show'), 10);
    setTimeout(() => {
        n.classList.remove('show');
        setTimeout(() => n.remove(), 300);
    }, 3000);
}

function showError(msg) {
    document.getElementById('reading-text').innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle"></i>
            <p>${msg}</p>
            <button onclick="backToOriginal()" class="submit-btn" style="margin-top: 20px;">
                <i class="fas fa-arrow-left"></i> Go Back
            </button>
        </div>
    `;
}

// ============================================
// AFFICHAGE MESSAGE LIMITE ATTEINTE
// ============================================

function showLimitReachedMessage() {
    const readingContainer = document.getElementById('reading-text');
    
    readingContainer.innerHTML = `
        <div class="limit-message">
            <i class="fas fa-lock"></i>
            <h4>Maximum Exercises Reached</h4>
            <p>You have generated the maximum of <strong>${MAX_GENERATED} exercises</strong> for this text.</p>
            <p style="margin-top: 12px; font-size: 0.9rem;">
                You can still practice with the existing exercises using the tabs above.
            </p>
        </div>
    `;
    
    // Masquer le formulaire de questions
    document.querySelector('.questions-form').innerHTML = '';
    document.getElementById('submit-btn').style.display = 'none';
}

// Exposer fonctions globales
window.closeResults = closeResults;
window.backToOriginal = backToOriginal;
window.closeAlreadySubmittedModal = closeAlreadySubmittedModal;
window.closeAlreadySubmittedModalAndShowResults = closeAlreadySubmittedModalAndShowResults;