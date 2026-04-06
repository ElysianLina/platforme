// ============================================
// exercise-menu.js
// ✅ FIX : passe subunit_id dans l'URL de comprehension-ecrite
//          pour ne pas dépendre du localStorage (perdu entre onglets)
// ============================================

function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        subunit:   params.get('subunit')    || '1.1',
        title:     params.get('title')      || 'Exercise',
        subunitId: params.get('subunit_id') || ''
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const { subunit, title, subunitId } = getUrlParams();

    // Mettre à jour le badge et le titre
    const subunitIdEl    = document.getElementById('subunit-id');
    const subunitTitleEl = document.getElementById('subunit-title');
    if (subunitIdEl)    subunitIdEl.textContent    = subunit;
    if (subunitTitleEl) subunitTitleEl.textContent = title;

    // Stocker en localStorage (fallback)
    localStorage.setItem('currentSubunit',      subunit);
    localStorage.setItem('currentSubunitTitle', title);
    if (subunitId) localStorage.setItem('currentSubunitId', subunitId);

    // ✅ Inclure subunit_id dans l'URL de comprehension-ecrite
    const comprehensionLink = document.getElementById('comprehension-ecrite');
    if (comprehensionLink) {
        comprehensionLink.href = `/comprehension-ecrite/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
    }

    // ✅ Lien retour vers home avec learner_id
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
        const learnerId = localStorage.getItem('learner_id');
        backBtn.href = learnerId ? `/?learner_id=${learnerId}` : '/';
    }

    // Corriger le menu actif dans la sidebar
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => item.classList.remove('active'));
    const homeLink = document.querySelector('.sidebar-nav a[href="home.html"]');
    if (homeLink) homeLink.classList.add('active');
});