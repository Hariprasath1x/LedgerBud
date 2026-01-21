// Authentication functions

// Check if user is authenticated
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn || isLoggedIn !== 'true') {
        window.location.href = 'index.html';
    }
}

// Logout function
function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    window.location.href = 'index.html';
}

// Get current user
function getCurrentUser() {
    return {
        email: localStorage.getItem('userEmail') || '',
        name: localStorage.getItem('userName') || 'User'
    };
}
