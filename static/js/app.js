/* Frontend Interactivity & Agent Automation - ResearchRadar AI */

document.addEventListener('DOMContentLoaded', () => {
    initSplashScreen();   // Must run first — shows before everything else
    init3DBackground();
    init3DTilt();
    initNotificationContainer();
    initUploadZone();
    initSemanticSearch();
    initRealTimePolling();
});

// ─── SPLASH SCREEN ──────────────────────────────────────────────
function initSplashScreen() {
    const splash = document.getElementById('splash-screen');
    if (!splash) return;

    // Only show once per session
    if (sessionStorage.getItem('rr-splash-shown')) {
        splash.classList.add('splash-hidden');
        return;
    }

    // ── Splash particle canvas ──
    const canvas = document.getElementById('splash-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const COLORS = ['rgba(99,102,241,', 'rgba(0,242,254,', 'rgba(168,85,247,', 'rgba(255,255,255,'];
    const pts = Array.from({ length: 80 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        r: Math.random() * 2 + 0.5,
        c: Math.floor(Math.random() * COLORS.length),
        a: Math.random() * 0.6 + 0.2,
        pulse: Math.random() * Math.PI * 2,
    }));

    let splashRafId;
    function drawSplash() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (const p of pts) {
            p.x += p.vx; p.y += p.vy; p.pulse += 0.018;
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width)  p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;
            const a = p.a * (0.7 + 0.3 * Math.sin(p.pulse));
            const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 8);
            grd.addColorStop(0, COLORS[p.c] + a + ')');
            grd.addColorStop(1, COLORS[p.c] + '0)');
            ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 8, 0, Math.PI * 2);
            ctx.fillStyle = grd; ctx.fill();
            ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = COLORS[p.c] + (a + 0.3) + ')'; ctx.fill();
        }
        // Connecting lines
        for (let i = 0; i < pts.length; i++) {
            for (let j = i + 1; j < pts.length; j++) {
                const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
                const d = Math.sqrt(dx*dx + dy*dy);
                if (d < 140) {
                    ctx.beginPath();
                    ctx.moveTo(pts[i].x, pts[i].y);
                    ctx.lineTo(pts[j].x, pts[j].y);
                    ctx.strokeStyle = COLORS[pts[i].c] + ((1 - d/140) * 0.12) + ')';
                    ctx.lineWidth = 0.8; ctx.stroke();
                }
            }
        }
        splashRafId = requestAnimationFrame(drawSplash);
    }
    drawSplash();

    // ── Progress bar ──
    const bar   = document.getElementById('splashLoaderBar');
    const label = document.getElementById('splashLoadingText');
    const STEPS = [
        [0,   'Initializing AI Agents…'],
        [20,  'Loading Knowledge Base…'],
        [45,  'Connecting to ChromaDB…'],
        [65,  'Preparing Analysis Engine…'],
        [85,  'Almost ready…'],
        [100, 'Welcome to ResearchRadar AI!'],
    ];

    let stepIdx = 0;
    const TOTAL_DURATION = 2800; // ms before dismiss
    const TICK = 40;
    let elapsed = 0;

    const tick = setInterval(() => {
        elapsed += TICK;
        const pct = Math.min((elapsed / TOTAL_DURATION) * 100, 100);
        if (bar) bar.style.width = pct + '%';

        // Update label at each step
        if (stepIdx < STEPS.length - 1 && pct >= STEPS[stepIdx + 1][0]) {
            stepIdx++;
            if (label) label.textContent = STEPS[stepIdx][1];
        }

        if (elapsed >= TOTAL_DURATION) {
            clearInterval(tick);
            dismissSplash();
        }
    }, TICK);

    function dismissSplash() {
        cancelAnimationFrame(splashRafId);
        splash.classList.add('splash-exit');
        sessionStorage.setItem('rr-splash-shown', '1');
        setTimeout(() => splash.classList.add('splash-hidden'), 750);
    }

    // Also allow click/tap to skip
    splash.addEventListener('click', () => {
        clearInterval(tick);
        dismissSplash();
    }, { once: true });
}

