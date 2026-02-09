// Theme management functions

const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
    SYSTEM: 'system',
    HIGH_CONTRAST: 'high-contrast'
};

// Get current theme from localStorage
function getCurrentTheme() {
    return localStorage.getItem('ledgerbud-theme') || THEMES.LIGHT;
}

// Set theme
function setTheme(theme) {
    localStorage.setItem('ledgerbud-theme', theme);
    applyTheme(theme);
    updateThemeSelector();
    console.log('Theme saved:', theme);
}

// Apply theme to document
function applyTheme(theme) {
    const root = document.documentElement;
    const body = document.body;
    
    // Remove all theme classes from html element
    root.classList.remove('dark', 'high-contrast', 'dark-mode', 'high-contrast-mode');
    
    // Remove from body if it exists
    if (body) {
        body.classList.remove('dark-mode', 'high-contrast-mode');
    }
    
    let effectiveTheme = theme;
    
    // Handle system theme
    if (theme === THEMES.SYSTEM) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        effectiveTheme = prefersDark ? THEMES.DARK : THEMES.LIGHT;
    }
    
    // Apply theme classes to both html and body
    if (effectiveTheme === THEMES.DARK) {
        root.classList.add('dark', 'dark-mode');
        if (body) body.classList.add('dark-mode');
    } else if (effectiveTheme === THEMES.HIGH_CONTRAST) {
        root.classList.add('high-contrast', 'high-contrast-mode');
        if (body) body.classList.add('high-contrast-mode');
    }
    
    // Store effective theme for reference
    root.setAttribute('data-theme', effectiveTheme);
    if (body) body.setAttribute('data-theme', effectiveTheme);
}

// Update theme selector UI
function updateThemeSelector() {
    const currentTheme = getCurrentTheme();
    const themeOptions = document.querySelectorAll('.theme-option');
    
    themeOptions.forEach(option => {
        const isSelected = option.dataset.theme === currentTheme;
        option.classList.toggle('ring-2', isSelected);
        option.classList.toggle('ring-blue-500', isSelected);
        option.classList.toggle('ring-offset-2', isSelected);
    });
}

// Initialize theme on page load
function initializeTheme() {
    const theme = getCurrentTheme();
    applyTheme(theme);
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (getCurrentTheme() === THEMES.SYSTEM) {
            applyTheme(THEMES.SYSTEM);
        }
    });
}

// Apply theme to html element immediately (before body loads)
(function() {
    const theme = localStorage.getItem('ledgerbud-theme') || 'light';
    let effectiveTheme = theme;
    
    if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        effectiveTheme = prefersDark ? 'dark' : 'light';
    }
    
    if (effectiveTheme === 'dark') {
        document.documentElement.classList.add('dark', 'dark-mode');
    } else if (effectiveTheme === 'high-contrast') {
        document.documentElement.classList.add('high-contrast', 'high-contrast-mode');
    }
})();

// Apply theme again when DOM is ready (for body element)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
} else {
    initializeTheme();
}
