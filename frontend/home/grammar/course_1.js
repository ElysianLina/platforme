/**
 * course_1.js
 * Fetches grammar_a1_sentence_construction from /api/grammar-course/
 * and renders all sections dynamically.
 */

const COURSE_ID = 'grammar_a1_sentence_construction';

document.addEventListener('DOMContentLoaded', () => {
    initDropdown();
    loadUserData();
    loadCourse();
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
function getCookie(name) {
    for (const c of document.cookie.split(';')) {
        const [k, v] = c.trim().split('=');
        if (k === name) return decodeURIComponent(v);
    }
    return null;
}

// ── Profile dropdown ──────────────────────────────────────────────────────────
function initDropdown() {
    const trigger  = document.getElementById('profile-trigger');
    const dropdown = document.getElementById('profile-dropdown');
    if (!trigger || !dropdown) return;

    trigger.addEventListener('click', e => { e.stopPropagation(); dropdown.classList.toggle('active'); });
    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && !trigger.contains(e.target))
            dropdown.classList.remove('active');
    });

    const logoutBtn = document.querySelector('[data-action="logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async e => {
            e.preventDefault();
            await fetch('/api/logout/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
            localStorage.clear();
            window.location.href = '/login/';
        });
    }
}

// ── Load user data ────────────────────────────────────────────────────────────
async function loadUserData() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) return;
    try {
        const res  = await fetch(`/api/learner/?learner_id=${learnerId}`);
        const data = await res.json();
        if (!data.success || !data.learner) return;
        const l = data.learner;
        const initials = l.name ? l.name.slice(0, 2).toUpperCase() : '--';

        setText('avatar-initials',          initials);
        setText('dropdown-avatar-initials', initials);
        setText('dropdown-name',            l.name  || '--');
        setText('dropdown-email',           l.email || '--');

        const badge = document.getElementById('level-badge');
        if (badge) badge.textContent = `CEFR Level: ${l.cefr_level || '--'}`;

        if (l.picture) {
            ['avatar-img', 'dropdown-avatar-img'].forEach(id => {
                const img = document.getElementById(id);
                if (img) { img.src = l.picture; img.style.display = 'block'; }
            });
            hideEl('avatar-initials');
            hideEl('dropdown-avatar-initials');
        }
    } catch (err) { console.error('loadUserData:', err); }
}

// ── Load course ───────────────────────────────────────────────────────────────
async function loadCourse() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) { showError('Please log in to view this lesson.'); return; }

    try {
        const res  = await fetch(`/api/grammar-course/?course_id=${COURSE_ID}&learner_id=${learnerId}`);
        const data = await res.json();

        if (!data.success) { showError(data.error || 'Course not found.'); return; }

        // Hero
        setText('hero-title',       data.title);
        setText('hero-subtitle',    data.subtitle);
        setText('breadcrumb-title', data.title);

        // Render sections
        const body = document.getElementById('sections-body');
        body.innerHTML = '';
        const lessonSections = data.sections.filter(s => s.section_type !== 'exercise');

        lessonSections.forEach((sec, idx) => {
            const el = buildSection(sec, idx);
            body.appendChild(el);
        });

        // Open first section by default
        const firstBody = body.querySelector('.section-body');
        const firstToggle = body.querySelector('.section-toggle');
        if (firstBody)  firstBody.classList.add('open');
        if (firstToggle) firstToggle.classList.add('open');

        // Show course, hide loader
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('course-wrapper').style.display = 'block';

    } catch (err) {
        console.error('loadCourse:', err);
        showError('Failed to load the lesson. Please try again.');
    }
}

