// ============================================
// writing.js - Writing Exercise Frontend
// ============================================

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const DEFAULT_SUBUNIT = '1.1';

// State
let currentExercise = null;
let currentSubunit = null;
let learnerId = null;
let isSubmitting = false;

// ============================================
// UTILITY FUNCTIONS
// ============================================

function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        subunit: params.get('subunit') || DEFAULT_SUBUNIT,
        title: params.get('title') || 'Writing Exercise',
        subunitId: params.get('subunit_id') || null
    };
}

function showLoading() {
    document.getElementById('loading-state').style.display = 'flex';
    document.getElementById('exercise-content').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('already-submitted').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading-state').style.display = 'none';
}

function showExercise() {
    document.getElementById('exercise-content').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('already-submitted').style.display = 'none';
}

function showResults(isReviewMode = false) {
    document.getElementById('exercise-content').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('already-submitted').style.display = 'none';


    // Afficher/masquer le bouton "Generate Another Exercise"
    const generateBtn = document.getElementById('generate-exercise-btn');
    if (generateBtn) {
        generateBtn.style.display = isReviewMode ? 'inline-flex' : 'none';
    }
}

function showAlreadySubmitted(result = null) {
    document.getElementById('exercise-content').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('already-submitted').style.display = 'block';
    
    if (result) {
        const prevResultDiv = document.getElementById('previous-result');
        prevResultDiv.innerHTML = `
            <div class="score-item">
                <div class="score-item-label">Your Score</div>
                <div class="score-item-value" style="color: ${getScoreColor(result.score)}">${result.score}%</div>
            </div>
            <div style="margin-top: 1rem; color: var(--gray-600);">
                <i class="fas fa-font"></i> ${result.word_count} words submitted
            </div>
        `;
        
        // Store result for view button
        const userSubmittedText = result.submitted_text || result.text || '';
        document.getElementById('view-result-btn').onclick = () => {

            const feedback = result.feedback || {};
        const errors = feedback.errors || [];
        
        // 🔥 RECONSTRUIRE le texte surligné côté client
        let highlightedText = userSubmittedText;
        if (errors.length > 0 && userSubmittedText) {
            highlightedText = _highlightErrorsClientSide(userSubmittedText, errors);
        }



            displayResults({
                overall_score: result.score,
                word_count: result.word_count,
                feedback: result.feedback,
                your_text_highlighted: highlightedText
            }, userSubmittedText, currentExercise.model_answer, true);
        };
    }
}
function _highlightErrorsClientSide(text, errors) {
    if (!errors || errors.length === 0) return text;
    
    // Trier par longueur décroissante pour éviter les conflits
    const sorted = [...errors]
        .filter(e => e.word)
        .sort((a, b) => b.word.length - a.word.length);
    
    let result = text;
    const alreadyDone = new Set();
    
    for (const err of sorted) {
        const word = err.word;
        if (!word || alreadyDone.has(word)) continue;
        
        // Escape HTML pour éviter d'injecter du HTML dans le title
        const safeWord = word.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        const safeCorrection = (err.correction || err.corrected_sentence || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        const safeType = (err.type || 'error').replace(/&/g,'&amp;').replace(/"/g,'&quot;');
        
        const title = `${safeType}: ${safeWord} → ${safeCorrection}`;
        const replacement = `<span class="error-word" title="${title}">${word}</span>`;
        
        // Remplacer la première occurrence (case-insensitive, mot entier)
        const regex = new RegExp(`\\b${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
        const newResult = result.replace(regex, replacement);
        
        if (newResult !== result) {
            result = newResult;
            alreadyDone.add(word);
        }
    }
    return result;
}
function getScoreColor(score) {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--warning)';
    return 'var(--danger)';
}

// ============================================
// API FUNCTIONS
// ============================================

async function fetchExercise(subunitId) {
    try {
        const response = await fetch(`${API_BASE_URL}/writing-exercise/?subunit_id=${subunitId}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load exercise');
        }
        
        return data.exercise;
    } catch (error) {
        console.error('Error fetching exercise:', error);
        throw error;
    }
}

async function checkExistingResult(exerciseId, learnerId) {
    if (!learnerId) return null;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/check-writing-result/?exercise_id=${exerciseId}&learner_id=${learnerId}`
        );
        const data = await response.json();
        
        if (data.success && data.has_result) {
            return data;
        }
        return null;
    } catch (error) {
        console.error('Error checking result:', error);
        return null;
    }
}

async function submitWriting(exerciseId, text, learnerId) {
    const payload = {
        exercise_id: exerciseId,
        text: text,
        learner_id: learnerId
    };
    
    const response = await fetch(`${API_BASE_URL}/submit-writing-exercise/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    return await response.json();
}

// ============================================
// UI UPDATE FUNCTIONS
// ============================================

function updateHeader(subunit, title) {
    document.getElementById('subunit-id').textContent = subunit;
    document.getElementById('subunit-title').textContent = title;
}

function renderExercise(exercise) {
    // Update instruction text
    document.getElementById('instruction-text').textContent = exercise.instruction;
    
    // Update word target
    document.getElementById('word-target').textContent = exercise.word_count_target;
    
    // Render guiding points
    const pointsList = document.getElementById('points-list');
    pointsList.innerHTML = '';
    
    if (exercise.guiding_points && exercise.guiding_points.length > 0) {
        exercise.guiding_points.forEach(point => {
            const li = document.createElement('li');
            li.textContent = point;
            pointsList.appendChild(li);
        });
    } else {
        document.getElementById('guiding-points').style.display = 'none';
    }
    
    // Store model answer for later
    currentExercise = exercise;
}

function updateWordCount() {
    const textarea = document.getElementById('writing-textarea');
    const counter = document.getElementById('word-counter');
    
    const text = textarea.value.trim();
    const wordCount = text ? text.split(/\s+/).length : 0;
    
    counter.textContent = `${wordCount} word${wordCount !== 1 ? 's' : ''}`;
    
    // Update counter color based on target (60-80 words)
    counter.className = 'word-counter';
    if (wordCount < 50) {
        counter.classList.add('warning');
    } else if (wordCount > 100) {
        counter.classList.add('danger');
    } else if (wordCount >= 60 && wordCount <= 80) {
        counter.classList.add('success');
    }
}

function displayResults(result, userText, modelAnswer, isReviewMode = false, fullResponse = null) {
    const feedback = result.feedback;
    
    // Update score circle
    const score = result.overall_score;
    document.getElementById('score-value').textContent = score;
    
    // Score breakdown
    const breakdown = document.getElementById('score-breakdown');
    const scores = feedback.score_breakdown || {};
    breakdown.innerHTML = `
        <div class="score-item">
            <div class="score-item-label">Content</div>
            <div class="score-item-value">${scores.content || 0}</div>
        </div>
        <div class="score-item">
            <div class="score-item-label">Vocabulary</div>
            <div class="score-item-value">${scores.vocabulary || 0}</div>
        </div>
        <div class="score-item">
            <div class="score-item-label">Grammar</div>
            <div class="score-item-value">${scores.grammar || 0}</div>
        </div>
        <div class="score-item">
            <div class="score-item-label">Length</div>
            <div class="score-item-value">${scores.length || 0}</div>
        </div>
    `;
    
    // Feedback content
    const feedbackContent = document.getElementById('feedback-content');

    // Errors list
    let errorsHtml = '';
    if (feedback.errors && feedback.errors.length > 0) {
        errorsHtml = `
            <div class="feedback-section improvements">
                <h4><i class="fas fa-exclamation-circle"></i> Errors to Fix</h4>
                <ul class="feedback-list improvements">
                   ${feedback.errors.map(e => {
                       const errObj = (typeof e === 'object' && e !== null) ? e : { word: String(e) };
                       const word = errObj.word || 'unknown';
                       const correction = errObj.correction || errObj.corrected_sentence || '';
                       const type = errObj.type || '';
                       return `<li><i class="fas fa-times"></i> ${word} ${correction ? '→ <strong>' + correction + '</strong>' : ''} ${type ? '<span style="color:var(--gray-500)">(' + type + ')</span>' : ''}</li>`;
                   }).join('')}
                </ul>
            </div>
        `;
    }

    // Warning banners for copied / off-topic
    let warningHtml = '';
    if (feedback.is_copied) {
        warningHtml = `<div style="background:var(--danger-light, #fee2e2);color:var(--danger);padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem;">
            <i class="fas fa-copy"></i> ${feedback.general}
        </div>`;
    } else if (feedback.is_off_topic) {
        warningHtml = `<div style="background:#fef9c3;color:#92400e;padding:.75rem 1rem;border-radius:.5rem;margin-bottom:1rem;">
            <i class="fas fa-exclamation-triangle"></i> ${feedback.general}
        </div>`;
    }

    feedbackContent.innerHTML = `
        ${warningHtml}
        ${!feedback.is_copied && !feedback.is_off_topic ? `<div class="feedback-general">${feedback.general}</div>` : ''}
        ${errorsHtml}
        ${feedback.word_count_feedback ? `<div style="margin-top: 1rem; color: var(--gray-600);"><i class="fas fa-info-circle"></i> ${feedback.word_count_feedback}</div>` : ''}
    `;
    
    // User text display
    const userTextDisplay = document.getElementById('user-text-display');
    const highlighted = (fullResponse && fullResponse.your_text_highlighted) 
                        || result.your_text_highlighted;
    
    if (highlighted) {
        userTextDisplay.innerHTML = highlighted;
    } else {
        userTextDisplay.textContent = userText || 'No text submitted';
    }
    document.getElementById('user-word-count').textContent = `${result.word_count || 0} words`;
    
    // Model answer — hidden by default, with toggle button under user text
    const modelSection = document.getElementById('model-answer-section');
    const toggleBtn = document.getElementById('toggle-model-btn');
    const modelTextDisplay = document.getElementById('model-text-display');
    
    if (modelAnswer) {
        modelTextDisplay.textContent = modelAnswer.text || modelAnswer;
        modelSection.style.display = 'none';
        if (toggleBtn) {
            toggleBtn.style.display = 'inline-flex';
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i> Show Typical Example';
        }
    } else {
        if (toggleBtn) toggleBtn.style.display = 'none';
    }
    
    showResults(isReviewMode);
}
function toggleModelAnswer() {
    const modelSection = document.getElementById('model-answer-section');
    const toggleBtn = document.getElementById('toggle-model-btn');
    
    if (modelSection.style.display === 'none' || modelSection.style.display === '') {
        modelSection.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Typical Example';
    } else {
        modelSection.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i> Show Typical Example';
    }
}
// ============================================
// EVENT HANDLERS
// ============================================

async function handleSubmit() {
    if (isSubmitting) return;
    
    const textarea = document.getElementById('writing-textarea');
    const text = textarea.value.trim();
    
    if (!text) {
        alert('Please write something before submitting!');
        return;
    }
    
    const wordCount = text.split(/\s+/).length;
    if (wordCount < 10) {
        alert('Your text is too short. Please write at least 10 words.');
        return;
    }
    
    isSubmitting = true;
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    
    try {
        const response = await submitWriting(currentExercise.id, text, learnerId);
        
        if (response.success) {
            if (response.already_submitted) {
                showAlreadySubmitted(response);
            } else {
                displayResults(response.result, text, currentExercise.model_answer, false, response);
            }
        } else {
            alert('Error: ' + (response.error || 'Failed to submit'));
        }
    } catch (error) {
        console.error('Submit error:', error);
        alert('Failed to submit. Please try again.');
    } finally {
        isSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit';
    }
}

function handleTryAgain() {
    document.getElementById('writing-textarea').value = '';
    updateWordCount();
    showExercise();
}

// ============================================
// INITIALIZATION
// ============================================

async function init() {
    // Get URL parameters
    const { subunit, title, subunitId } = getUrlParams();
    currentSubunit = subunit;
    
    // Get learner ID from localStorage
    learnerId = localStorage.getItem('learner_id');
    
    // Update header
    updateHeader(subunit, title);
    
    // Setup back button
    document.getElementById('back-btn').href = `/exercise-menu/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
    
    // Setup event listeners
    document.getElementById('writing-textarea').addEventListener('input', updateWordCount);
    document.getElementById('submit-btn').addEventListener('click', handleSubmit);
    
    const generateBtn = document.getElementById('generate-exercise-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            console.log('Generate another exercise - à implémenter');
            // TODO: Implémenter ici
        });
    }
    
    if (!subunitId) {
        alert('No subunit specified!');
        return;
    }
    
    showLoading();
    
    try {
        // Fetch exercise
        const exercise = await fetchExercise(subunitId);
        renderExercise(exercise);
        
        // Check for existing result
        if (learnerId) {
            const existingResult = await checkExistingResult(exercise.id, learnerId);
            if (existingResult) {
                showAlreadySubmitted(existingResult);
                hideLoading();
                return;
            }
        }
        
        showExercise();
        
    } catch (error) {
        alert('Failed to load exercise: ' + error.message);
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);