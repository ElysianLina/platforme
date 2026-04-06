// ============================================
// home.js - servi par Live Server :8080
// ✅ FIX 1 : récupère learner_id depuis l'URL (?learner_id=...)
//            car localStorage :8000 (login) ≠ localStorage :8080 (home)
// ✅ FIX 2 : learner_id est un entier AutoField (pas UUID)
//            → parseInt est correct ici pour le modèle Learner
// ============================================

const API_BASE = 'http://localhost:8000';

const userState = {
    learnerId: null,
    name: '',
    email: '',
    cefrLevel: '',
    progress: 0
};

let profileTrigger = null;
let profileDropdown = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    getLearnerId();      // ✅ récupère depuis URL ou localStorage
    fetchLearnerData();
    loadUnits();
    initProfileDropdown();
    
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') return;
            e.preventDefault();
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            this.style.transform = 'scale(0.98)';
            setTimeout(() => { this.style.transform = ''; }, 150);
        });
    });

    animateCards();
    console.log('EnglishLearn Dashboard loaded ✅');
});

// ============================================
// LOADING UNITS
// ============================================

async function loadUnits() {
    const unitsContainer = document.querySelector('.units-section');
    
    unitsContainer.innerHTML = `
        <h2 class="section-title">Learning Units</h2>
        <div class="loading-message">
            <i class="fas fa-spinner fa-spin"></i> Loading units...
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/api/units/`);
        const data = await response.json();
        
        console.log("=== API UNITS RESPONSE ===", data);
        
        if (data.success && data.units) {
            renderUnits(data.units);
        } else {
            throw new Error(data.error || 'Loading error');
        }
    } catch (error) {
        console.error('Error loading units:', error);
        unitsContainer.innerHTML = `
            <h2 class="section-title">Learning Units</h2>
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                Unable to load units.
                <button onclick="loadUnits()" style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

function renderUnits(units) {
    const unitsContainer = document.querySelector('.units-section');
    console.log("=== RENDER UNITS ===", units.length, "units");
    
    let html = '<h2 class="section-title">Learning Units</h2>';
    
    if (units.length === 0) {
        html += '<div class="error-message">No units available</div>';
        unitsContainer.innerHTML = html;
        return;
    }
    
    units.forEach((unit, index) => {
        const unitNumber = unit.display_number || String(index + 1).padStart(2, '0');
        
        // CAS 1 : SOUS-UNITÉ UNIQUE → LIEN DIRECT
        if (unit.is_single_subunit === true) {
            const sub = unit.subunit;
            html += `
                <a href="/exercise-menu/?subunit=${sub.code}&title=${encodeURIComponent(sub.title)}&subunit_id=${sub.id}" 
                   class="unit-card single-subunit" 
                   onclick="localStorage.setItem('currentSubunitId', '${sub.id}')"
                   style="text-decoration: none; color: inherit; display: block;">
                    <div class="unit-header" style="cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <div class="unit-info">
                            <div class="unit-icon" style="background: rgba(255,255,255,0.2); color: white;">${unitNumber}</div>
                            <div class="unit-details">
                                <h3>${unit.title}</h3>
                                <p>${sub.title} • Level ${unit.level}</p>
                            </div>
                        </div>
                        <div class="unit-meta">
                            <span class="progress-badge" style="background: rgba(255,255,255,0.2); color: white;">Click to start</span>
                            <i class="fas fa-arrow-right" style="margin-left: 8px;"></i>
                        </div>
                    </div>
                </a>
            `;
            return;
        }
        
        // CAS 2 : PLUSIEURS SOUS-UNITÉS → ACCORDÉON
        const visibleSubunits = unit.subunits || [];
        if (visibleSubunits.length === 0) return;
        
        const subunitsHtml = visibleSubunits.map(sub => `
            <a href="/exercise-menu/?subunit=${sub.code}&title=${encodeURIComponent(sub.title)}&subunit_id=${sub.id}" 
               class="subunit-card"
               onclick="localStorage.setItem('currentSubunitId', '${sub.id}')">
                <div class="subunit-icon">
                    <i class="fas fa-${getIconForSubunit(sub.order)}"></i>
                </div>
                <div class="subunit-info">
                    <h4>Sub-unit ${sub.code}</h4>
                    <p>${sub.title}</p>
                </div>
                <div class="subunit-status pending">
                    <i class="fas fa-circle"></i>
                </div>
            </a>
        `).join('');
        
        html += `
            <div class="unit-card" id="unit-${unit.id}">
                <div class="unit-header" onclick="toggleUnit(this)">
                    <div class="unit-info">
                        <div class="unit-icon">${unitNumber}</div>
                        <div class="unit-details">
                            <h3>${unit.title}</h3>
                            <p>Level ${unit.level} - ${visibleSubunits.length} sub-units</p>
                        </div>
                    </div>
                    <div class="unit-meta">
                        <span class="progress-badge">0/${visibleSubunits.length} completed</span>
                        <i class="fas fa-chevron-down unit-arrow"></i>
                    </div>
                </div>
                <div class="unit-content">
                    <div class="subunits-list">${subunitsHtml}</div>
                </div>
            </div>
        `;
    });
    
    unitsContainer.innerHTML = html;
    console.log("=== RENDER COMPLETE ===");
}

function getIconForSubunit(order) {
    const icons = ['user-circle', 'handshake', 'users', 'comments', 'star', 'heart'];
    return icons[(order - 1) % icons.length] || 'book';
}

// ============================================
// USER FUNCTIONS
// ============================================

function getLearnerId() {
    // Récupérer learner_id depuis l'URL en priorité
    const urlParams = new URLSearchParams(window.location.search);
    let idFromUrl = urlParams.get('learner_id');
    const cefrFromUrl = urlParams.get('cefr_level');
    const nameFromUrl = urlParams.get('name');
    const emailFromUrl = urlParams.get('email');
    
    // ✅ VALIDATION STRICTE : rejeter "null", "undefined", chaîne vide
    if (idFromUrl && idFromUrl !== 'null' && idFromUrl !== 'undefined' && idFromUrl.trim() !== '') {
        console.log('✅ learner_id valide depuis URL:', idFromUrl);
        
        // Stocker dans localStorage pour les prochaines visites
        localStorage.setItem('learner_id', idFromUrl);
        
        // Stocker les autres paramètres avec décodage
        if (nameFromUrl && nameFromUrl !== 'null' && nameFromUrl !== 'undefined') {
            const decodedName = decodeURIComponent(nameFromUrl);
            localStorage.setItem('learner_name', decodedName);
            console.log('✅ name stocké:', decodedName);
        }
        if (emailFromUrl && emailFromUrl !== 'null' && emailFromUrl !== 'undefined') {
            const decodedEmail = decodeURIComponent(emailFromUrl);
            localStorage.setItem('learner_email', decodedEmail);
            console.log('✅ email stocké:', decodedEmail);
        }
        if (cefrFromUrl && cefrFromUrl !== 'null' && cefrFromUrl !== 'undefined') {
            localStorage.setItem('learner_cefr_level', cefrFromUrl);
            console.log('✅ cefr_level stocké:', cefrFromUrl);
        }
        
        // Nettoyer l'URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (idFromUrl) {
        console.warn('⚠️ learner_id invalide dans URL:', idFromUrl);
    }

    // Récupérer depuis localStorage
    const storedId = localStorage.getItem('learner_id');
    const storedName = localStorage.getItem('learner_name');
    const storedEmail = localStorage.getItem('learner_email');
    const storedCefr = localStorage.getItem('learner_cefr_level');
    const storedProgress = localStorage.getItem('learner_progress');
    
    // ✅ VALIDATION : vérifier que storedId est valide
    if (storedId && storedId !== 'null' && storedId !== 'undefined' && storedId.trim() !== '') {
        const parsedId = parseInt(storedId);
        
        // Vérifier que c'est un nombre valide
        if (!isNaN(parsedId) && parsedId > 0) {
            userState.learnerId = parsedId;
            userState.name = storedName || '';
            userState.email = storedEmail || '';
            userState.cefrLevel = storedCefr || '';
            userState.progress = parseInt(storedProgress) || 0;
            
            console.log('📋 Données utilisateur chargées:', userState);
            return userState.learnerId;
        } else {
            console.error('❌ learner_id n\'est pas un nombre valide:', storedId);
        }
    }
    
    console.error('❌ Non connecté, redirection vers login...');
    window.location.href = '/login/';
    return null;
}

async function fetchLearnerData() {
    // ✅ FIX BUG 3 : supprimé le guard "if (userState.name) return"
    // qui affichait les données d'un ancien apprenant depuis le cache localStorage
    // On fait TOUJOURS l'appel API pour avoir les données fraîches du bon apprenant
    if (!userState.learnerId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/learner/?learner_id=${userState.learnerId}`);
        const result = await response.json();
        
        if (result.success) {
            userState.name      = result.learner.name;
            userState.email     = result.learner.email;
            userState.cefrLevel = result.learner.cefr_level;
            userState.progress  = result.learner.progress;
            
            localStorage.setItem('learner_name',       userState.name);
            localStorage.setItem('learner_email',      userState.email);
            localStorage.setItem('learner_cefr_level', userState.cefrLevel);
            localStorage.setItem('learner_progress',   userState.progress);
            
            updateDashboard();
            updateDropdown();
        }
    } catch (error) {
        console.error('Erreur fetchLearnerData:', error);
    }
}

