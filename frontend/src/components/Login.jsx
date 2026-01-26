import React, { useState } from 'react';
import './LandingPage.css'; // Re-use styles

const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        const endpoint = isRegistering ? '/api/auth/register' : '/api/auth/login';

        try {
            const formData = new URLSearchParams();
            formData.append('username', email); // OAuth2 form uses 'username'
            formData.append('password', password);

            // Register uses JSON, Login uses Form Data for OAuth2 compat
            let body;
            let headers = {};

            if (isRegistering) {
                body = JSON.stringify({ email, password, role: 'owner' });
                headers['Content-Type'] = 'application/json';
            } else {
                body = formData;
                headers['Content-Type'] = 'application/x-www-form-urlencoded';
            }

            const res = await fetch(endpoint, {
                method: 'POST',
                headers,
                body
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            // If registering, now login automatically or ask to login
            if (isRegistering) {
                setIsRegistering(false); // Switch to login view
                setError("Account created! Please log in.");
                return;
            }

            // Success Login
            onLogin(data.access_token);

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="landing-container">
            <div className="landing-card" style={{ maxWidth: '400px' }}>
                <h1>{isRegistering ? 'Create Account' : 'Welcome Back'}</h1>
                <p className="subtitle">AI Hotel Assistant SaaS</p>

                {error && <div className="error-banner" style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="input-field"
                        style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #ccc' }}
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="input-field"
                        style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #ccc' }}
                    />

                    <button type="submit" className="cta-button">
                        {isRegistering ? 'Register' : 'Login'}
                    </button>
                </form>

                <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                    {isRegistering ? 'Already have an account?' : "Don't have an account?"}
                    <span
                        onClick={() => { setIsRegistering(!isRegistering); setError(null); }}
                        style={{ color: '#007bff', cursor: 'pointer', marginLeft: '5px' }}
                    >
                        {isRegistering ? 'Login here' : 'Register here'}
                    </span>
                </p>
            </div>
        </div>
    );
};

export default Login;
