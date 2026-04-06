// reset-request.js — Email-only password reset

const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function () {
    const backBtn = document.getElementById('backBtn');
    const resetForm = document.getElementById('resetForm');
    const emailInput = document.getElementById('emailInput');
    const submitBtn = document.getElementById('submitBtn');

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

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Real-time validation
    emailInput.addEventListener('input', function () {
        const val = this.value.trim();
        if (val === '') {
            this.classList.remove('error', 'success');
            return;
        }
        if (validateEmail(val)) {
            this.classList.remove('error');
            this.classList.add('success');
        } else {
            this.classList.remove('success');
            this.classList.add('error');
        }
    });

    // Back button
    backBtn.addEventListener('click', () => {
        if (document.referrer && document.referrer.includes(location.host)) {
            window.history.back();
        } else {
            window.location.href = `${API_BASE}/login/`;
        }
    });

    // Form submission
    resetForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (isLoading) return;

        const email = emailInput.value.trim();
        if (!email) {
            showToast('Please enter your email address', 'error');
            emailInput.classList.add('error');
            return;
        }
        if (!validateEmail(email)) {
            showToast('Please enter a valid email address (e.g., name@example.com)', 'error');
            emailInput.classList.add('error');
            return;
        }

        isLoading = true;
        submitBtn.disabled = true;
        const originalContent = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="loading"></span> Sending...';

        try {
            const response = await fetch(`${API_BASE}/api/password-reset/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showToast(`✅ Reset link sent to ${email}. Check your inbox.`, 'success');
                emailInput.value = '';
                emailInput.classList.remove('success', 'error');
                setTimeout(() => {
                    window.location.href = `${API_BASE}/login/`;
                }, 2800);
            } else {
                const errorMsg = data.message || data.error || 'Request failed. Please try again.';
                showToast(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Password reset error:', error);
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                console.warn('⚠️ Backend not reachable – simulating reset for UI demo');
                showToast(`🔐 [DEMO] Reset link sent to ${email} (backend not configured)`, 'success');
                setTimeout(() => {
                    window.location.href = `${API_BASE}/login/`;
                }, 2500);
            } else {
                showToast('Network error. Please check your connection.', 'error');
            }
        } finally {
            if (!window.location.href.includes('login')) {
                setTimeout(() => {
                    if (submitBtn) {
                        submitBtn.innerHTML = originalContent;
                        submitBtn.disabled = false;
                        isLoading = false;
                    }
                }, 1000);
            } else {
                isLoading = false;
            }
        }
    });

   

    // Focus animation
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach(input => {
        input.addEventListener('focus', function () {
            this.parentElement.style.transform = 'scale(1.01)';
            this.parentElement.style.transition = 'transform 0.2s';
        });
        input.addEventListener('blur', function () {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    console.log('Reset page (email only) initialized ✅');
});