function updateDashboard() {
    const welcomeTitle = document.querySelector('.welcome-title');
    if (welcomeTitle && userState.name) {
        welcomeTitle.textContent = `Welcome, ${userState.name}!`;
    }
    
    const levelBadge = document.querySelector('.level-badge');
    if (levelBadge && userState.cefrLevel) {
        levelBadge.textContent = `CEFR Level: ${userState.cefrLevel}`;
    }
    
    const cefrValue = document.querySelector('.stat-card:nth-child(1) .stat-value');
    if (cefrValue && userState.cefrLevel) {
        cefrValue.textContent = userState.cefrLevel;
    }
    
    const progressValue = document.querySelector('.stat-card:nth-child(2) .stat-value');
    if (progressValue && userState.progress !== undefined) {
        progressValue.textContent = userState.progress + '%';
    }
    
    const avatarInitials = document.getElementById('avatar-initials');
    if (avatarInitials && userState.name) {
        const initials = userState.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        avatarInitials.textContent = initials;
    }
}

function updateDropdown() {
    const dropdownAvatarInitials = document.getElementById('dropdown-avatar-initials');
    const dropdownName  = document.getElementById('dropdown-name');
    const dropdownEmail = document.getElementById('dropdown-email');
    
    if (userState.name) {
        const initials = userState.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        if (dropdownAvatarInitials) dropdownAvatarInitials.textContent = initials;
        if (dropdownName) dropdownName.textContent = userState.name;
    }
    if (userState.email) {
        if (dropdownEmail) dropdownEmail.textContent = userState.email;
    }
}

