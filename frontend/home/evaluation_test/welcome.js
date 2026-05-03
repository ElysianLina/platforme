// ============================================
// welcome.js - Evaluation Test Welcome Page
// ============================================

const API_BASE = 'http://localhost:8000';
const UNLOCK_THRESHOLD = 0;

const userState = {
    learnerId: null,
    progress: 0,
    cefrLevel: ''
};

document.addEventListener('DOMContentLoaded', function() {
    getLearnerId();
    fetchLearnerData();
    initNavigation();
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
            return;
        }
    }

    window.location.href = '/login/';
}

// ============================================
// FETCH LEARNER DATA
// ============================================

async function fetchLearnerData() {
    if (!userState.learnerId) return;

    try {
        const response = await fetch(`${API_BASE}/api/learner/?learner_id=${userState.learnerId}`);
        const result = await response.json();

        if (result.success) {
            const learner = result.learner;
            userState.progress = learner.progress || 0;
            userState.cefrLevel = learner.cefr_level || '';

            updateUI();
        }
    } catch (error) {
        console.error('Error fetching learner data:', error);
        // Fallback to localStorage
        const storedProgress = localStorage.getItem('learner_progress');
        if (storedProgress) {
            userState.progress = parseInt(storedProgress) || 0;
            updateUI();
        }
    }
}

// ============================================
// UPDATE UI
// ============================================

function updateUI() {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressHint = document.getElementById('progress-hint');
   
    const ctaButton = document.getElementById('cta-button');
    const welcomeContainer = document.querySelector('.welcome-container');
    const lockIcon = document.querySelector('.lock-icon i');

    // Update progress bar
    const progress = Math.min(userState.progress, 100);
    progressBar.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;

    // Check if unlocked
    const isUnlocked = progress >= UNLOCK_THRESHOLD;

    if (isUnlocked) {
        // Unlocked state
        progressBar.classList.add('complete');
        progressHint.textContent = 'Congratulations! You can now take the evaluation test.';
        progressHint.style.color = '#48bb78';
        progressHint.style.fontWeight = '600';



        ctaButton.disabled = false;
        ctaButton.innerHTML = '<i class="fas fa-play"></i> Start Evaluation Test';

        welcomeContainer.classList.add('unlocked');

        // Change lock icon to unlock
        lockIcon.classList.remove('fa-lock');
        lockIcon.classList.add('fa-lock-open');

    } else {
        // Locked state
        const remaining = UNLOCK_THRESHOLD - progress;
        progressHint.textContent = `You need ${remaining}% more to unlock the evaluation test.`;



        ctaButton.disabled = true;
        ctaButton.innerHTML = '<i class="fas fa-lock"></i> Locked - Keep Learning!';
    }
}

// ============================================
// NAVIGATION
// ============================================

function initNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') return;
            e.preventDefault();
        });
    });

    // CTA button click
    const ctaButton = document.getElementById('cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            if (!this.disabled) {
                // Redirect to the actual test page
                window.location.href = '/evaluation-test/take/';
            }
        });
    }
}