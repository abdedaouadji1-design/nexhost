/**
 * NexHost V4 - Utils
 * ==================
 * Shared utilities, page transitions, toast notifications, polling
 */

// ── Page Transitions ──────────────────────
document.addEventListener('DOMContentLoaded', () => {
    requestAnimationFrame(() => document.body.classList.add('page-loaded'));
});

function navigateTo(url) {
    document.body.classList.add('page-exit');
    setTimeout(() => window.location.href = url, 220);
}

document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (href && !href.startsWith('http') && !href.startsWith('#') 
        && !href.startsWith('javascript') && !href.startsWith('mailto')
        && !link.hasAttribute('target')) {
        e.preventDefault();
        navigateTo(href);
    }
});

// ── Toast Notifications ───────────────────
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>
        <button onclick="this.parentElement.remove()" style="margin-right:auto;background:none;border:none;color:inherit;cursor:pointer;font-size:16px">×</button>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── Auth Guard ────────────────────────────
function requireAuth() {
    if (!TokenManager || !TokenManager.isLoggedIn()) {
        navigateTo('login.html');
        return false;
    }
    return true;
}

// ── Role Guard ────────────────────────────
function requireAdmin() {
    const user = TokenManager.getUser();
    if (!user || !['admin', 'superadmin'].includes(user.role)) {
        showToast('ليس لديك صلاحية للوصول لهذه الصفحة', 'error');
        setTimeout(() => navigateTo('hosting-panel.html'), 1500);
        return false;
    }
    return true;
}

function requireSuperAdmin() {
    const user = TokenManager.getUser();
    if (!user || user.role !== 'superadmin') {
        showToast('يجب أن تكون Super Admin', 'error');
        return false;
    }
    return true;
}

// ── Bottom Nav Active State ───────────────
function setActiveNavItem() {
    const page = window.location.pathname.split('/').pop() || 'hosting-panel.html';
    document.querySelectorAll('.bnav-item').forEach(item => {
        const href = item.getAttribute('href') || '';
        if (href.includes(page)) item.classList.add('active');
    });
}

// ── Hide Admin-Only Elements ──────────────
function applyRoleVisibility() {
    const user = TokenManager ? TokenManager.getUser() : null;
    const isAdmin = user && ['admin', 'superadmin'].includes(user.role);
    const isSuperAdmin = user && user.role === 'superadmin';
    
    if (!isAdmin) {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
    }
    if (!isSuperAdmin) {
        document.querySelectorAll('.superadmin-only').forEach(el => el.style.display = 'none');
    }
    
    // Show superadmin button in topbar
    if (isSuperAdmin) {
        const superadminBtn = document.getElementById('superadminBtn');
        if (superadminBtn) superadminBtn.style.display = 'inline-flex';
    }
}

// ── Maintenance Mode Polling ──────────────
let maintenanceCheckInterval = null;

async function checkMaintenanceStatus() {
    try {
        const res = await fetch('/api/admin/maintenance/status');
        const data = await res.json();
        const user = TokenManager.getUser();
        const isAdmin = user && ['admin', 'superadmin'].includes(user.role);
        
        if (data.maintenance && !isAdmin) {
            showMaintenanceScreen(data.message, data.end_time);
        } else if (!data.maintenance) {
            hideMaintenanceScreen();
        }
        
        // Banner for admin
        if (data.maintenance && isAdmin) {
            showMaintenanceBanner(data.message);
        } else {
            hideMaintenanceBanner();
        }
    } catch(e) {}
}

function showMaintenanceScreen(message, endTime) {
    const screen = document.getElementById('maintenanceScreen');
    const msgEl = document.getElementById('maintenanceMsg');
    if (screen && msgEl) {
        msgEl.textContent = message || 'النظام تحت الصيانة، سيعود قريباً 🔧';
        screen.classList.add('active');
    }
}

function hideMaintenanceScreen() {
    const screen = document.getElementById('maintenanceScreen');
    if (screen) screen.classList.remove('active');
}

function showMaintenanceBanner(message) {
    let banner = document.getElementById('maintenanceBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'maintenanceBanner';
        banner.className = 'maintenance-banner';
        document.body.insertBefore(banner, document.body.firstChild);
    }
    banner.innerHTML = `🔧 وضع الصيانة مفعل: ${message || 'النظام تحت الصيانة'}`;
    banner.style.display = 'block';
}

