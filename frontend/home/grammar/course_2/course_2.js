/**
 * course_2.js — Word Order in English
 * Fetches grammar_a1_word_order from /api/grammar-course/
 * and renders all sections (lessons + tips).
 * Handles all breakdown tag types specific to course 2:
 * subject, verb, object, manner, place, time, frequency,
 * indirect_object, direct_object, linking_verb, complement,
 * opinion, size, age, shape, color, origin, material, noun, to
 */

const COURSE_ID = 'grammar_a1_word_order';

document.addEventListener('DOMContentLoaded', () => {
    initDropdown();
    loadUserData();
    loadCourse();
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(str) {
    return String(str || '')
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function getCookie(name) {
    for (const c of document.cookie.split(';')) {
        const [k,v] = c.trim().split('=');
        if (k === name) return decodeURIComponent(v);
    }
    return null;
}
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

// ── Dropdown ──────────────────────────────────────────────────────────────────
function initDropdown() {
    const trigger  = document.getElementById('profile-trigger');
    const dropdown = document.getElementById('profile-dropdown');
    if (!trigger || !dropdown) return;

    trigger.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
    });
    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && !trigger.contains(e.target))
            dropdown.classList.remove('active');
    });

    const logoutBtn = document.querySelector('[data-action="logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async e => {
            e.preventDefault();
            await fetch('/api/logout/', {
                method : 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
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
        const initials = l.name ? l.name.slice(0,2).toUpperCase() : '--';

        setText('avatar-initials',          initials);
        setText('dropdown-avatar-initials', initials);
        setText('dropdown-name',            l.name  || '--');
        setText('dropdown-email',           l.email || '--');

        const badge = document.getElementById('level-badge');
        if (badge) badge.textContent = `CEFR Level: ${l.cefr_level || '--'}`;

        if (l.picture) {
            ['avatar-img','dropdown-avatar-img'].forEach(id => {
                const img = document.getElementById(id);
                if (img) { img.src = l.picture; img.style.display = 'block'; }
            });
            hideEl('avatar-initials');
            hideEl('dropdown-avatar-initials');
        }
    } catch (err) { console.error('loadUserData:', err); }
}

// ── Load course from API ──────────────────────────────────────────────────────
async function loadCourse() {
    const learnerId = localStorage.getItem('learner_id');
    if (!learnerId) { showError('Please log in to view this lesson.'); return; }

    try {
        const res  = await fetch(`/api/grammar-course/?course_id=${COURSE_ID}&learner_id=${learnerId}`);
        const data = await res.json();

        if (!data.success) { showError(data.error || 'Course not found.'); return; }

        setText('hero-title',       data.title);
        setText('hero-subtitle',    data.subtitle);
        setText('breadcrumb-title', data.title);

        // Render lesson + tips sections only (skip exercise section)
        const body = document.getElementById('sections-body');
        body.innerHTML = '';
        const visibleSections = data.sections.filter(s => s.section_type !== 'exercise');

        visibleSections.forEach((sec, idx) => {
            const el = buildSection(sec, idx);
            body.appendChild(el);
        });

        // Open first section by default
        const firstBody   = body.querySelector('.section-body');
        const firstToggle = body.querySelector('.section-toggle');
        if (firstBody)   firstBody.classList.add('open');
        if (firstToggle) firstToggle.classList.add('open');

        document.getElementById('loading-state').style.display  = 'none';
        document.getElementById('course-wrapper').style.display = 'block';

    } catch (err) {
        console.error('loadCourse:', err);
        showError('Failed to load the lesson. Please try again.');
    }
}

// ── Build section card ────────────────────────────────────────────────────────
function buildSection(sec, idx) {
    const wrapper = document.createElement('div');
    wrapper.className = 'lesson-section';
    wrapper.style.animationDelay = `${idx * 80}ms`;

    const numClass = sec.section_type === 'tips' ? 'num-tips' : 'num-lesson';

    wrapper.innerHTML = `
        <div class="section-header">
            <div class="section-num ${numClass}">${esc(sec.section_id)}</div>
            <h2>${esc(sec.title)}</h2>
            <i class="fas fa-chevron-down section-toggle"></i>
        </div>
        <div class="section-body">
            ${buildSectionBody(sec)}
        </div>`;

    wrapper.querySelector('.section-header').addEventListener('click', () => {
        wrapper.querySelector('.section-body').classList.toggle('open');
        wrapper.querySelector('.section-toggle').classList.toggle('open');
    });

    return wrapper;
}

// ── Section body dispatcher ───────────────────────────────────────────────────
function buildSectionBody(sec) {
    if (sec.section_type === 'lesson') return buildLesson(sec);
    if (sec.section_type === 'tips')   return buildTips(sec);
    return '';
}

// ── LESSON builder ────────────────────────────────────────────────────────────
function buildLesson(sec) {
    const c = sec.content;
    let html = '';

    // Explanation
    if (c.explanation) {
        html += `<p class="explanation-text">${esc(c.explanation)}</p>`;
    }

    // Single formula (sections 1 & 2)
    if (c.formula) {
        html += `<div class="formula-box">
            <i class="fas fa-equals"></i>
            <span class="formula-text">${esc(c.formula)}</span>
        </div>`;
    }

    // Multiple formulas (sections 3 & 4)
    if (c.formulas && c.formulas.length) {
        html += '<div class="formulas-grid">';
        c.formulas.forEach(f => {
            html += `<div class="formula-row">
                <div class="f-label">${esc(f.label || '')}</div>
                <div class="f-text">${esc(f.structure || '')}</div>
            </div>`;
        });
        html += '</div>';
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
            html += buildExample(ex);
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

// ── Example card with all breakdown tag types ─────────────────────────────────
function buildExample(ex) {
    let html = `<div class="example-card">
        <div class="example-sentence">${esc(ex.sentence)}</div>`;

    if (ex.breakdown && typeof ex.breakdown === 'object') {
        html += '<div class="example-breakdown">';
        const bd = ex.breakdown;

        // SVOMPT tags
        if (bd.subject)         html += tag('S',          bd.subject,         'subject');
        if (bd.frequency)       html += tag('Freq',       bd.frequency,       'frequency');
        if (bd.verb)            html += tag('V',          bd.verb,            'verb');
        if (bd.linking_verb)    html += tag('V',          bd.linking_verb,    'linking');
        if (bd.indirect_object) html += tag('Ind.O',      bd.indirect_object, 'indirect');
        if (bd.to)              html += tag('to',         bd.to,              'to');
        if (bd.direct_object)   html += tag('Dir.O',      bd.direct_object,   'direct');
        if (bd.object)          html += tag('O',          bd.object,          'object');
        if (bd.complement)      html += tag('C',          bd.complement,      'complement');
        if (bd.manner)          html += tag('Manner',     bd.manner,          'manner');
        if (bd.place)           html += tag('Place',      bd.place,           'place');
        if (bd.time)            html += tag('Time',       bd.time,            'time');

        // Adjective order tags
        if (bd.opinion)   html += tag('Opinion',   bd.opinion,   'opinion');
        if (bd.size)      html += tag('Size',       bd.size,      'size');
        if (bd.age)       html += tag('Age',        bd.age,       'age');
        if (bd.shape)     html += tag('Shape',      bd.shape,     'shape');
        if (bd.color)     html += tag('Color',      bd.color,     'color');
        if (bd.origin)    html += tag('Origin',     bd.origin,    'origin');
        if (bd.material)  html += tag('Material',   bd.material,  'material');
        if (bd.noun)      html += tag('Noun',       bd.noun,      'noun');

        html += '</div>';
    }

    if (ex.note) {
        html += `<div class="example-note">${esc(ex.note)}</div>`;
    }

    html += '</div>';
    return html;
}

// ── Tag builder ───────────────────────────────────────────────────────────────
function tag(label, value, type) {
    return `<span class="tag tag-${type}"><strong>${label}:</strong> ${esc(value)}</span>`;
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