// ── Build one section card ────────────────────────────────────────────────────
function buildSection(sec, idx) {
    const wrapper = document.createElement('div');
    wrapper.className = 'lesson-section';
    wrapper.style.animationDelay = `${idx * 80}ms`;

    const typeClass = sec.section_type === 'tips' ? 'num-tips' : 'num-lesson';
    const typeIcon  = sec.section_type === 'tips' ? 'fa-exclamation-triangle' : 'fa-book';

    wrapper.innerHTML = `
        <div class="section-header" data-id="${sec.section_id}">
            <div class="section-num ${typeClass}">${sec.section_id}</div>
            <h2>${esc(sec.title)}</h2>
            <i class="fas fa-chevron-down section-toggle"></i>
        </div>
        <div class="section-body">
            ${buildSectionBody(sec)}
        </div>`;

    // Toggle collapse
    wrapper.querySelector('.section-header').addEventListener('click', () => {
        const body   = wrapper.querySelector('.section-body');
        const toggle = wrapper.querySelector('.section-toggle');
        body.classList.toggle('open');
        toggle.classList.toggle('open');
    });

    return wrapper;
}

// ── Section body dispatcher ───────────────────────────────────────────────────
function buildSectionBody(sec) {
    if (sec.section_type === 'lesson') return buildLesson(sec);
    if (sec.section_type === 'tips')   return buildTips(sec);
    return '';
}

// ── LESSON sections (1,2,3,4) ─────────────────────────────────────────────────
function buildLesson(sec) {
    const c  = sec.content;
    let html = '';

    // Explanation
    if (c.explanation) {
        html += `<p class="explanation-text">${esc(c.explanation)}</p>`;
    }

    // Single formula (sec 1 & 2)
    if (c.formula) {
        html += `<div class="formula-box">
            <i class="fas fa-equals"></i>
            <span class="formula-text">${esc(c.formula)}</span>
        </div>`;
    }

    // Multiple formulas (sec 3 & 4)
    if (c.formulas && c.formulas.length) {
        html += '<div class="formulas-grid">';
        c.formulas.forEach(f => {
            html += `<div class="formula-row">
                <div class="f-label">${esc(f.label || '')}</div>
                <div class="f-text">${esc(f.structure || f.formula || '')}</div>
            </div>`;
        });
        html += '</div>';
    }

    // Question words table (sec 4)
    if (c.question_words && c.question_words.length) {
        html += `<p class="block-title">Question Words</p>
        <table class="qwords-table">
            <thead><tr><th>Word</th><th>Use</th><th>Example</th></tr></thead>
            <tbody>`;
        c.question_words.forEach(qw => {
            html += `<tr>
                <td><strong>${esc(qw.word)}</strong></td>
                <td>${esc(qw.use || qw.meaning || '')}</td>
                <td><em>${esc(qw.example || '')}</em></td>
            </tr>`;
        });
        html += '</tbody></table>';
    }

    // Key rules
    if (c.key_rules && c.key_rules.length) {
        html += `<p class="block-title">Key Rules</p><div class="key-rules">`;
        c.key_rules.forEach(r => {
            html += `<div class="key-rule"><i class="fas fa-check-circle"></i><span>${esc(r)}</span></div>`;
        });
        html += '</div>';
    }

    // Examples
    if (c.examples && c.examples.length) {
        html += `<p class="block-title">Examples</p><div class="examples-grid">`;
        c.examples.forEach(ex => {
            // Section 4 — question format
            if (ex.type && ex.question) {
                html += buildQuestionExample(ex);
            } else {
                html += buildRegularExample(ex);
            }
        });
        html += '</div>';
    }

    // Did you know
    if (c.did_you_know) {
        html += `<div class="did-you-know">
            <i class="fas fa-lightbulb"></i>
            <p><strong>Did you know?</strong> ${esc(c.did_you_know)}</p>
        </div>`;
    }

    // Common errors from CSV
    if (c.common_errors && c.common_errors.length) {
        html += `<p class="block-title">Common Errors (from real learners)</p>`;
        c.common_errors.forEach(e => {
            html += `<div class="error-pair">
                <div class="err-bad"><div class="err-label">✗ Incorrect</div>${esc(e.incorrect)}</div>
                <div class="err-good"><div class="err-label">✓ Correct</div>${esc(e.correct)}</div>
            </div>`;
        });
    }

    return html;
}