function hideMaintenanceBanner() {
    const banner = document.getElementById('maintenanceBanner');
    if (banner) banner.style.display = 'none';
}

function startMaintenancePolling() {
    checkMaintenanceStatus();
    maintenanceCheckInterval = setInterval(checkMaintenanceStatus, 60000);
}

// ── Broadcast Messages Polling ────────────
let lastBroadcastId = null;
let broadcastCheckInterval = null;

async function checkBroadcast() {
    try {
        const token = TokenManager.getToken();
        if (!token) return;
        
        const res = await fetch('/api/admin/broadcast/active', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        if (data.broadcast && data.broadcast.id !== lastBroadcastId) {
            lastBroadcastId = data.broadcast.id;
            showBroadcastBanner(data.broadcast);
        } else if (!data.broadcast) {
            hideBroadcastBanner();
            lastBroadcastId = null;
        }
    } catch(e) {}
}

function showBroadcastBanner(broadcast) {
    let banner = document.getElementById('broadcastBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'broadcastBanner';
        banner.className = `broadcast-banner ${broadcast.type}`;
        banner.innerHTML = `
            <span id="broadcastIcon">📢</span>
            <span id="broadcastMsg"></span>
            <button onclick="hideBroadcastBanner()" style="margin-right:auto;background:none;border:none;color:inherit;cursor:pointer">×</button>
        `;
        document.body.insertBefore(banner, document.body.firstChild);
    }
    
    banner.className = `broadcast-banner ${broadcast.type}`;
    const icons = { info: 'ℹ️', warning: '⚠️', error: '❌', success: '✅' };
    banner.querySelector('#broadcastIcon').textContent = icons[broadcast.type] || '📢';
    banner.querySelector('#broadcastMsg').textContent = broadcast.message;
    banner.style.display = 'flex';
}

function hideBroadcastBanner() {
    const banner = document.getElementById('broadcastBanner');
    if (banner) banner.style.display = 'none';
}

function startBroadcastPolling() {
    checkBroadcast();
    broadcastCheckInterval = setInterval(checkBroadcast, 30000);
}

// ── Quick Links Loader ────────────────────
async function loadQuickLinks() {
    try {
        const token = TokenManager.getToken();
        if (!token) return;
        
        const res = await fetch('/api/quick-links', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        if (data.success && data.links && data.links.length > 0) {
            renderQuickLinks(data.links);
        }
    } catch(e) {
        console.error('Error loading quick links:', e);
    }
}

function renderQuickLinks(links) {
    const container = document.getElementById('quickLinksContainer');
    if (!container) return;
    
    const colorClasses = {
        cyan: 'ql-cyan',
        purple: 'ql-purple',
        green: 'ql-green',
        yellow: 'ql-yellow',
        red: 'ql-red'
    };
    
    container.innerHTML = links.map(link => `
        <div class="quick-link ${colorClasses[link.color] || 'ql-cyan'}" 
             onclick="handleQuickLinkClick('${link.type}', '${encodeURIComponent(link.content)}')">
            <span class="ql-icon">${link.icon}</span>
            <span class="ql-title">${link.title}</span>
        </div>
    `).join('');
    
    container.style.display = 'grid';
}

function handleQuickLinkClick(type, content) {
    const decodedContent = decodeURIComponent(content);
    
    switch(type) {
        case 'url':
            window.open(decodedContent, '_blank');
            break;
        case 'telegram_channel':
            window.open(`https://t.me/${decodedContent.replace('@', '')}`, '_blank');
            break;
        case 'telegram_contact':
            window.open(`https://t.me/${decodedContent.replace('@', '')}`, '_blank');
            break;
        case 'message':
            showMessageModal(decodedContent);
            break;
    }
}

function showMessageModal(content) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay open';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-title">📢 رسالة</div>
            <div class="modal-sub">${content}</div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">إغلاق</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ── Init ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (typeof TokenManager !== 'undefined') {
        applyRoleVisibility();
        setActiveNavItem();
        startMaintenancePolling();
        startBroadcastPolling();
        loadQuickLinks();
    }
});

// ── Cleanup on page unload ────────────────
window.addEventListener('beforeunload', () => {
    if (maintenanceCheckInterval) clearInterval(maintenanceCheckInterval);
    if (broadcastCheckInterval) clearInterval(broadcastCheckInterval);
});
