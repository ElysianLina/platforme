// ============================================
// CONFIGURATION PAGE JAVASCRIPT
// For Django EnglishLearn Platform
// ============================================

// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye-slash';
    }
}

async function saveAccount() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const countryCode = document.getElementById('country-code').value;
    const phone = document.getElementById('phone').value.trim();
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    const isGoogleAccount = localStorage.getItem('is_google_account') === 'true';

    // Pour les comptes normaux seulement
    const currentPasswordInput = document.getElementById('current-password');
    const currentPassword = (!isGoogleAccount && currentPasswordInput)
        ? currentPasswordInput.value
        : '';

    // ── Validation champs de base ──────────────
    if (!username || !email) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }

    // ── Validation mot de passe ────────────────
    if (newPassword || confirmPassword || currentPassword) {
        // Compte normal : current password obligatoire
        if (!isGoogleAccount && !currentPassword) {
            showNotification('Please enter your current password', 'error');
            return;
        }
        if (newPassword !== confirmPassword) {
            showNotification('New passwords do not match', 'error');
            return;
        }
        if (newPassword.length < 8) {
            showNotification('New password must be at least 8 characters', 'error');
            return;
        }
    }

    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) {
        showNotification('Session expired, please log in again', 'error');
        return;
    }

    // ── Appel API ──────────────────────────────
    try {
        const response = await fetch('/api/account/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                learner_id:       learnerId,
                username:         username,
                email:            email,
                phone:            phone ? (countryCode + phone) : '',
                current_password: currentPassword,
                new_password:     newPassword,
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Account information saved successfully!', 'success');

            // Mettre à jour l'affichage
            const initials = data.learner.name.slice(0, 2).toUpperCase();
            document.getElementById('avatar-initials').textContent = initials;
            document.getElementById('dropdown-avatar-initials').textContent = initials;
            document.getElementById('dropdown-name').textContent = data.learner.name;
            document.getElementById('dropdown-email').textContent = data.learner.email;

            // Vider les champs password
            if (!isGoogleAccount && currentPasswordInput) {
                currentPasswordInput.value = '';
            }
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-password').value = '';

        } else {
            const errorMsg = data.errors ? data.errors.join(', ') : 'An error occurred';
            showNotification(errorMsg, 'error');
        }

    } catch (error) {
        console.error('Error saving account:', error);
        showNotification('Network error, please try again', 'error');
    }
}

// Start assessment test
async function startAssessment() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) {
        showNotification('Session expired, please log in again', 'error');
        return;
    }

    const confirmed = confirm('You are about to start the English Assessment Test. This will take approximately 15-20 minutes. Do you want to continue?');
    if (!confirmed) return;

    try {
        const response = await fetch('/api/test/demarrer/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ learner_id: learnerId })
        });

        const data = await response.json();
        const testId = data.test_id;

        if (!testId) {
            showNotification('Unable to start the test, please try again', 'error');
            return;
        }

        localStorage.setItem('current_test_id', testId);
        // ✅ Rediriger vers la nouvelle page dédiée
        window.location.href = `/assessment/?test_id=${testId}&learner_id=${learnerId}`;

    } catch (error) {
        console.error('Error starting assessment:', error);
        showNotification('Network error, please try again', 'error');
    }
}

// Delete account with double confirmation
async function deleteAccount() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) {
        showNotification('Session expired, please log in again', 'error');
        return;
    }

    // 1ère confirmation
    const warningMessage = 'WARNING: This action cannot be undone.\n\n' +
        'Deleting your account will:\n' +
        '- Remove all your personal data\n' +
        '- Delete your learning progress\n' +
        '- Cancel any active subscriptions\n\n' +
        'Are you absolutely sure you want to delete your account?';

    if (!confirm(warningMessage)) {
        showNotification('Account deletion cancelled', 'info');
        return;
    }

    // 2ème confirmation — taper DELETE
    const secondConfirm = prompt('Please type "DELETE" to confirm account deletion:');
    if (secondConfirm !== 'DELETE') {
        showNotification('Account deletion cancelled - confirmation text did not match', 'error');
        return;
    }

    // ── Appel API ──────────────────────────────
    try {
        const response = await fetch('/api/account/delete/', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ learner_id: learnerId })
        });

        const data = await response.json();

        if (data.success) {
            // Nettoyer le localStorage
            localStorage.clear();

            showNotification('Account deleted successfully. Redirecting...', 'success');

            // Rediriger vers login après 2 secondes
            setTimeout(() => {
                window.location.href = '/login/';
            }, 2000);

        } else {
            const errorMsg = data.errors ? data.errors.join(', ') : 'An error occurred';
            showNotification(errorMsg, 'error');
        }

    } catch (error) {
        console.error('Error deleting account:', error);
        showNotification('Network error, please try again', 'error');
    }
}

