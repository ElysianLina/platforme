// ============================================
// evaluation_test.js - Evaluation Test Page
// ============================================

const API_BASE = 'http://localhost:8000';
const userState = {
    learnerId: null,
    cefrLevel: 'A1',
    attemptId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: {},
    timerInterval: null,
    timeRemaining: 0,
    totalTime: 0
};

document.addEventListener('DOMContentLoaded', function() {
    getLearnerId();
    initNavigation();
    loadTestInfo();
    setupEventListeners();
});

// ============================================
// LEARNER ID
// ============================================

function getLearnerId() {
    const urlParams = new URLSearchParams(window.location.search);
    let idFromUrl = urlParams.get('learner_id');

    if (idFromUrl && idFromUrl !== 'null' && idFromUrl !== 'undefined' && idFromUrl.trim() !== '') {
        localStorage.setItem('learner_id', idFromUrl);
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    const storedId = localStorage.getItem('learner_id');
    if (storedId && storedId !== 'null' && storedId !== 'undefined' && storedId.trim() !== '') {
        const parsedId = parseInt(storedId);
        if (!isNaN(parsedId) && parsedId > 0) {
            userState.learnerId = parsedId;
            fetchLearnerData();
            return;
        }
    }

    window.location.href = '/login/';
}

async function fetchLearnerData() {
    if (!userState.learnerId) return;
    try {
        const response = await fetch(`${API_BASE}/api/learner/?learner_id=${userState.learnerId}`);
        const result = await response.json();
        if (result.success) {
            userState.cefrLevel = result.learner.cefr_level || 'A1';
            document.getElementById('level-badge').textContent = userState.cefrLevel;
        }
    } catch (error) {
        console.error('Error fetching learner data:', error);
    }
}

// ============================================
// LOAD TEST INFO
// ============================================

async function loadTestInfo() {
    try {
        const response = await fetch(`${API_BASE}/api/evaluation-test/?level=${userState.cefrLevel}`);
        const result = await response.json();
        
        if (result.success) {
            const test = result.test;
            document.getElementById('time-limit').textContent = `${test.time_limit_minutes} min`;
            document.getElementById('total-questions').textContent = test.total_questions;
            document.getElementById('passing-score').textContent = `${test.passing_score}%`;
            userState.totalTime = test.time_limit_minutes * 60;
            userState.timeRemaining = userState.totalTime;
        }
    } catch (error) {
        console.error('Error loading test info:', error);
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    document.getElementById('start-btn').addEventListener('click', startTest);
    document.getElementById('prev-btn').addEventListener('click', goToPrevious);
    document.getElementById('next-btn').addEventListener('click', goToNext);
    document.getElementById('finish-btn').addEventListener('click', finishTest);
    document.getElementById('retry-btn').addEventListener('click', retryTest);
    document.getElementById('home-btn').addEventListener('click', () => {
        window.location.href = '/';
    });
}

// ============================================
// START TEST
// ============================================

async function startTest() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/evaluation-start/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level: userState.cefrLevel,
                learner_id: userState.learnerId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            userState.attemptId = result.attempt_id;
            
            const testResponse = await fetch(`${API_BASE}/api/evaluation-test/?level=${userState.cefrLevel}`);
            const testResult = await testResponse.json();
            
            if (testResult.success) {
                userState.questions = testResult.questions;
                showScreen('quiz-screen');
                startTimer();
                renderQuestion(0);
            }
        } else {
            alert(result.error || 'Failed to start test');
        }
    } catch (error) {
        console.error('Error starting test:', error);
        alert('Failed to start test. Please try again.');
    } finally {
        showLoading(false);
    }
}

// ============================================
// TIMER
// ============================================