// ============================================
// PROFILE DROPDOWN
// ============================================

function initProfileDropdown() {
    profileTrigger  = document.getElementById('profile-trigger');
    profileDropdown = document.getElementById('profile-dropdown');
    
    if (!profileTrigger || !profileDropdown) return;
    
    profileTrigger.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleDropdown();
    });
    
    profileDropdown.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleDropdownAction(this.getAttribute('data-action'));
        });
    });
    
    document.addEventListener('click', function(e) {
        if (profileDropdown.classList.contains('show') && 
            !profileDropdown.contains(e.target) && 
            !profileTrigger.contains(e.target)) {
            closeDropdown();
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && profileDropdown.classList.contains('show')) {
            closeDropdown();
        }
    });
}

function toggleDropdown() {
    profileDropdown.classList.contains('show') ? closeDropdown() : openDropdown();
}
function openDropdown()  { profileDropdown.classList.add('show');    profileTrigger.classList.add('active'); }
function closeDropdown() { profileDropdown.classList.remove('show'); profileTrigger.classList.remove('active'); }

function handleDropdownAction(action) {
    closeDropdown();
    switch(action) {
        case 'profile':  showNotification('Redirecting to My Profile...'); break;
        case 'settings': showNotification('Redirecting to Settings...'); break;
        case 'logout':   logout(); break;
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/api/logout/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ learner_id: userState.learnerId })
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        localStorage.removeItem('learner_id');
        localStorage.removeItem('learner_name');
        localStorage.removeItem('learner_email');
        localStorage.removeItem('learner_cefr_level');
        localStorage.removeItem('learner_progress');
        localStorage.removeItem('currentSubunitId');
        // Rediriger vers login sur Django :8000
        window.location.href = 'http://localhost:8000/login/';
    }
}

// ============================================
// UTILITIES
// ============================================

function toggleUnit(header) {
    const unitCard = header.parentElement;
    if (unitCard.classList.contains('locked')) return;

    const isOpen = unitCard.classList.contains('open');

    document.querySelectorAll('.unit-card').forEach(card => {
        card.classList.remove('open');
        const content = card.querySelector('.unit-content');
        if (content) {
            content.style.maxHeight = '0';
            content.style.overflowY = 'hidden';
            content.style.overflowX = 'hidden';
            content.style.padding   = '0 24px';
        }
    });

    if (!isOpen) {
        const content = unitCard.querySelector('.unit-content');
        if (!content) return;
        unitCard.classList.add('open');
        content.style.maxHeight = '400px';
        content.style.overflowY = 'auto';
        content.style.overflowX = 'hidden';
        content.style.padding   = '0 24px 24px 24px';
    }
}

function animateCards() {
    const cards = document.querySelectorAll('.stat-card, .unit-card');
    cards.forEach((card, index) => {
        card.style.opacity   = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity    = '1';
            card.style.transform  = 'translateY(0)';
        }, index * 100);
    });
}

function showNotification(message) {
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