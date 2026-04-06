// reset-password.js — New password confirmation

const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function () {
    const backBtn = document.getElementById('backBtn');
    const resetForm = document.getElementById('resetForm');
    const passwordInput = document.getElementById('passwordInput');
    const confirmInput = document.getElementById('confirmInput');
    const togglePassword = document.getElementById('togglePassword');
    const submitBtn = document.getElementById('submitBtn');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    
    // Récupérer les tokens de l'URL (/reset-password/<uidb64>/<token>/)
    const pathParts = window.location.pathname.split('/');
    const uidb64 = pathParts[pathParts.length - 3];
    const token = pathParts[pathParts.length - 2];
    
    document.getElementById('uidb64').value = uidb64;
    document.getElementById('token').value = token;

    let isLoading = false;

    function showToast(message, type = 'info') {
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // Toggle password visibility
    togglePassword.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        confirmInput.setAttribute('type', type);
        
        // Changer l'icône
        this.innerHTML = type === 'password' 
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
    });

    // Check password strength
    function checkStrength(password) {
        let strength = 0;
        const hasLength = password.length >= 8;
        const hasUpper = /[A-Z]/.test(password);
        const hasLower = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[^A-Za-z0-9]/.test(password);

        if (hasLength) strength++;
        if (hasUpper && hasLower) strength++;
        if (hasNumber) strength++;
        if (hasSpecial) strength++;

        return { strength, hasLength, hasUpper, hasLower, hasNumber, hasSpecial };
    }

    function updateRequirements(checks) {
        const reqs = {
            'req-length': checks.hasLength,
            'req-upper': checks.hasUpper,
            'req-lower': checks.hasLower,
            'req-number': checks.hasNumber
        };

        for (const [id, valid] of Object.entries(reqs)) {
            const el = document.getElementById(id);
            if (valid) {
                el.classList.add('valid');
                el.querySelector('svg').innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
            } else {
                el.classList.remove('valid');
                el.querySelector('svg').innerHTML = '<circle cx="12" cy="12" r="10"></circle>';
            }
        }
    }

    passwordInput.addEventListener('input', function() {
        const { strength, hasLength, hasUpper, hasLower, hasNumber } = checkStrength(this.value);
        
        updateRequirements({ hasLength, hasUpper, hasLower, hasNumber });

        strengthBar.className = 'strength-bar';
        strengthText.className = 'strength-text';

        if (this.value.length === 0) {
            strengthText.textContent = 'Enter at least 8 characters';
            return;
        }

        const levels = ['weak', 'fair', 'good', 'strong'];
        const texts = ['Weak', 'Fair', 'Good', 'Strong'];
        
        const level = Math.min(strength, 3);
        strengthBar.classList.add(levels[level]);
        strengthText.textContent = texts[level];
        strengthText.classList.add(levels[level]);
    });

    // Check password match
    function checkMatch() {
        const matchIndicator = document.getElementById('matchIndicator');
        if (!confirmInput.value) {
            matchIndicator.className = 'match-indicator';
            return;
        }

        if (passwordInput.value === confirmInput.value) {
            matchIndicator.className = 'match-indicator match';
            confirmInput.classList.remove('error');
            confirmInput.classList.add('success');
        } else {
            matchIndicator.className = 'match-indicator mismatch';
            confirmInput.classList.remove('success');
            confirmInput.classList.add('error');
        }
    }

    confirmInput.addEventListener('input', checkMatch);
    passwordInput.addEventListener('input', checkMatch);

    // Back button
    backBtn.addEventListener('click', () => {
        window.location.href = `${API_BASE}/login/`;
    });

    // Form submission
    resetForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (isLoading) return;

        const password = passwordInput.value;
        const confirm = confirmInput.value;

        // Validation
        const checks = checkStrength(password);
        if (!checks.hasLength || !checks.hasUpper || !checks.hasLower || !checks.hasNumber) {
            showToast('Please meet all password requirements', 'error');
            return;
        }

        if (password !== confirm) {
            showToast('Passwords do not match', 'error');
            confirmInput.focus();
            return;
        }

        isLoading = true;
        submitBtn.disabled = true;
        const originalContent = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading"></span> Updating...';

        try {
            const response = await fetch(`${API_BASE}/api/password-reset-confirm/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uidb64: uidb64,
                    token: token,
                    new_password: password
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showToast('✅ Password updated successfully!', 'success');
                setTimeout(() => {
                    window.location.href = `${API_BASE}/login/?reset=success`;
                }, 2000);
            } else {
                const errorMsg = data.message || data.error || 'Invalid or expired link';
                showToast(errorMsg, 'error');
                if (data.error === 'invalid_token') {
                    setTimeout(() => {
                        window.location.href = `${API_BASE}/reset-request/`;
                    }, 3000);
                }
            }
        } catch (error) {
            console.error('Password reset error:', error);
            showToast('Network error. Please try again.', 'error');
        } finally {
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
            isLoading = false;
        }
    });

    // Focus effects
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.01)';
            this.parentElement.style.transition = 'transform 0.2s';
        });
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    console.log('Reset password page initialized ✅');
});