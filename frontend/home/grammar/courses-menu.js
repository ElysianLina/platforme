/**
 * courses-menu.js - Grammar Courses Menu
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // PROFILE DROPDOWN
    // ============================================
    
    const profileTrigger = document.getElementById('profile-trigger');
    const profileDropdown = document.getElementById('profile-dropdown');
    
    if (profileTrigger && profileDropdown) {
        profileTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle('active');
        });
        
        document.addEventListener('click', function(e) {
            if (!profileDropdown.contains(e.target) && !profileTrigger.contains(e.target)) {
                profileDropdown.classList.remove('active');
            }
        });
    }
    
    // ============================================
    // LOAD USER DATA — CORRIGÉ (comme configuration.js)
    // ============================================
    
    async function loadUserData() {
        const learnerId = localStorage.getItem('learner_id');
        
        if (!learnerId) {
            console.log('No learner_id found in localStorage');
            return;
        }
        
        try {
            const response = await fetch(`/api/learner/?learner_id=${learnerId}`);
            const data = await response.json();
            
            if (data.success && data.learner) {
                const learner = data.learner;
                
                // ── Avatar & infos dropdown ────────────────
                const initials = learner.name ? learner.name.slice(0, 2).toUpperCase() : '--';
                
                const avatarInitials = document.getElementById('avatar-initials');
                const dropdownAvatarInitials = document.getElementById('dropdown-avatar-initials');
                const dropdownName = document.getElementById('dropdown-name');
                const dropdownEmail = document.getElementById('dropdown-email');
                
                if (avatarInitials) avatarInitials.textContent = initials;
                if (dropdownAvatarInitials) dropdownAvatarInitials.textContent = initials;
                if (dropdownName) dropdownName.textContent = learner.name || '--';
                if (dropdownEmail) dropdownEmail.textContent = learner.email || '--';
                
                // ── Badge niveau CEFR ──────────────────────
                const levelBadge = document.querySelector('.level-badge');
                if (levelBadge) {
                    levelBadge.textContent = `CEFR Level: ${learner.cefr_level || '--'}`;
                }
                
                // ── Avatar image si disponible ───────────
                if (learner.picture) {
                    const avatarImgs = document.querySelectorAll('#avatar-img, #dropdown-avatar-img');
                    avatarImgs.forEach(img => {
                        img.src = learner.picture;
                        img.style.display = 'block';
                    });
                    if (avatarInitials) avatarInitials.style.display = 'none';
                    if (dropdownAvatarInitials) dropdownAvatarInitials.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading learner data:', error);
        }
    }
    
    // ============================================
    // LOAD COURSE PROGRESS
    // ============================================
    
    async function loadCourseProgress() {
        try {
            const response = await fetch('/api/grammar-progress/', {
                credentials: 'include'
            });
            
            if (!response.ok) return;
            
            const progressData = await response.json();
            
            progressData.courses?.forEach(course => {
                const card = document.querySelector(`[data-course="${course.id}"]`);
                if (card) {
                    const fill = card.querySelector('.progress-fill');
                    const text = card.querySelector('.progress-text');
                    
                    if (fill) fill.style.width = `${course.progress}%`;
                    if (text) text.textContent = `${course.progress}% completed`;
                }
            });
            
        } catch (error) {
            console.log('No progress data available');
        }
    }
    
    // ============================================
    // LOGOUT
    // ============================================
    
    const logoutItem = document.querySelector('[data-action="logout"]');
    if (logoutItem) {
        logoutItem.addEventListener('click', async function(e) {
            e.preventDefault();
            
            try {
                const response = await fetch('/api/logout/', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                
                if (response.ok) {
                    localStorage.clear();
                    window.location.href = '/login/';
                }
            } catch (error) {
                console.error('Logout error:', error);
            }
        });
    }
    
    // ============================================
    // UTILS
    // ============================================
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // ============================================
    // ANIMATIONS
    // ============================================
    
    function animateCards() {
        const cards = document.querySelectorAll('.course-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    // ============================================
    // INIT
    // ============================================
    
    loadUserData();
    loadCourseProgress();
    animateCards();
    initCourseLinks();
    
});

// ============================================
// COURSE CARD NAVIGATION
// ============================================

function initCourseLinks() {
    // Map data-course attribute → URL
    const courseRoutes = {
        '1': '/grammar/course-1/',   // Building Sentences in English
        '2': '/grammar/course-2/',  // Word Order — à activer quand disponible
        // '3': '/grammar/course-3/',  // Possessive Adjectives
    };

    document.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('click', function(e) {
            e.preventDefault();
            const courseId = this.dataset.course;
            const url      = courseRoutes[courseId];
            if (url) {
                window.location.href = url;
            } else {
                showComingSoon(this);
            }
        });
    });
}

function showComingSoon(card) {
    // Visual feedback for unavailable courses
    const existing = card.querySelector('.coming-soon-msg');
    if (existing) return;

    const msg = document.createElement('div');
    msg.className = 'coming-soon-msg';
    msg.style.cssText = 'position:absolute;bottom:1rem;right:1rem;background:#1a1a2e;color:#fff;font-size:.75rem;font-weight:600;padding:.3rem .7rem;border-radius:8px;z-index:10;pointer-events:none';
    msg.textContent = 'Coming soon';
    card.style.position = 'relative';
    card.appendChild(msg);
    setTimeout(() => msg.remove(), 2000);
}