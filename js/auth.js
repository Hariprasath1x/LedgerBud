/**
 * ============================================
 * LedgerBud - Firebase Authentication Module
 * ============================================
 * 
 * This module handles all authentication operations using Firebase Auth.
 * Uses Firebase Web SDK v9+ with modular imports via CDN.
 * 
 * Features:
 * - Email/Password Registration with Email Verification
 * - Login with Email Verification Check
 * - Password Reset via Email
 * - Session Management
 * 
 * @author LedgerBud Team
 * @version 2.0.0
 */

// ============================================
// FIREBASE CONFIGURATION
// ============================================
// Replace these values with your Firebase project config
// You can find these in: Firebase Console > Project Settings > Web App
const firebaseConfig = {
    apiKey: "AIzaSyDLQgC1Jbor7LPBDbdHCJhwL2a84_3Mo3A",
    authDomain: "ledgerbud.firebaseapp.com",
    projectId: "ledgerbud",
    storageBucket: "ledgerbud.firebasestorage.app",
    messagingSenderId: "876014641992",
    appId: "1:876014641992:web:a8744d057699e90c26897d"
  };


// ============================================
// FIREBASE INITIALIZATION (v9+ Modular SDK)
// ============================================
// We use the compat version for simpler CDN usage while maintaining modern patterns

let auth = null;
let firebaseInitialized = false;

/**
 * Initialize Firebase App and Auth
 * This function should be called before any auth operations
 */
function initializeFirebase() {
    // Check if Firebase is already initialized
    if (firebaseInitialized && auth) {
        return auth;
    }
    
    try {
        // Initialize Firebase App (using compat for CDN compatibility)
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        
        // Get Firebase Auth instance
        auth = firebase.auth();
        firebaseInitialized = true;
        
        console.log('✅ Firebase initialized successfully');
        return auth;
    } catch (error) {
        console.error('❌ Firebase initialization failed:', error);
        throw new Error('Failed to initialize Firebase. Check your configuration.');
    }
}

// ============================================
// USER REGISTRATION
// ============================================

/**
 * Register a new user with email and password
 * After registration, sends a verification email
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password (min 6 characters)
 * @param {string} displayName - User's display name (optional)
 * @returns {Promise<Object>} - Result object with success status and message
 * 
 * Flow:
 * 1. Create user account with email/password
 * 2. Update user profile with display name
 * 3. Send email verification link
 * 4. User must verify email before logging in
 */
async function registerUser(email, password, displayName = '') {
    try {
        // Step 1: Ensure Firebase is initialized
        const authInstance = initializeFirebase();
        
        // Step 2: Create user with email and password
        // Firebase will throw an error if email is already in use or password is weak
        const userCredential = await authInstance.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        console.log('✅ User account created:', user.uid);
        
        // Step 3: Update the user's display name if provided
        if (displayName) {
            await user.updateProfile({
                displayName: displayName
            });
            console.log('✅ Display name set:', displayName);
        }
        
        // Step 4: Send email verification
        // Firebase will send a verification link to the user's email
        await user.sendEmailVerification();
        console.log('✅ Verification email sent to:', email);
        
        // Step 5: Sign out the user (they must verify email first)
        await authInstance.signOut();
        
        return {
            success: true,
            message: 'Registration successful! Please check your email to verify your account before logging in.',
            user: {
                uid: user.uid,
                email: user.email,
                displayName: displayName
            }
        };
        
    } catch (error) {
        // Handle specific Firebase Auth errors with user-friendly messages
        const errorMessage = getAuthErrorMessage(error.code);
        console.error('❌ Registration failed:', error.code, error.message);
        
        return {
            success: false,
            message: errorMessage,
            errorCode: error.code
        };
    }
}

// ============================================
// USER LOGIN
// ============================================

/**
 * Login user with email and password
 * IMPORTANT: Login is blocked if email is not verified
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise<Object>} - Result object with success status and user data
 * 
 * Flow:
 * 1. Sign in with email/password
 * 2. Check if email is verified
 * 3. If not verified, sign out and prompt to verify
 * 4. If verified, allow access
 */
