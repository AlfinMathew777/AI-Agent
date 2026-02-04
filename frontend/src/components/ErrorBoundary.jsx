import React from 'react';

/**
 * Error Boundary Component
 * 
 * Catches React component errors and displays a fallback UI
 * instead of crashing the entire application.
 * 
 * Usage:
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    static getDerivedStateFromError(error) {
        // Update state so next render shows fallback UI
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // Log error details
        console.error('Error caught by ErrorBoundary:', error);
        console.error('Error info:', errorInfo);

        // Store in state for display
        this.state = { ...this.state, error, errorInfo };

        // TODO: Send to error tracking service (Sentry, etc.)
        // logErrorToService(error, errorInfo);
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={styles.container}>
                    <div style={styles.content}>
                        <h1 style={styles.title}>⚠️ Something Went Wrong</h1>
                        <p style={styles.message}>
                            We're sorry, but something unexpected happened.
                            The error has been logged.
                        </p>

                        {this.state.error && (
                            <details style={styles.details}>
                                <summary style={styles.summary}>Error Details</summary>
                                <pre style={styles.errorText}>
                                    {this.state.error.toString()}
                                </pre>
                                {this.state.errorInfo && (
                                    <pre style={styles.stackTrace}>
                                        {this.state.errorInfo.componentStack}
                                    </pre>
                                )}
                            </details>
                        )}

                        <div style={styles.actions}>
                            <button
                                onClick={this.handleReset}
                                style={styles.resetButton}
                            >
                                Try Again
                            </button>
                            <button
                                onClick={() => window.location.reload()}
                                style={styles.reloadButton}
                            >
                                Reload Page
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

// Styles
const styles = {
    container: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        padding: '2rem'
    },
    content: {
        maxWidth: '600px',
        backgroundColor: 'white',
        padding: '3rem',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        textAlign: 'center'
    },
    title: {
        fontSize: '2rem',
        fontWeight: '600',
        color: '#1a1a1a',
        marginBottom: '1rem'
    },
    message: {
        fontSize: '1rem',
        color: '#666',
        marginBottom: '2rem',
        lineHeight: '1.6'
    },
    details: {
        textAlign: 'left',
        backgroundColor: '#f9f9f9',
        padding: '1rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        border: '1px solid #e5e5e5'
    },
    summary: {
        cursor: 'pointer',
        fontWeight: '600',
        marginBottom: '0.5rem',
        color: '#ef4444'
    },
    errorText: {
        fontSize: '0.875rem',
        color: '#dc2626',
        overflow: 'auto',
        marginTop: '0.5rem'
    },
    stackTrace: {
        fontSize: '0.75rem',
        color: '#666',
        overflow: 'auto',
        marginTop: '0.5rem',
        maxHeight: '200px'
    },
    actions: {
        display: 'flex',
        gap: '1rem',
        justifyContent: 'center'
    },
    resetButton: {
        padding: '0.75rem 1.5rem',
        backgroundColor: '#d4af37',
        color: '#1a1a1a',
        border: 'none',
        borderRadius: '8px',
        fontSize: '1rem',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    reloadButton: {
        padding: '0.75rem 1.5rem',
        backgroundColor: '#f3f4f6',
        color: '#1a1a1a',
        border: '1px solid #e5e5e5',
        borderRadius: '8px',
        fontSize: '1rem',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.2s'
    }
};

export default ErrorBoundary;
