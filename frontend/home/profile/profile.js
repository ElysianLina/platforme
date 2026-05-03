// ============================================================
// profile.js — Profile page functionality
// ============================================================

const API_BASE = 'http://localhost:8000';

const state = {
    learnerId: null,
    name: '',
    email: '',
    location: 'Algeria',
    countryCode: 'dz',
    progress: 30,
    picture: null,
};

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    if (!getLearnerId()) return;
    fetchProfile();
    bindEvents();
    console.log('Profile page loaded');
});

// ── Get learner_id ──────────────────────────────────────────
function getLearnerId() {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = params.get('learner_id');

    if (fromUrl && fromUrl !== 'null' && fromUrl !== 'undefined') {
        localStorage.setItem('learner_id', fromUrl);
        window.history.replaceState({}, '', window.location.pathname);
    }

    const id = localStorage.getItem('learner_id');
    if (!id || id === 'null' || id === 'undefined') {
        window.location.href = `${API_BASE}/login/`;
        return null;
    }

    state.learnerId = parseInt(id);
    return state.learnerId;
}

// ============================================================
// FETCH PROFILE
// ============================================================
async function fetchProfile() {
    try {
        const res = await fetch(`${API_BASE}/api/learner/?learner_id=${state.learnerId}`);
        const data = await res.json();

        if (!data.success) {
            console.error('Failed to load profile');
            return;
        }

        const l = data.learner;

        state.name = l.name || '';
        state.email = l.email || '';
        state.picture = l.picture || null;
        state.progress = l.progress ;

        if (l.country) {
            state.countryCode = l.country.toLowerCase();
            state.location = l.country;
        }

        renderProfile();
        updateMasteryChart(state.progress);

    } catch (err) {
        console.error('fetchProfile error:', err);
    }
}

// ============================================================
// RENDER PROFILE
// ============================================================
function renderProfile() {
    // Avatar
    const img = document.getElementById('avatar-img');
    const initials = document.getElementById('avatar-initials');

    if (state.picture) {
        img.src = state.picture;
        img.style.display = 'block';
        initials.style.display = 'none';
        img.onerror = () => {
            img.style.display = 'none';
            initials.style.display = 'flex';
            initials.textContent = getInitials(state.name);
        };
    } else {
        img.style.display = 'none';
        initials.style.display = 'flex';
        initials.textContent = getInitials(state.name);
    }

    // Name and location
    document.getElementById('profile-name').textContent = state.name || 'User';
    document.getElementById('location-text').textContent = state.location;

    // Flag
    const flagImg = document.getElementById('country-flag');
    flagImg.src = `https://flagcdn.com/w40/${state.countryCode}.png`;
    flagImg.alt = state.location;
}

// ============================================================
// UPDATE MASTERY CHART
// ============================================================
function updateMasteryChart(percentage) {
    const circle = document.querySelector('.circle-progress');
    const valueEl = document.getElementById('mastery-value');

    if (!circle || !valueEl) return;

    const radius = 54;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = offset;
    valueEl.textContent = percentage;
}

// ============================================================
// BIND EVENTS
// ============================================================
function bindEvents() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            // Update active tab button
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update active content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });
}

// ============================================================
// HELPERS
// ============================================================
function getInitials(name) {
    if (!name) return '?';
    return name.trim().split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
}