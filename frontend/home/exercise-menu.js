// ============================================
// exercise-menu.js
// ✅ FIX : passe subunit_id dans l'URL de comprehension-ecrite
//          pour ne pas dépendre du localStorage (perdu entre onglets)
// ✅ AJOUT : Calcul et affichage du score moyen de compréhension écrite
//          Moyenne = somme des scores / nombre d'exercices faits (1 à 4)
// ============================================

function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        subunit:   params.get('subunit')    || '1.1',
        title:     params.get('title')      || 'Exercise',
        subunitId: params.get('subunit_id') || null
    };
}

// ============================================
// CALCUL DU SCORE MOYEN DE COMPRÉHENSION ÉCRITE
// ============================================

/**
 * Charge et calcule le score moyen de compréhension écrite
 * Score = (somme des scores des exercices faits) / (nombre d'exercices faits)
 * Ex: Si fait original (80%) + 1 généré (70%) → Moyenne = (80+70)/2 = 75%
 * @param {string} subunitId - ID du subunit
 * @param {string} learnerId - ID de l'apprenant
 * @returns {Promise<{average: number|null, count: number}>} - Score moyen et nombre d'exercices faits
 */
async function loadReadingComprehensionScore(subunitId, learnerId) {
    if (!learnerId || !subunitId || subunitId === '') {
        return { average: null, count: 0 };
    }
    
    try {
        // 1. Récupérer le texte original pour avoir son ID
        const textResponse = await fetch(`http://localhost:8000/api/reading-exercise/?subunit_id=${subunitId}`);
        const textData = await textResponse.json();
        
        if (!textData.success || !textData.text) {
            console.log('❌ No original text found for subunit:', subunitId);
            return { average: null, count: 0 };
        }
        
        const originalTextId = textData.text.id;
        const scores = []; // Tableau des scores trouvés
        
        // 2. Récupérer le score du texte original (si fait)
        try {
            const originalResult = await fetch(
                `http://localhost:8000/api/check-reading-result/?text_id=${originalTextId}&learner_id=${learnerId}`
            );
            const originalData = await originalResult.json();
            
            if (originalData.success && originalData.has_result) {
                scores.push(originalData.score);
                console.log('✅ Original score:', originalData.score);
            }
        } catch (e) {
            console.log('ℹ️ No original score available');
        }
        
        // 3. Récupérer les scores des exercices générés (0 à 3 possibles)
        try {
            const genResponse = await fetch(
                `http://localhost:8000/api/gen-results/?learner_id=${learnerId}&original_id=${originalTextId}`
            );
            const genData = await genResponse.json();
            
            if (genData.success && genData.results && genData.results.length > 0) {
                genData.results.forEach(r => {
                    if (r.score_percentage !== null && r.score_percentage !== undefined) {
                        scores.push(r.score_percentage);
                    }
                });
                console.log('✅ Generated scores found:', genData.results.length);
            }
        } catch (e) {
            console.log('ℹ️ No generated scores available');
        }
        
        // 4. Calculer la moyenne si on a des scores
        const count = scores.length;
        
        if (count === 0) {
            console.log('ℹ️ No scores found - returning null');
            return { average: null, count: 0 }; // Aucun exercice fait
        }
        
        // ✅ CORRECTION : Diviser par le nombre réel d'exercices faits, pas toujours par 4
        const average = Math.round(scores.reduce((a, b) => a + b, 0) / count);
        console.log(`📊 Average score: ${average}% (from ${count} exercise${count > 1 ? 's' : ''})`);
        console.log('   Scores:', scores);
        
        return { average, count };
        
    } catch (error) {
        console.error('❌ Error loading reading score:', error);
        return { average: null, count: 0 };
    }
}

/**
 * Met à jour l'affichage du badge de score
 * @param {number|null} score - Score moyen ou null
 * @param {number} count - Nombre d'exercices faits
 *@returns {Promise<{average: number|null, count: number}>} Score moyen et nombre d'exercices faits
 */
function updateReadingScoreBadge(score, count) {
    const badge = document.getElementById('reading-score-badge');
    if (!badge) {
        console.error('❌ Badge element not found');
        return;
    }
    
    if (score === null || count === 0) {
        // ✅ Aucun exercice fait - afficher "No progress yet !"
        badge.textContent = 'No progress yet !';
        badge.className = 'difficulty no-progress';
        badge.style.background = '#e9ecef';
        badge.style.color = '#6c757d';
        badge.title = 'Start your first reading exercise!';
    } else {
        // ✅ Score disponible - afficher "15% (1 exercise completed)" ou "75% (3 exercises completed)"
        const exerciseWord = count === 1 ? 'exercise' : 'exercises';
        badge.textContent = `${score}% (${count} ${exerciseWord} completed)`;
        
        // Texte au survol pour détails
        badge.title = `Average score from ${count} completed ${exerciseWord}`;
        
        // Couleur selon le score
        if (score >= 80) {
            badge.className = 'difficulty excellent';
            badge.style.background = '#d4edda';
            badge.style.color = '#155724';
        } else if (score >= 60) {
            badge.className = 'difficulty good';
            badge.style.background = '#fff3cd';
            badge.style.color = '#856404';
        } else if (score >= 40) {
            badge.className = 'difficulty average';
            badge.style.background = '#ffe5cc';
            badge.style.color = '#cc6600';
        } else {
            badge.className = 'difficulty needs-work';
            badge.style.background = '#f8d7da';
            badge.style.color = '#721c24';
        }
    }
}

// ============================================
// INITIALISATION
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    const { subunit, title, subunitId } = getUrlParams();
    const learnerId = localStorage.getItem('learner_id');

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

    const listeningLink = document.getElementById('comprehension-orale');
    if (listeningLink) {
        listeningLink.href = `/listening/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
        listeningLink.classList.remove('disabled');
        // Remplacer le cadenas par une flèche
        listeningLink.querySelector('.exercise-arrow i').className = 'fas fa-chevron-right';
    }

    // Lien Writing
    const writingLink = document.getElementById('expression-ecrite');
    if (writingLink) {
        writingLink.href = `/writing/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
        writingLink.classList.remove('disabled');
        writingLink.querySelector('.exercise-arrow i').className = 'fas fa-chevron-right';
    }

    const speakingLink = document.getElementById('expression-orale');
    if (speakingLink) {
        speakingLink.href = `/speaking/?subunit=${subunit}&title=${encodeURIComponent(title)}&subunit_id=${subunitId}`;
        speakingLink.classList.remove('disabled');
        speakingLink.querySelector('.exercise-arrow i').className = 'fas fa-chevron-right';
    }
    // ✅ Lien retour vers home avec learner_id
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
        backBtn.href = learnerId ? `/?learner_id=${learnerId}` : '/';
    }

    // Corriger le menu actif dans la sidebar
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => item.classList.remove('active'));
    const homeLink = document.querySelector('.sidebar-nav a[href="home.html"]');
    if (homeLink) homeLink.classList.add('active');

    // ✅ CHARGER ET AFFICHER LE SCORE MOYEN
    if (subunitId && learnerId) {
        console.log('🔄 Loading reading comprehension score...');
        const { average, count } = await loadReadingComprehensionScore(subunitId, learnerId);
        updateReadingScoreBadge(average, count);
    } else {
        console.log('⚠️ Missing subunitId or learnerId, showing "No progress yet !"');
        updateReadingScoreBadge(null, 0);
    }
});