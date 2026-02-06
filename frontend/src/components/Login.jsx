import React, { useState } from 'react';
import './LandingPage.css';

const Login = ({ onLogin, isModal = false, onClose }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email.trim() || !password.trim()) {
            setError('Please enter both email and password');
            return;
        }

        setError(null);
        setLoading(true);

        const backendUrl = 'http://127.0.0.1:8011';
        const endpoint = isRegistering ? `${backendUrl}/auth/register` : `${backendUrl}/auth/login`;

        try {
            let body;
            let headers = {};

            if (isRegistering) {
                body = JSON.stringify({ email, password, role: 'owner' });
                headers['Content-Type'] = 'application/json';
            } else {
                // Login: form-urlencoded
                body = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
                headers['Content-Type'] = 'application/x-www-form-urlencoded';
            }

            // Use fetch directly - the interceptor should skip /auth/ endpoints anyway
            const res = await fetch(endpoint, {
                method: 'POST',
                headers,
                body,
                mode: 'cors'
            });

            const responseText = await res.text();
            console.log('Response status:', res.status);
            console.log('Response text:', responseText);

            if (!res.ok) {
                let errorMsg = 'Login failed';
                try {
                    const errorData = JSON.parse(responseText);
                    if (errorData.detail) {
                        if (typeof errorData.detail === 'string') {
                            errorMsg = errorData.detail;
                        } else if (errorData.detail.error) {
                            errorMsg = errorData.detail.error;
                        }
                    } else {
                        errorMsg = errorData.message || errorData.error || errorMsg;
                    }
                } catch {
                    errorMsg = responseText || `Server error: ${res.status}`;
                }
                throw new Error(errorMsg);
            }

            // Parse successful response
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (parseErr) {
                throw new Error('Invalid response format from server');
            }

            // Check for required fields
            if (!data.access_token) {
                throw new Error('Server did not return an access token');
            }

            // Success - call onLogin callback
            console.log('Login successful, token received');
            if (onLogin) {
                onLogin(data.access_token, data.role || 'staff');
            } else {
                console.error('onLogin callback is not defined!');
                setError('Login successful but callback failed. Please refresh the page.');
            }

        } catch (err) {
            console.error('Login error:', err);
            let errorMsg = err.message || 'An error occurred during login';
            
            if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
                errorMsg = 'Cannot connect to backend server. Please ensure the backend is running on port 8011.';
            } else if (err.message.includes('CORS')) {
                errorMsg = 'CORS error. Please check backend CORS configuration.';
            }
            
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const content = (
        <div className="landing-card" style={{ maxWidth: '400px', position: 'relative' }}>
            {isModal && (
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        background: 'transparent',
                        border: 'none',
                        fontSize: '1.5rem',
                        cursor: 'pointer',
                        color: '#666',
                        padding: '0.5rem'
                    }}
                    aria-label="Close"
                >
                    ✕
                </button>
            )}
            <h1>{isRegistering ? 'Create Account' : 'Staff & Admin Login'}</h1>
            <p className="subtitle">Southern Horizons Hotel Portal</p>

            {error && (
                <div className="error-banner" style={{ 
                    color: 'red', 
                    marginBottom: '1rem', 
                    padding: '0.75rem',
                    background: '#fee',
                    borderRadius: '4px',
                    border: '1px solid #fcc'
                }}>
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                    className="input-field"
                    style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    className="input-field"
                    style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />

                <button 
                    type="submit" 
                    className="cta-button"
                    disabled={loading}
                >
                    {loading ? 'Processing...' : (isRegistering ? 'Register' : 'Login')}
                </button>
            </form>

            <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                {isRegistering ? 'Already have an account?' : "Don't have an account?"}
                <span
                    onClick={() => { 
                        if (!loading) {
                            setIsRegistering(!isRegistering); 
                            setError(null); 
                        }
                    }}
                    style={{ 
                        color: '#007bff', 
                        cursor: loading ? 'not-allowed' : 'pointer', 
                        marginLeft: '5px',
                        opacity: loading ? 0.5 : 1
                    }}
                >
                    {isRegistering ? 'Login here' : 'Register here'}
                </span>
            </p>
        </div>
    );

    if (isModal) {
        return (
            <div
                className="login-modal-backdrop"
                onClick={onClose}
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.75)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10000,
                    backdropFilter: 'blur(5px)'
                }}
            >
                <div onClick={(e) => e.stopPropagation()}>
                    {content}
                </div>
            </div>
        );
    }

    return (
        <div className="landing-container">
            {content}
        </div>
    );
};

export default Login;
