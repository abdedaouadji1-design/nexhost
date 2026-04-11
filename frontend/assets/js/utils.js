/**
 * NexHost V5 - Utilities
 * ======================
 * Helper functions and UI utilities
 */

// Format utilities
const FormatUtils = {
  // Format bytes to human readable
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  },
  
  // Format duration in seconds to human readable
  formatDuration(seconds) {
    if (seconds < 60) return seconds + 's';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's';
    if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      return hours + 'h ' + mins + 'm';
    }
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return days + 'd ' + hours + 'h';
  },
  
  // Format relative time
  formatRelativeTime(dateString) {
    if (!dateString) return 'غير معروف';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'الآن';
    if (diffMin < 60) return `منذ ${diffMin} دقيقة`;
    if (diffHour < 24) return `منذ ${diffHour} ساعة`;
    if (diffDay < 7) return `منذ ${diffDay} يوم`;
    if (diffDay < 30) return `منذ ${Math.floor(diffDay / 7)} أسبوع`;
    
    return date.toLocaleDateString('ar-SA');
  },
  
  // Format date
  formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

// Toast notification system
const Toast = {
  container: null,
  
  init() {
    if (this.container) return;
    
    this.container = document.createElement('div');
    this.container.className = 'toast-container';
    document.body.appendChild(this.container);
  },
  
  show(message, type = 'info', duration = 4000) {
    this.init();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    
    toast.innerHTML = `
      <span>${icons[type] || 'ℹ️'}</span>
      <span>${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    this.container.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
};

// Global toast function
function showToast(message, type = 'info', duration = 4000) {
  Toast.show(message, type, duration);
}

// Confirm dialog
function showConfirm(title, message, onConfirm, onCancel = null) {
  // Remove existing dialog
  const existing = document.getElementById('confirmDialogOverlay');
  if (existing) existing.remove();
  
  // Create overlay
  const overlay = document.createElement('div');
  overlay.className = 'confirm-dialog-overlay open';
  overlay.id = 'confirmDialogOverlay';
  
  overlay.innerHTML = `
    <div class="confirm-dialog">
      <div class="confirm-dialog-icon">❓</div>
      <div class="confirm-dialog-title">${title}</div>
      <div class="confirm-dialog-message">${message}</div>
      <div class="confirm-dialog-buttons">
        <button class="btn btn-ghost" id="confirmCancel">إلغاء</button>
        <button class="btn btn-danger" id="confirmOk">تأكيد</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Handle buttons
  document.getElementById('confirmCancel').onclick = () => {
    overlay.remove();
    if (onCancel) onCancel();
  };
  
  document.getElementById('confirmOk').onclick = () => {
    overlay.remove();
    onConfirm();
  };
  
  // Close on overlay click
  overlay.onclick = (e) => {
    if (e.target === overlay) {
      overlay.remove();
      if (onCancel) onCancel();
    }
  };
  
  // Close on Escape
  const handleEscape = (e) => {
    if (e.key === 'Escape') {
      overlay.remove();
      if (onCancel) onCancel();
      document.removeEventListener('keydown', handleEscape);
    }
  };
  document.addEventListener('keydown', handleEscape);
}

// Loading overlay
const Loading = {
  overlay: null,
  
  show(message = 'جاري التحميل...') {
    if (this.overlay) this.hide();
    
    this.overlay = document.createElement('div');
    this.overlay.className = 'loading-overlay';
    this.overlay.innerHTML = `
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <div style="color:var(--muted);font-size:14px">${message}</div>
      </div>
    `;
    
    document.body.appendChild(this.overlay);
  },
  
  hide() {
    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
    }
  }
};

// Debounce function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Throttle function
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Copy to clipboard
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('تم النسخ', 'success');
  } catch (err) {
    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('تم النسخ', 'success');
  }
}

// Download file
function downloadFile(content, filename, contentType = 'text/plain') {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Escape HTML
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Generate random ID
function generateId(length = 8) {
  return Math.random().toString(36).substring(2, 2 + length);
}

// Check if element is in viewport
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

// Animate element
function animateElement(element, animation, duration = 300) {
  element.style.animation = `${animation} ${duration}ms ease`;
  setTimeout(() => {
    element.style.animation = '';
  }, duration);
}

// Local storage helpers
const Storage = {
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error('Storage error:', e);
      return false;
    }
  },
  
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
      console.error('Storage error:', e);
      return defaultValue;
    }
  },
  
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      console.error('Storage error:', e);
      return false;
    }
  },
  
  clear() {
    try {
      localStorage.clear();
      return true;
    } catch (e) {
      console.error('Storage error:', e);
      return false;
    }
  }
};

// Session storage helpers
const SessionStorage = {
  set(key, value) {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error('Session storage error:', e);
      return false;
    }
  },
  
  get(key, defaultValue = null) {
    try {
      const item = sessionStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
      console.error('Session storage error:', e);
      return defaultValue;
    }
  },
  
  remove(key) {
    try {
      sessionStorage.removeItem(key);
      return true;
    } catch (e) {
      console.error('Session storage error:', e);
      return false;
    }
  }
};

// Mobile detection
const isMobile = {
  Android() {
    return /Android/i.test(navigator.userAgent);
  },
  BlackBerry() {
    return /BlackBerry/i.test(navigator.userAgent);
  },
  iOS() {
    return /iPhone|iPad|iPod/i.test(navigator.userAgent);
  },
  Opera() {
    return /Opera Mini/i.test(navigator.userAgent);
  },
  Windows() {
    return /IEMobile/i.test(navigator.userAgent);
  },
  any() {
    return this.Android() || this.BlackBerry() || this.iOS() || this.Opera() || this.Windows();
  }
};

// Page visibility API
const PageVisibility = {
  isHidden() {
    return document.hidden || document.webkitHidden || document.mozHidden || document.msHidden;
  },
  
  onChange(callback) {
    const eventName = document.hidden !== undefined ? 'visibilitychange' :
                      document.webkitHidden !== undefined ? 'webkitvisibilitychange' :
                      document.mozHidden !== undefined ? 'mozvisibilitychange' :
                      document.msHidden !== undefined ? 'msvisibilitychange' : null;
    
    if (eventName) {
      document.addEventListener(eventName, callback);
      return () => document.removeEventListener(eventName, callback);
    }
    return () => {};
  }
};

// Initialize page
function initPage() {
  // Add page loaded class
  document.body.classList.add('page-loaded');
  
  // Handle page unload
  window.addEventListener('beforeunload', () => {
    document.body.classList.add('page-exit');
  });
  
  // Check for broadcast messages (if admin)
  checkBroadcast();
  setInterval(checkBroadcast, 30000);
}

// Check for broadcast messages
async function checkBroadcast() {
  try {
    const result = await AdminAPI.getMaintenanceStatus();
    if (result.broadcast) {
      const banner = document.getElementById('broadcastBanner');
      const msg = document.getElementById('broadcastMsg');
      const icon = document.getElementById('broadcastIcon');
      
      if (banner && msg) {
        msg.textContent = result.broadcast.message;
        
        // Set icon based on type
        const icons = {
          info: 'ℹ️',
          warning: '⚠️',
          error: '❌',
          success: '✅'
        };
        if (icon) icon.textContent = icons[result.broadcast.type] || '📢';
        
        // Set class based on type
        banner.className = `broadcast-banner ${result.broadcast.type} show`;
      }
    }
  } catch (e) {}
}

// Run init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPage);
} else {
  initPage();
}