async function loginUser(email, password) {
    try {
        // Step 1: Ensure Firebase is initialized
        const authInstance = initializeFirebase();
        
        // Step 2: Sign in with email and password
        const userCredential = await authInstance.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        console.log('✅ Sign-in successful for:', user.email);
        
        // Step 3: CRITICAL - Check if email is verified
        // This is a security requirement - unverified users cannot access the app
        if (!user.emailVerified) {
            console.log('⚠️ Email not verified, signing out user');
            
            // Sign out the unverified user
            await authInstance.signOut();
            
            return {
                success: false,
                message: 'Please verify your email address before logging in. Check your inbox for the verification link.',
                emailVerified: false,
                canResendVerification: true
            };
        }
        
        // Step 4: Email is verified - Store session data
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('userEmail', user.email);
        localStorage.setItem('userName', user.displayName || email.split('@')[0]);
        localStorage.setItem('userUid', user.uid);
        
        console.log('✅ Login complete, email verified');
        
        return {
            success: true,
            message: 'Login successful!',
            user: {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName,
                emailVerified: user.emailVerified
            }
        };
        
    } catch (error) {
        // Handle specific Firebase Auth errors
        const errorMessage = getAuthErrorMessage(error.code);
        console.error('❌ Login failed:', error.code, error.message);
        
        return {
            success: false,
            message: errorMessage,
            errorCode: error.code
        };
    }
}

// ============================================
// PASSWORD RESET
// ============================================

/**
 * Send password reset email to user
 * 
 * @param {string} email - User's email address
 * @returns {Promise<Object>} - Result object with success status
 * 
 * Flow:
 * 1. Send password reset email via Firebase
 * 2. User clicks link in email
 * 3. User sets new password on Firebase's reset page
 */
async function resetPassword(email) {
    try {
        // Step 1: Ensure Firebase is initialized
        const authInstance = initializeFirebase();
        
        // Step 2: Send password reset email
        // Firebase handles the reset flow automatically
        await authInstance.sendPasswordResetEmail(email);
        
        console.log('✅ Password reset email sent to:', email);
        
        return {
            success: true,
            message: 'Password reset email sent! Please check your inbox and follow the instructions to reset your password.'
        };
        
    } catch (error) {
        // Handle specific Firebase Auth errors
        const errorMessage = getAuthErrorMessage(error.code);
        console.error('❌ Password reset failed:', error.code, error.message);
        
        return {
            success: false,
            message: errorMessage,
            errorCode: error.code
        };
    }
}

// ============================================
// RESEND VERIFICATION EMAIL
// ============================================

/**
 * Resend verification email for users who haven't verified
 * Must be called while user is signed in
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password (needed to sign in temporarily)
 * @returns {Promise<Object>} - Result object with success status
 */
async function resendVerificationEmail(email, password) {
    try {
        const authInstance = initializeFirebase();
        
        // Sign in temporarily to resend verification
        const userCredential = await authInstance.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        if (user.emailVerified) {
            await authInstance.signOut();
            return {
                success: false,
                message: 'Your email is already verified. You can log in now.'
            };
        }
        
        // Resend verification email
        await user.sendEmailVerification();
        await authInstance.signOut();
        
        console.log('✅ Verification email resent to:', email);
        
        return {
            success: true,
            message: 'Verification email resent! Please check your inbox.'
        };
        
    } catch (error) {
        const errorMessage = getAuthErrorMessage(error.code);
        console.error('❌ Resend verification failed:', error.code);
        
        return {
            success: false,
            message: errorMessage,
            errorCode: error.code
        };
    }
}

// ============================================
// ERROR MESSAGE HELPER
// ============================================

/**
 * Convert Firebase error codes to user-friendly messages
 * This makes error messages easier to understand for users
 * 
 * @param {string} errorCode - Firebase error code
 * @returns {string} - User-friendly error message
 */
function getAuthErrorMessage(errorCode) {
    const errorMessages = {
        // Registration errors
        'auth/email-already-in-use': 'This email is already registered. Please try logging in or use a different email.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/operation-not-allowed': 'Email/password sign-in is not enabled. Please contact support.',
        'auth/weak-password': 'Password is too weak. Please use at least 6 characters with a mix of letters and numbers.',
        
        // Login errors
        'auth/user-disabled': 'This account has been disabled. Please contact support.',
        'auth/user-not-found': 'No account found with this email. Please register first.',
        'auth/wrong-password': 'Incorrect password. Please try again or reset your password.',
        'auth/invalid-credential': 'Invalid email or password. Please check your credentials and try again.',
        'auth/too-many-requests': 'Too many failed attempts. Please wait a few minutes before trying again.',
        
        // Password reset errors
        'auth/expired-action-code': 'This password reset link has expired. Please request a new one.',
        'auth/invalid-action-code': 'This password reset link is invalid. Please request a new one.',
        
        // Network errors
        'auth/network-request-failed': 'Network error. Please check your internet connection and try again.',
        
        // Default error
        'default': 'An unexpected error occurred. Please try again.'
    };
    
    return errorMessages[errorCode] || errorMessages['default'];
}

// ============================================
// SESSION MANAGEMENT
// ============================================

// Check if user is authenticated
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn || isLoggedIn !== 'true') {
        window.location.href = 'index.html';
    }
}