function startTimer() {
    updateTimerDisplay();
    userState.timerInterval = setInterval(() => {
        userState.timeRemaining--;
        updateTimerDisplay();
        
        if (userState.timeRemaining <= 0) {
            clearInterval(userState.timerInterval);
            finishTest();
        }
        
        if (userState.timeRemaining <= 60) {
            document.getElementById('timer').classList.add('warning');
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(userState.timeRemaining / 60);
    const seconds = userState.timeRemaining % 60;
    document.getElementById('timer-display').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// ============================================
// RENDER QUESTION
// ============================================

function renderQuestion(index) {
    userState.currentQuestionIndex = index;
    const question = userState.questions[index];
    const container = document.getElementById('question-container');
    
    const progress = ((index + 1) / userState.questions.length) * 100;
    document.getElementById('quiz-progress-bar').style.width = `${progress}%`;
    document.getElementById('progress-text').textContent = 
        `Question ${index + 1} / ${userState.questions.length}`;
    
    let html = `<div class="question-section-badge">${getSectionLabel(question.section)}</div>`;
    
    if (question.reading) {
        html += `<div class="question-reading">${escapeHtml(question.reading)}</div>`;
    }
    
    if (question.image) {
        html += `
            <div class="question-image-wrapper">
                <img src="${question.image}" alt="Question image" class="question-image">
            </div>
        `;
    }
    
    if (question.audio) {
        const ext = question.audio.split('.').pop().toLowerCase();
        const mimeType = ext === 'wav' ? 'audio/wav' : 
                         ext === 'ogg' ? 'audio/ogg' : 
                         ext === 'webm' ? 'audio/webm' : 'audio/mpeg';
        
        const audioUrl = question.audio.startsWith('http') 
            ? question.audio 
            : `${API_BASE}${question.audio}`;
        
        html += `
            <div class="question-audio">
                <audio controls class="audio-player" preload="auto">
                    <source src="${audioUrl}" type="${mimeType}">
                    Your browser does not support the audio element.
                </audio>
            </div>
        `;
    }
    
    html += `<div class="question-text">${escapeHtml(question.text)}</div>`;
    
    // 🔥 RÉCUPÉRER LA RÉPONSE SAUVEGARDÉE (texte, pas lettre)
    let savedAnswer = userState.answers[question.id] || '';
    if (typeof savedAnswer === 'string' && savedAnswer.includes('|')) {
        savedAnswer = savedAnswer.split('|');
    }
    
    if (question.type === 'mcq' && question.options) {
        html += '<div class="choices-container">';
        question.options.forEach((opt, idx) => {
            const letter = String.fromCharCode(65 + idx);
            
            // 🔥 NETTOYER LE TEXTE DE L'OPTION
            let cleanOpt = opt;
            if (typeof opt === 'object' && opt.text) {
                cleanOpt = opt.text;
            }
            const prefixPatterns = [
                /^\s*[A-Da-d][\.:\)]\s*/,
                /^\s*\d+[\.\)]\s*/,
                /^\s*[A-Da-d]\s+/,
            ];
            for (const pattern of prefixPatterns) {
                cleanOpt = cleanOpt.replace(pattern, '');
            }
            cleanOpt = cleanOpt.trim();
            
            // 🔥 VÉRIFIER SI CETTE OPTION EST SÉLECTIONNÉE (comparer le texte)
            const isSelected = (savedAnswer === cleanOpt);
            
            html += `
                <div class="choice-item ${isSelected ? 'selected' : ''}" 
                     data-value="${escapeHtml(cleanOpt)}" 
                     data-letter="${letter}"
                     onclick="selectChoice('${letter}', '${escapeHtml(cleanOpt)}')">
                    <span class="choice-letter">${letter}</span>
                    <span class="choice-text">${escapeHtml(cleanOpt)}</span>
                </div>
            `;
        });
        html += '</div>';
    } else if (question.type === 'true_false') {
        html += `
            <div class="true-false-container">
                <button class="tf-btn ${savedAnswer === 'True' ? 'selected' : ''}" 
                        onclick="selectTrueFalse('True')">
                    <i class="fas fa-check"></i> True
                </button>
                <button class="tf-btn ${savedAnswer === 'False' ? 'selected' : ''}" 
                        onclick="selectTrueFalse('False')">
                    <i class="fas fa-times"></i> False
                </button>
            </div>
        `;
    } else if (question.type === 'fill_blank') {
        const blankMatches = question.text.match(/_{2,}/g);
        const blankCount = blankMatches ? blankMatches.length : 1;
        
        html += '<div class="blanks-container">';
        
        for (let i = 0; i < blankCount; i++) {
            const savedValue = (savedAnswer && savedAnswer[i]) ? savedAnswer[i] : '';
            html += `
                <div class="blank-item">
                    <label class="blank-label">Answer ${blankCount > 1 ? (i + 1) : ''}</label>
                    <input type="text" class="blank-input" 
                           id="blank-answer-${i}" 
                           placeholder="Type your answer here..." 
                           value="${escapeHtml(savedValue)}"
                           data-index="${i}"
                           onchange="saveBlankAnswer(this.value, ${i})">
                </div>
            `;
        }
        html += '</div>';
    }
    
    container.innerHTML = html;
    
    document.getElementById('prev-btn').disabled = index === 0;
    
    const isLast = index === userState.questions.length - 1;
    const hasAnswered = hasAnsweredQuestion(question);
    
    if (isLast) {
        document.getElementById('next-btn').classList.add('hidden');
        document.getElementById('finish-btn').classList.toggle('hidden', !hasAnswered);
    } else {
        document.getElementById('next-btn').classList.toggle('hidden', !hasAnswered);
        document.getElementById('finish-btn').classList.add('hidden');
    }
}

function hasAnsweredQuestion(question) {
    const answer = userState.answers[question.id];
    
    if (answer === undefined || answer === null || answer === '') {
        return false;
    }
    
    if (question.type === 'fill_blank') {
        let answerArray;
        if (Array.isArray(answer)) {
            answerArray = answer;
        } else if (typeof answer === 'string' && answer.includes('|')) {
            answerArray = answer.split('|');
        } else {
            answerArray = [answer];
        }
        
        const blankMatches = question.text.match(/_{2,}/g);
        const blankCount = blankMatches ? blankMatches.length : 1;
        
        if (answerArray.length < blankCount) {
            return false;
        }
        
        return answerArray.every(v => v !== undefined && v !== null && v.toString().trim() !== '');
    }
    
    return true;
}

function showNextButton() {
    const isLast = userState.currentQuestionIndex === userState.questions.length - 1;
    
    if (isLast) {
        document.getElementById('finish-btn').classList.remove('hidden');
    } else {
        document.getElementById('next-btn').classList.remove('hidden');
    }
}

function getSectionLabel(section) {
    const labels = {
        'listening': 'Listening Comprehension',
        'reading': 'Reading Comprehension',
        'visual': 'Visual Comprehension',
        'grammar': 'Grammar',
        'vocabulary': 'Vocabulary'
    };
    return labels[section] || section;
}

// ============================================
// ANSWER HANDLING — 🔥 CORRIGÉ : ENVOIE LE TEXTE
// ============================================

function selectChoice(letter, answerText) {
    const question = userState.questions[userState.currentQuestionIndex];
    
    // 🔥 SAUVEGARDER LE TEXTE DE LA RÉPONSE, PAS LA LETTRE
    userState.answers[question.id] = answerText;
    
    // Update UI
    document.querySelectorAll('.choice-item').forEach(item => {
        item.classList.toggle('selected', item.dataset.value === answerText);
    });
    
    showNextButton();
    
    // 🔥 ENVOYER LE TEXTE AU SERVEUR
    saveAnswer(question.id, answerText);
}

function selectTrueFalse(value) {
    const question = userState.questions[userState.currentQuestionIndex];
    userState.answers[question.id] = value;
    
    document.querySelectorAll('.tf-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.closest('.tf-btn').classList.add('selected');
    
    showNextButton();
    saveAnswer(question.id, value);
}

function saveBlankAnswer(value, index = 0) {
    const question = userState.questions[userState.currentQuestionIndex];
    
    if (!Array.isArray(userState.answers[question.id])) {
        userState.answers[question.id] = [];
    }
    
    userState.answers[question.id][index] = value;
    
    const blankMatches = question.text.match(/_{2,}/g);
    const blankCount = blankMatches ? blankMatches.length : 1;
    const currentAnswers = userState.answers[question.id];
    
    const allFilled = currentAnswers.length >= blankCount && 
                      currentAnswers.every(v => v !== undefined && v !== null && v.toString().trim() !== '');
    
    if (allFilled) {
        const answerString = currentAnswers.join('|');
        saveAnswer(question.id, answerString);
        showNextButton();
    }
}

async function saveAnswer(questionId, answer) {
    if (!userState.attemptId) return;
    
    try {
        await fetch(`${API_BASE}/api/evaluation-answer/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                attempt_id: userState.attemptId,
                question_id: questionId,
                answer: answer,
                learner_id: userState.learnerId
            })
        });
    } catch (error) {
        console.error('Error saving answer:', error);
    }
}

// ============================================
// NAVIGATION
// ============================================

function goToPrevious() {
    if (userState.currentQuestionIndex > 0) {
        renderQuestion(userState.currentQuestionIndex - 1);
    }
}

function goToNext() {
    // Sauvegarder la réponse de la question actuelle avant de partir
    saveCurrentAnswer();
    
    if (userState.currentQuestionIndex < userState.questions.length - 1) {
        renderQuestion(userState.currentQuestionIndex + 1);
    }
}

function saveCurrentAnswer() {
    const question = userState.questions[userState.currentQuestionIndex];
    const answer = userState.answers[question.id];
    
    if (answer !== undefined && answer !== null && answer !== '') {
        if (question.type === 'fill_blank') {
            // S'assurer que la réponse est bien formatée
            let answerToSave = answer;
            if (Array.isArray(answer)) {
                answerToSave = answer.join('|');
            }
            saveAnswer(question.id, answerToSave);
        } else {
            saveAnswer(question.id, answer);
        }
    }
}

// ============================================
// FINISH TEST
// ============================================

async function finishTest() {
    clearInterval(userState.timerInterval);

    // Sauvegarder TOUTES les réponses avant de finir
    for (const question of userState.questions) {
        const answer = userState.answers[question.id];
        if (answer !== undefined && answer !== null && answer !== '') {
            let answerToSave = answer;
            if (question.type === 'fill_blank' && Array.isArray(answer)) {
                answerToSave = answer.join('|');
            }
            await saveAnswer(question.id, answerToSave);
        }
    }
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/evaluation-finish/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                attempt_id: userState.attemptId,
                learner_id: userState.learnerId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResults(result);
        } else {
            alert(result.error || 'Failed to finish test');
        }
    } catch (error) {
        console.error('Error finishing test:', error);
        alert('Failed to submit test. Please try again.');
    } finally {
        showLoading(false);
    }
}

// ============================================
// SHOW RESULTS
// ============================================

function showResults(result) {
    showScreen('results-screen');
    
    const percentage = result.percentage;
    const passed = result.passed;
    
    const circle = document.getElementById('score-circle-progress');
    const circumference = 339.292;
    const offset = circumference - (percentage / 100) * circumference;
    
    const svg = document.querySelector('.score-circle svg');
    if (!svg.querySelector('defs')) {
        svg.innerHTML = `
            <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#4f46e5"/>
                    <stop offset="100%" style="stop-color:#6366f1"/>
                </linearGradient>
            </defs>
        ` + svg.innerHTML;
    }
    
    setTimeout(() => {
        circle.style.strokeDashoffset = offset;
    }, 100);
    
    document.getElementById('score-percentage').textContent = `${percentage}%`;
    
    const statusEl = document.getElementById('result-status');
    const iconEl = document.querySelector('.result-icon');
    
    if (passed) {
        statusEl.className = 'result-status pass';
        statusEl.innerHTML = '<i class="fas fa-check-circle"></i><span>Congratulations! You passed!</span>';
        iconEl.classList.remove('fail');
        document.getElementById('results-title').textContent = 'Test Completed!';
    } else {
        statusEl.className = 'result-status fail';
        statusEl.innerHTML = '<i class="fas fa-times-circle"></i><span>You did not pass. Keep practicing!</span>';
        iconEl.classList.add('fail');
        document.getElementById('results-title').textContent = 'Test Completed';
    }
    
    const sectionsContainer = document.getElementById('section-results');
    const sectionIcons = {
        'listening': 'fa-headphones',
        'reading': 'fa-book-reader',
        'visual': 'fa-eye',
        'grammar': 'fa-spell-check',
        'vocabulary': 'fa-font'
    };
    
    let sectionsHtml = '';
    for (const [section, data] of Object.entries(result.section_results || {})) {
        const sectionPercentage = data.total > 0 ? Math.round((data.correct / data.total) * 100) : 0;
        sectionsHtml += `
            <div class="section-result-item">
                <div class="section-result-name">
                    <i class="fas ${sectionIcons[section] || 'fa-question'}"></i>
                    ${getSectionLabel(section)}
                </div>
                <div class="section-result-score">${data.correct}/${data.total} (${sectionPercentage}%)</div>
            </div>
        `;
    }
    sectionsContainer.innerHTML = sectionsHtml;
}

// ============================================
// RETRY TEST
// ============================================

function retryTest() {
    userState.answers = {};
    userState.currentQuestionIndex = 0;
    userState.attemptId = null;
    userState.timeRemaining = userState.totalTime;
    document.getElementById('timer').classList.remove('warning');
    
    showScreen('start-screen');
    loadTestInfo();
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showScreen(screenId) {
    document.querySelectorAll('.test-container').forEach(el => {
        el.classList.add('hidden');
    });
    document.getElementById(screenId).classList.remove('hidden');
}

function showLoading(show) {
    document.getElementById('loading-overlay').classList.toggle('hidden', !show);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function initNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') return;
            e.preventDefault();
        });
    });
}