// ── Regular example card (sec 1,2,3) ─────────────────────────────────────────
function buildRegularExample(ex) {
    let html = `<div class="example-card">`;

    if (ex.contraction) {
        html += `<span class="contraction">Contraction: ${esc(ex.contraction)}</span>`;
    }

    html += `<div class="example-sentence">${esc(ex.sentence)}</div>`;

    if (ex.breakdown && typeof ex.breakdown === 'object') {
        html += '<div class="example-breakdown">';
        const bd = ex.breakdown;
        if (bd.subject)    html += `<span class="tag tag-subject">S: ${esc(bd.subject)}</span>`;
        if (bd.auxiliary)  html += `<span class="tag tag-aux">Aux: ${esc(bd.auxiliary)}</span>`;
        if (bd.verb)       html += `<span class="tag tag-verb">V: ${esc(bd.verb)}</span>`;
        if (bd.negation)   html += `<span class="tag tag-neg">Neg: ${esc(bd.negation)}</span>`;
        if (bd.object)     html += `<span class="tag tag-object">O: ${esc(bd.object)}</span>`;
        if (bd.complement) html += `<span class="tag tag-compl">C: ${esc(bd.complement)}</span>`;
        html += '</div>';
    }

    if (ex.note) {
        html += `<div class="example-note">${esc(ex.note)}</div>`;
    }

    html += '</div>';
    return html;
}

// ── Question example (sec 4) ──────────────────────────────────────────────────
function buildQuestionExample(ex) {
    let html = `<div class="q-example">
        <div class="q-type">${esc(ex.type)}</div>
        <div class="q-sentence">${esc(ex.question)}</div>`;

    if (ex.short_answers) {
        html += '<div class="q-answers">';
        if (ex.short_answers.positive)
            html += `<span class="q-ans pos"><i class="fas fa-check"></i>${esc(ex.short_answers.positive)}</span>`;
        if (ex.short_answers.negative)
            html += `<span class="q-ans neg"><i class="fas fa-times"></i>${esc(ex.short_answers.negative)}</span>`;
        html += '</div>';
    }

    if (ex.breakdown && typeof ex.breakdown === 'object') {
        html += '<div class="example-breakdown" style="margin-top:.5rem">';
        const bd = ex.breakdown;
        if (bd.auxiliary)  html += `<span class="tag tag-aux">Aux: ${esc(bd.auxiliary)}</span>`;
        if (bd.subject)    html += `<span class="tag tag-subject">S: ${esc(bd.subject)}</span>`;
        if (bd.verb)       html += `<span class="tag tag-verb">V: ${esc(bd.verb)}</span>`;
        if (bd.object)     html += `<span class="tag tag-object">O: ${esc(bd.object)}</span>`;
        if (bd.complement) html += `<span class="tag tag-compl">C: ${esc(bd.complement)}</span>`;
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// ── TIPS section (section 5) ──────────────────────────────────────────────────
function buildTips(sec) {
    const c = sec.content;
    let html = '';

    if (c.explanation) {
        html += `<p class="tips-intro">${esc(c.explanation)}</p>`;
    }

    if (c.mistakes && c.mistakes.length) {
        c.mistakes.forEach(m => {
            html += `<div class="mistake-card">
                <div class="mistake-row">
                    <div class="mistake-bad">
                        <div class="mistake-label">✗ Incorrect</div>
                        ${esc(m.incorrect)}
                    </div>
                    <div class="mistake-good">
                        <div class="mistake-label">✓ Correct</div>
                        ${esc(m.correct)}
                    </div>
                </div>
                <div class="mistake-explanation">${esc(m.explanation)}</div>
                ${m.error_type ? `<span class="mistake-type">${esc(m.error_type)}</span>` : ''}
            </div>`;
        });
    }

    return html;
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val || '';
}
function hideEl(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}
function showError(msg) {
    document.getElementById('loading-state').innerHTML =
        `<i class="fas fa-exclamation-circle" style="font-size:2rem;color:#ef4444"></i><p>${msg}</p>`;
}