// 0. Animated 3D Floating Particle Background
function init3DBackground() {
    const canvas = document.getElementById('bg-3d-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    });

    // Particle system — floating nodes and connecting edges
    const PARTICLE_COUNT = 55;
    const MAX_LINK_DIST = 180;

    const COLORS = [
        'rgba(138, 43, 226,',   // purple
        'rgba(0, 242, 254,',    // cyan
        'rgba(99, 102, 241,',   // indigo
        'rgba(255, 0, 127,',    // pink
    ];

    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        z: Math.random() * 2 + 0.3,       // depth factor (0.3..2.3)
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 2.5 + 1,
        colorIdx: Math.floor(Math.random() * COLORS.length),
        pulse: Math.random() * Math.PI * 2,
    }));

    function draw() {
        ctx.clearRect(0, 0, W, H);

        // Update & draw particles
        for (const p of particles) {
            p.x += p.vx * p.z;
            p.y += p.vy * p.z;
            p.pulse += 0.02;

            // Wrap around
            if (p.x < 0) p.x = W;
            if (p.x > W) p.x = 0;
            if (p.y < 0) p.y = H;
            if (p.y > H) p.y = 0;

            const alpha = 0.3 + 0.3 * Math.sin(p.pulse);
            const radius = p.r * p.z * (1 + 0.3 * Math.sin(p.pulse));
            const color = COLORS[p.colorIdx];

            // Glow halo
            const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius * 6);
            grd.addColorStop(0, color + `${alpha}) `);
            grd.addColorStop(1, color + '0)');
            ctx.beginPath();
            ctx.arc(p.x, p.y, radius * 6, 0, Math.PI * 2);
            ctx.fillStyle = grd;
            ctx.fill();

            // Core dot
            ctx.beginPath();
            ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = color + `${alpha + 0.3})`;
            ctx.fill();
        }

        // Draw connecting lines between nearby particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const a = particles[i], b = particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MAX_LINK_DIST) {
                    const lineAlpha = (1 - dist / MAX_LINK_DIST) * 0.15;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.strokeStyle = COLORS[a.colorIdx] + `${lineAlpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }

    draw();
}

// 1. Card hover physics (3D tilt removed — now just CSS lift)
function init3DTilt() {
    // 3D tilt effects removed; hover lift is handled purely by CSS (.card-3d:hover)
}

// 2. Alert Toasts Notification Core
function initNotificationContainer() {
    if (!document.getElementById('floating-alerts')) {
        const div = document.createElement('div');
        div.id = 'floating-alerts';
        div.className = 'floating-alerts-container';
        document.body.appendChild(div);
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('floating-alerts');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `alert-toast ${type}`;
    
    let icon = '<i class="fas fa-info-circle"></i>';
    if (type === 'success') icon = '<i class="fas fa-check-circle"></i>';
    if (type === 'error') icon = '<i class="fas fa-exclamation-triangle"></i>';
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);
    
    // Auto-remove after 4.5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// 3. PDF Upload drag-and-drop
function initUploadZone() {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('upload-file-input');
    if (!zone || !input) return;
    
    zone.addEventListener('click', () => input.click());
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'var(--secondary)';
        zone.style.background = 'rgba(0, 242, 254, 0.04)';
    });
    
    zone.addEventListener('dragleave', () => {
        zone.style.borderColor = 'rgba(138, 43, 226, 0.3)';
        zone.style.background = 'rgba(15, 17, 30, 0.4)';
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'rgba(138, 43, 226, 0.3)';
        zone.style.background = 'rgba(15, 17, 30, 0.4)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFilesUpload(files);
        }
    });
    
    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            handleFilesUpload(input.files);
        }
    });
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

async function handleFilesUpload(files) {
    const csrfToken = getCSRFToken();
    let uploadedCount = 0;
    
    showToast(`Uploading ${files.length} paper(s)...`, 'info');
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const allowedExtensions = ['pdf', 'pptx', 'ppt'];
        const extension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(extension)) {
            showToast(`"${file.name}" is not a PDF or PowerPoint file. Skipped.`, 'error');
            continue;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        const titleWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
        formData.append('title', titleWithoutExtension);
        
        try {
            const response = await fetch('/api/papers/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                uploadedCount++;
                showToast(`Uploaded: ${file.name}. Initializing analysis.`, 'success');
                // Trigger background parsing
                triggerPaperProcessing(data.id);
            } else {
                showToast(`Failed to upload ${file.name}`, 'error');
            }
        } catch (err) {
            showToast(`Network error uploading ${file.name}`, 'error');
            console.error(err);
        }
    }
    
    if (uploadedCount > 0) {
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    }
}

// 4. Trigger Paper processing agent pipeline
async function triggerPaperProcessing(paperId) {
    const csrfToken = getCSRFToken();
    try {
        const response = await fetch(`/api/papers/${paperId}/process/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        if (response.ok) {
            const data = await response.json();
            showToast(`AI analysis complete for paper: "${data.title}"`, 'success');
            return true;
        } else {
            showToast("AI extraction failed for uploaded paper", 'error');
            return false;
        }
    } catch (e) {
        console.error(e);
        return false;
    }
}