// Logout function with Firebase sign out
async function logout() {
    try {
        // Sign out from Firebase if initialized
        if (firebaseInitialized && auth) {
            await auth.signOut();
            console.log('✅ Firebase sign out successful');
        }
    } catch (error) {
        console.error('Firebase sign out error:', error);
    }
    
    // Clear all local storage data
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userUid');
    localStorage.removeItem('userProfilePicture');
    
    // Redirect to login page
    window.location.href = 'index.html';
}

// Show logout confirmation modal
function showLogoutConfirmation() {
    document.getElementById('logoutModal').classList.remove('hidden');
}

// Hide logout confirmation modal
function hideLogoutConfirmation() {
    document.getElementById('logoutModal').classList.add('hidden');
}

// Toggle profile dropdown menu
function toggleProfileDropdown() {
    const dropdown = document.getElementById('profileDropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('profileDropdown');
    const profileBtn = document.getElementById('profileBtn');
    
    if (dropdown && profileBtn) {
        // Check if click is outside the dropdown and profile button
        if (!dropdown.contains(event.target) && !profileBtn.contains(event.target)) {
            dropdown.classList.add('hidden');
        }
    }
});

// Get current user
function getCurrentUser() {
    return {
        email: localStorage.getItem('userEmail') || '',
        name: localStorage.getItem('userName') || 'User',
        profilePicture: localStorage.getItem('userProfilePicture') || ''
    };
}

// Update user profile
function updateUserProfile(data) {
    if (data.name) {
        localStorage.setItem('userName', data.name);
    }
    if (data.email) {
        localStorage.setItem('userEmail', data.email);
    }
    if (data.profilePicture !== undefined) {
        localStorage.setItem('userProfilePicture', data.profilePicture);
    }
}

// Change password
function changePassword(currentPassword, newPassword) {
    const storedPassword = localStorage.getItem('userPassword');
    if (storedPassword === currentPassword) {
        localStorage.setItem('userPassword', newPassword);
        return { success: true, message: 'Password changed successfully' };
    }
    return { success: false, message: 'Current password is incorrect' };
}

// Delete all transactions and history
function deleteAllTransactionsAndHistory() {
    localStorage.removeItem('transactions');
    return { success: true, message: 'All transactions and history deleted' };
}

// Remove account permanently
function removeAccountPermanently() {
    const userEmail = localStorage.getItem('userEmail');
    // Remove all user data
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userPassword');
    localStorage.removeItem('userProfilePicture');
    localStorage.removeItem('transactions');
    // Remove from users list if exists
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const updatedUsers = users.filter(u => u.email !== userEmail);
    localStorage.setItem('users', JSON.stringify(updatedUsers));
    window.location.href = 'index.html';
}

// Show profile modal
function showProfileModal() {
    const modal = document.getElementById('profileModal');
    const user = getCurrentUser();
    
    // Populate form fields
    document.getElementById('profileName').value = user.name;
    document.getElementById('profileEmail').value = user.email;
    
    // Set profile picture preview
    const profilePreview = document.getElementById('profilePicturePreview');
    if (user.profilePicture) {
        profilePreview.src = user.profilePicture;
        profilePreview.classList.remove('hidden');
        document.getElementById('profilePicturePlaceholder').classList.add('hidden');
    } else {
        profilePreview.classList.add('hidden');
        document.getElementById('profilePicturePlaceholder').classList.remove('hidden');
    }
    
    // Update theme selector
    if (typeof updateThemeSelector === 'function') {
        updateThemeSelector();
    }
    
    modal.classList.remove('hidden');
}

// Hide profile modal
function hideProfileModal() {
    document.getElementById('profileModal').classList.add('hidden');
    // Reset password fields
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmNewPassword').value = '';
}

// Handle profile picture upload
function handleProfilePictureUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64Image = e.target.result;
            document.getElementById('profilePicturePreview').src = base64Image;
            document.getElementById('profilePicturePreview').classList.remove('hidden');
            document.getElementById('profilePicturePlaceholder').classList.add('hidden');
            updateUserProfile({ profilePicture: base64Image });
            updateProfileButtonImage();
        };
        reader.readAsDataURL(file);
    }
}

// Update profile button image
function updateProfileButtonImage() {
    const user = getCurrentUser();
    const profileBtnImg = document.getElementById('profileBtnImg');
    const profileBtnPlaceholder = document.getElementById('profileBtnPlaceholder');
    
    if (profileBtnImg && profileBtnPlaceholder) {
        if (user.profilePicture) {
            profileBtnImg.src = user.profilePicture;
            profileBtnImg.classList.remove('hidden');
            profileBtnPlaceholder.classList.add('hidden');
        } else {
            profileBtnImg.classList.add('hidden');
            profileBtnPlaceholder.classList.remove('hidden');
        }
    }
}
