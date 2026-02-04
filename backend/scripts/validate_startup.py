"""
Startup validation script - verifies all required configuration and services.

Run this before starting the application to ensure everything is properly configured:
    python scripts/validate_startup.py

Exit codes:
    0: All checks passed
    1: Validation failed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def print_header(message):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def print_check(name, passed, message=""):
    """Print check result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"       {message}")
    return passed


def validate_environment_variables():
    """Validate required environment variables"""
    print_header("Environment Variables")
    
    all_passed = True
    
    # Critical variables
    admin_key = os.getenv("ADMIN_API_KEY")
    all_passed &= print_check(
        "ADMIN_API_KEY",
        admin_key is not None and len(admin_key) > 0,
        "Required for admin endpoints"
    )
    
    # AI Service
    google_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    has_ai = google_key or openai_key
    all_passed &= print_check(
        "AI API Keys",
        has_ai,
        f"Google: {'✓' if google_key else '✗'}, OpenAI: {'✓' if openai_key else '✗'}"
    )
    
    # Optional but recommended
    environment = os.getenv("ENVIRONMENT", "development")
    print_check("ENVIRONMENT", True, f"Set to: {environment}")
    
    log_level = os.getenv("LOG_LEVEL", "INFO")
    print_check("LOG_LEVEL", True, f"Set to: {log_level}")
    
    return all_passed


def validate_database():
    """Validate database connectivity"""
    print_header("Database")
    
    try:
        from app.db.session import get_db_connection
        
        # Test connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        return print_check(
            "Database Connection",
            result is not None,
            f"Connected successfully, {table_count} tables found"
        )
    
    except Exception as e:
        return print_check(
            "Database Connection",
            False,
            f"Error: {str(e)[:100]}"
        )


def validate_directories():
    """Validate required directories exist"""
    print_header("Directories")
    
    all_passed = True
    
    # Required directories
    required_dirs = [
        ("logs", "Log files directory"),
        ("backend/app", "Application code"),
        ("backend/app/data", "Knowledge base documents"),
    ]
    
    for dir_path, description in required_dirs:
        exists = Path(dir_path).exists()
        all_passed &= print_check(
            dir_path,
            exists,
            description
        )
        
        # Create logs directory if it doesn't exist
        if dir_path == "logs" and not exists:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"       Created logs directory")
                all_passed = True
            except Exception as e:
                print(f"       Failed to create: {e}")
    
    return all_passed


def validate_imports():
    """Validate critical imports"""
    print_header("Python Dependencies")
    
    all_passed = True
    
    # Critical imports
    imports = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("sqlite3", "Database driver"),
        ("google.generativeai", "Google AI"),
        ("pydantic", "Data validation"),
        ("dotenv", "Environment loading"),
    ]
    
    for module_name, description in imports:
        try:
            __import__(module_name)
            all_passed &= print_check(module_name, True, description)
        except ImportError as e:
            all_passed &= print_check(
                module_name,
                False,
                f"Not installed - {description}"
            )
    
    return all_passed


def validate_config():
    """Validate configuration settings"""
    print_header("Configuration")
    
    try:
        from app.core.config import get_settings, validate_settings
        
        # This will raise if validation fails
        settings = validate_settings()
        
        return print_check(
            "Configuration Validation",
            True,
            f"Environment: {settings.environment}, Debug: {settings.debug}"
        )
    
    except Exception as e:
        return print_check(
            "Configuration Validation",
            False,
            f"Error: {str(e)[:100]}"
        )


def validate_health_endpoints():
    """Validate that app can be imported and routes exist"""
    print_header("Application Setup")
    
    try:
        from app.app_factory import create_app
        
        app = create_app()
        
        # Check routes exist
        routes = [route.path for route in app.routes]
        has_health = "/health" in routes
        
        return print_check(
            "Application Import",
            has_health,
            f"Found {len(routes)} routes, health endpoint: {'✓' if has_health else '✗'}"
        )
    
    except Exception as e:
        return print_check(
            "Application Import",
            False,
            f"Error: {str(e)[:100]}"
        )


def main():
    """Run all validation checks"""
    print("\n" + "🔍" * 30)
    print("  STARTUP VALIDATION")
    print("🔍" * 30)
    
    # Run all checks
    checks = [
        validate_environment_variables(),
        validate_directories(),
        validate_imports(),
        validate_database(),
        validate_config(),
        validate_health_endpoints(),
    ]
    
    # Summary
    print_header("Validation Summary")
    
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    if all(checks):
        print(f"✅ ALL CHECKS PASSED ({passed_checks}/{total_checks})")
        print("\n🚀 Application is ready to start!")
        print("   Run: uvicorn app.main:app --host 0.0.0.0 --port 8010\n")
        return 0
    else:
        print(f"❌ VALIDATION FAILED ({passed_checks}/{total_checks} passed)")
        print("\n⚠️  Please fix the issues above before starting the application.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