// Show notification toast
function showNotification(message, type = 'info') {
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Get CSRF token from cookies (for Django)
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

// Initialize profile dropdown
function initProfileDropdown() {
    const trigger = document.getElementById('profile-trigger');
    const dropdown = document.getElementById('profile-dropdown');

    if (!trigger || !dropdown) return;

    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });

    document.addEventListener('click', function(e) {
        if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
}

// Initialize tab switching
function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));

            // Add active to clicked tab
            this.classList.add('active');

            const tabName = this.getAttribute('data-tab');
            console.log('Switching to tab:', tabName);

            // TODO: Show corresponding tab content
            // For now only account tab is implemented
        });
    });
}

// Initialize form validation
function initFormValidation() {
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (this.value && !emailRegex.test(this.value)) {
                this.style.borderColor = '#dc3545';
            } else {
                this.style.borderColor = '#ddd';
            }
        });
    }

    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-password');

    function checkPasswordMatch() {
        if (confirmPassword && newPassword && confirmPassword.value && newPassword.value !== confirmPassword.value) {
            confirmPassword.style.borderColor = '#dc3545';
        } else if (confirmPassword) {
            confirmPassword.style.borderColor = '#ddd';
        }
    }

    if (newPassword) {
        newPassword.addEventListener('input', checkPasswordMatch);
    }
    if (confirmPassword) {
        confirmPassword.addEventListener('input', checkPasswordMatch);
    }
}

function updatePreferences() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) {
        showNotification('Session expired, please log in again', 'error');
        return;
    }
    window.location.href = `/update-preferences/?learner_id=${learnerId}`;
}

// Remplacer la fonction loadUserData() complète par :

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
            
            // ── IMPORTANT : Mettre à jour nom/email AVANT la photo ───────────
            if (dropdownName) dropdownName.textContent = learner.name || '--';
            if (dropdownEmail) dropdownEmail.textContent = learner.email || '--';
            
            // ── Avatar image si disponible (GOOGLE) ───────────
            if (learner.picture) {
                const avatarImg = document.getElementById('avatar-img');
                const dropdownAvatarImg = document.getElementById('dropdown-avatar-img');
                
                if (avatarImg) {
                    avatarImg.src = learner.picture;
                    avatarImg.style.display = 'block';
                }
                if (dropdownAvatarImg) {
                    dropdownAvatarImg.src = learner.picture;
                    dropdownAvatarImg.style.display = 'block';
                }
                
                // Cacher SEULEMENT les initials, pas les autres éléments
                if (avatarInitials) avatarInitials.style.display = 'none';
                if (dropdownAvatarInitials) dropdownAvatarInitials.style.display = 'none';
            }
            
            // ── Badge niveau CEFR ──────────────────────
            const levelBadge = document.querySelector('.level-badge');
            if (levelBadge) {
                levelBadge.textContent = `CEFR Level: ${learner.cefr_level || '--'}`;
            }
            
            // ── Pré-remplir le formulaire ──────────────
            const usernameInput = document.getElementById('username');
            const emailInput = document.getElementById('email');
            const phoneInput = document.getElementById('phone');

            if (usernameInput) usernameInput.value = learner.name || '';
            if (emailInput) emailInput.value = learner.email || '';
            if (phoneInput && learner.phone) phoneInput.value = learner.phone;

            // ── Gestion compte Google ──────────────────
            if (learner.is_google_account) {
                localStorage.setItem('is_google_account', 'true');
                const currentPasswordInput = document.getElementById('current-password');
                if (currentPasswordInput) {
                    const currentPasswordGroup = currentPasswordInput.closest('.form-group');
                    if (currentPasswordGroup) currentPasswordGroup.style.display = 'none';
                }
                const passwordSection = document.querySelector('.change-password-section');
                if (passwordSection && !passwordSection.querySelector('.google-account-info')) {
                    const info = document.createElement('p');
                    info.className = 'google-account-info';
                    info.style.cssText = 'color: #666; font-size: 0.85rem; margin-bottom: 12px;';
                    info.textContent = '🔒 You signed in with Google. You can set a password below to also enable email login.';
                    passwordSection.prepend(info);
                }
            } else {
                localStorage.setItem('is_google_account', 'false');
            }
        }
    } catch (error) {
        console.error('Error loading learner data:', error);
    }
}


// Handle Enter key in forms
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        const formGroups = document.querySelectorAll('.form-group input');
        const currentIndex = Array.from(formGroups).indexOf(e.target);

        if (currentIndex < formGroups.length - 1) {
            formGroups[currentIndex + 1].focus();
        } else {
            saveAccount();
        }
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Configuration page loaded');

    initProfileDropdown();
    initTabs();
    initFormValidation();
    loadUserData();
});