// Manually trigger single paper processing from summaries page
async function processPaperManually(paperId, btn) {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    showToast("PaperReading & Summary Agents initiated.", "info");
    
    const success = await triggerPaperProcessing(paperId);
    if (success) {
        btn.innerHTML = '<i class="fas fa-check"></i> Processed';
        btn.className = "btn-3d btn-3d-secondary";
        setTimeout(() => window.location.reload(), 1500);
    } else {
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// Delete single paper
async function deletePaper(paperId, btn) {
    if (!confirm("Are you sure you want to delete this paper? This will remove its database record, physical document, and all associated semantic vectors.")) {
        return;
    }
    
    const row = btn.closest('tr');
    const csrfToken = getCSRFToken();
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    try {
        const response = await fetch(`/api/papers/${paperId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        if (response.ok) {
            showToast("Paper deleted successfully", "success");
            // Fade out and remove row
            if (row) {
                row.style.transition = 'all 0.5s ease';
                row.style.opacity = '0';
                row.style.transform = 'translateX(20px)';
                setTimeout(() => {
                    row.remove();
                    // Check if table has any rows left
                    const tbody = document.querySelector('.custom-table tbody');
                    if (tbody && tbody.children.length === 0) {
                        window.location.reload(); // Shows empty state
                    }
                }, 500);
            } else {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else {
            showToast("Failed to delete paper", "error");
            btn.disabled = false;
            btn.innerHTML = oldHtml;
        }
    } catch (err) {
        showToast("Error deleting paper", "error");
        console.error(err);
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// Bulk paper selection handlers
function toggleSelectAllPapers(masterCheckbox) {
    const checkboxes = document.querySelectorAll('.paper-select');
    checkboxes.forEach(cb => {
        cb.checked = masterCheckbox.checked;
        const row = cb.closest('tr');
        if (row) {
            if (cb.checked) {
                row.classList.add('row-selected');
            } else {
                row.classList.remove('row-selected');
            }
        }
    });
    updateDeleteSelectedButton();
}

function togglePaperSelection(cb) {
    const row = cb.closest('tr');
    if (row) {
        if (cb.checked) {
            row.classList.add('row-selected');
        } else {
            row.classList.remove('row-selected');
        }
    }
    
    // Update master checkbox state
    const master = document.getElementById('select-all-papers');
    if (master) {
        const total = document.querySelectorAll('.paper-select').length;
        const checked = document.querySelectorAll('.paper-select:checked').length;
        master.checked = (total === checked && total > 0);
        master.indeterminate = (checked > 0 && checked < total);
    }
    
    updateDeleteSelectedButton();
}

function updateDeleteSelectedButton() {
    const btn = document.getElementById('delete-selected-btn');
    const countSpan = document.getElementById('selected-count');
    if (!btn) return;
    
    const checkedCount = document.querySelectorAll('.paper-select:checked').length;
    if (countSpan) {
        countSpan.textContent = checkedCount;
    }
    
    if (checkedCount > 0) {
        btn.style.display = 'inline-flex';
    } else {
        btn.style.display = 'none';
    }
}

async function deleteSelectedPapers() {
    const checkedBoxes = document.querySelectorAll('.paper-select:checked');
    if (checkedBoxes.length === 0) return;
    
    if (!confirm(`Are you sure you want to delete the ${checkedBoxes.length} selected paper(s)? This will remove their DB records, physical files, and vector embeddings.`)) {
        return;
    }
    
    const btn = document.getElementById('delete-selected-btn');
    const oldHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    
    const csrfToken = getCSRFToken();
    let successCount = 0;
    
    for (const cb of checkedBoxes) {
        const paperId = cb.value;
        const row = cb.closest('tr');
        
        try {
            const response = await fetch(`/api/papers/${paperId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            if (response.ok) {
                successCount++;
                if (row) {
                    row.style.transition = 'all 0.5s ease';
                    row.style.opacity = '0';
                    row.style.transform = 'translateX(20px)';
                    setTimeout(() => row.remove(), 500);
                }
            }
        } catch (err) {
            console.error(`Error deleting paper ${paperId}:`, err);
        }
    }
    
    showToast(`Deleted ${successCount} paper(s) successfully.`, 'success');
    
    setTimeout(() => {
        window.location.reload();
    }, 800);
}

// 5. Trigger Gap Detection Agent across papers
async function runGapDetection(btn) {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding Gaps...';
    showToast("GapDetectionAgent analyzing papers...", "info");
    
    const csrfToken = getCSRFToken();
    try {
        const response = await fetch('/api/gaps/detect/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Gap detection successful! Found ${data.length} gaps.`, 'success');
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showToast("Failed to detect research gaps", 'error');
            btn.disabled = false;
            btn.innerHTML = oldHtml;
        }
    } catch (e) {
        showToast("Network error running gap detection", 'error');
        console.error(e);
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// 6. Generate Project Idea from specific Gap
async function generateIdeaForGap(gapId, btn) {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    showToast("ProjectIdeaAgent constructing methodology...", "info");
    
    const csrfToken = getCSRFToken();
    try {
        const response = await fetch(`/api/gaps/${gapId}/generate_idea/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Project idea created: "${data.title}"`, 'success');
            setTimeout(() => {
                window.location.href = '/ideas/';
            }, 1500);
        } else {
            showToast("Failed to generate project idea", 'error');
            btn.disabled = false;
            btn.innerHTML = oldHtml;
        }
    } catch (e) {
        showToast("Network error creating project idea", 'error');
        console.error(e);
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// 7. Generate Experimental Plan for Project Idea
async function generateExperimentalPlan(ideaId, btn) {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Structuring...';
    showToast("ExperimentPlanningAgent detailing models & training approach...", "info");
    
    const csrfToken = getCSRFToken();
    try {
        const response = await fetch(`/api/ideas/${ideaId}/generate_plan/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Experimental plan finalized: "${data.title}"`, 'success');
            setTimeout(() => {
                window.location.href = '/experiments/';
            }, 1500);
        } else {
            showToast("Failed to generate experimental plan", 'error');
            btn.disabled = false;
            btn.innerHTML = oldHtml;
        }
    } catch (e) {
        showToast("Network error creating experimental plan", 'error');
        console.error(e);
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// 8. Generate Literature Review
async function generateLiteratureReview(btn) {
    const checkboxes = document.querySelectorAll('.multi-select-list input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        showToast("Please select at least one paper to review.", "error");
        return;
    }
    
    const paperIds = Array.from(checkboxes).map(cb => cb.value);
    const titleInput = document.getElementById('review-title-input');
    const title = titleInput ? titleInput.value.trim() : 'Literature Synthesis';
    
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Writing Review...';
    showToast("LiteratureReviewAgent parsing studies...", "info");
    
    const csrfToken = getCSRFToken();
    try {
        const response = await fetch('/api/literature/generate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                paper_ids: paperIds,
                title: title || 'Literature Synthesis'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast("Literature review synthesized successfully!", 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast("Failed to generate literature review", 'error');
            btn.disabled = false;
            btn.innerHTML = oldHtml;
        }
    } catch (e) {
        showToast("Network error compiling literature review", 'error');
        console.error(e);
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
}

// UI Toggles for Checkboxes list in review selection
function toggleSelectCard(card) {
    const cb = card.querySelector('input[type="checkbox"]');
    if (cb) {
        cb.checked = !cb.checked;
        if (cb.checked) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    }
}

// 9. Semantic search querying
function initSemanticSearch() {
    const input = document.getElementById('semantic-search-input');
    const resultsContainer = document.getElementById('search-results-list');
    if (!input || !resultsContainer) return;
    
    let debounceTimer;
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();
        
        if (query.length < 3) {
            resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>Type at least 3 characters to search across paper chunks semantically...</p></div>';
            return;
        }
        
        resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Querying ChromaDB vectors...</p></div>';
        
        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/papers/semantic_search/?q=${encodeURIComponent(query)}`);
                if (response.ok) {
                    const data = await response.json();
                    renderSearchResults(data, resultsContainer);
                } else {
                    resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-times"></i><p>Vector query failed.</p></div>';
                }
            } catch (e) {
                resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error searching databases.</p></div>';
                console.error(e);
            }
        }, 400); // 400ms debounce
    });
}

function renderSearchResults(results, container) {
    if (results.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-folder-open"></i><p>No matching segments found. Try uploading more papers or refining keywords.</p></div>';
        return;
    }
    
    container.innerHTML = '';
    results.forEach(res => {
        const item = document.createElement('div');
        item.className = 'search-result-item card-3d';
        
        // Calculate dynamic similarity score: Chroma distance. Distance is usually L2. If using cosine, smaller is better.
        // Let's show as a nice confidence percent.
        const similarityPct = Math.max(10, Math.round((1 - res.distance) * 100));
        
        item.innerHTML = `
            <div class="pop-3d">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span class="badge badge-completed">Match: ${similarityPct}%</span>
                    <span style="font-size:0.75rem; color:var(--text-muted);">Segment #${res.chunk_index + 1}</span>
                </div>
                <h4 style="color:var(--secondary);">${res.paper.title || 'Untitled Paper'}</h4>
                <p class="search-result-snippet">"${res.text_content}"</p>
                <div style="margin-top:10px; font-size:0.75rem; color:var(--text-muted);">
                    <i class="fas fa-user-friends"></i> ${res.paper.authors || 'Unknown Authors'} &nbsp;&bull;&nbsp;
                    <i class="fas fa-calendar-alt"></i> ${new Date(res.paper.upload_date).toLocaleDateString()}
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

// ─── REAL-TIME POLLING FOR PROCESSING PAPERS ──────────────────────
function initRealTimePolling() {
    const processingBadges = document.querySelectorAll('.badge[data-paper-status="PROCESSING"]');
    if (processingBadges.length === 0) return;

    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/papers/');
            if (!response.ok) return;
            
            const papers = await response.json();
            let allFinished = true;

            processingBadges.forEach(badge => {
                const paperId = badge.getAttribute('data-paper-id');
                const matchingPaper = papers.find(p => p.id === paperId);
                
                if (matchingPaper) {
                    const currentStatus = matchingPaper.status;
                    const pct = matchingPaper.processing_percentage || 0;
                    
                    badge.setAttribute('data-paper-status', currentStatus);
                    badge.className = `badge badge-${currentStatus.toLowerCase()}`;
                    
                    if (currentStatus === 'PROCESSING') {
                        badge.textContent = `Processing: ${pct}%`;
                        allFinished = false;
                    } else {
                        badge.textContent = currentStatus;
                    }
                }
            });

            const currentProcessing = document.querySelectorAll('.badge[data-paper-status="PROCESSING"]');
            if (currentProcessing.length < processingBadges.length || allFinished) {
                clearInterval(pollInterval);
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } catch (e) {
            console.error("Error polling paper statuses:", e);
        }
    }, 2500);
}
