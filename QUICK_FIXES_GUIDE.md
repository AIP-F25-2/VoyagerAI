# Quick Fixes Guide - Start Here

This guide provides step-by-step instructions for fixing the most critical issues immediately.

---

## 🚀 Fix #1: Centralized API Client (2 hours)

### Step 1: Create API Client Utility

Create `frontend/lib/apiClient.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    // Add auth token if available
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('voyagerai_token');
      if (token) {
        config.headers = {
          ...config.headers,
          'Authorization': `Bearer ${token}`,
        };
      }
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
```

### Step 2: Update Environment Variables

Add to `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:5001
```

Add to `frontend/.env.local.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:5001
```

### Step 3: Replace Hardcoded URLs

**Example: Replace in `AIChat.tsx`:**
```typescript
// OLD:
const response = await fetch("http://127.0.0.1:5001/api/llm/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: text, email: user?.email || null, history: history }),
});

// NEW:
import { apiClient } from '@/lib/apiClient';

const response = await apiClient.post('/api/llm/chat', {
  message: text,
  email: user?.email || null,
  history: history,
});
```

**Priority Files to Update:**
1. `frontend/components/AIChat.tsx`
2. `frontend/components/Recommendations.tsx`
3. `frontend/app/travel-plans/page.tsx`
4. `frontend/app/travel-plans/[id]/page.tsx`
5. All files in `frontend/app/api/`

---

## 🔒 Fix #2: JWT Secret Key Security (30 minutes)

### Step 1: Update `backend/app/models.py`

Find the `generate_token` method and update:

```python
def generate_token(self):
    """Generate JWT token for the user"""
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    
    payload = {
        'user_id': self.id,
        'email': self.email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')
```

Do the same for `verify_token`, `generate_verification_token`, and `generate_password_reset_token`.

### Step 2: Add Startup Validation

In `backend/app/__init__.py`, add:

```python
def create_app():
    app = Flask(__name__)
    
    # Validate required environment variables
    required_vars = ['JWT_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # ... rest of the code
```

### Step 3: Update `.env.example`

Add to `env.example`:
```
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### Step 4: Generate Strong Secret

Run this to generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the output to your `.env` file.

---

## 🛡️ Fix #3: Input Sanitization (1 hour)

### Step 1: Install Bleach

```bash
cd backend
source venv/bin/activate
pip install bleach
```

### Step 2: Create Sanitization Utility

Create `backend/app/utils/sanitizer.py`:

```python
import bleach
from html import unescape

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title']
}

def sanitize_html(text: str) -> str:
    """Sanitize HTML input to prevent XSS"""
    if not text:
        return ""
    
    # Decode HTML entities first
    text = unescape(text)
    
    # Sanitize
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return cleaned.strip()

def sanitize_text(text: str) -> str:
    """Sanitize plain text input"""
    if not text:
        return ""
    
    # Remove HTML tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    
    return cleaned.strip()
```

### Step 3: Apply to User Inputs

In `backend/app/routes.py`, import and use:

```python
from .utils.sanitizer import sanitize_text, sanitize_html

@bp.route("/events/reviews", methods=["POST"])
def create_review():
    data = request.get_json()
    review_text = sanitize_text(data.get("review", ""))
    rating = data.get("rating")
    # ... rest of the code
```

Apply to:
- Event reviews
- User descriptions
- Travel plan descriptions
- Any user-generated content

---

## ⚠️ Fix #4: Error Handling (2 hours)

### Step 1: Create Error Handler

Create `backend/app/utils/error_handler.py`:

```python
from flask import jsonify
import logging
import os

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API exception"""
    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

def handle_error(error):
    """Global error handler"""
    if isinstance(error, APIError):
        response = {
            "success": False,
            "error": error.message,
            "error_code": error.error_code
        }
        return jsonify(response), error.status_code
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    # Don't expose internal errors in production
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    response = {
        "success": False,
        "error": "An internal error occurred" if is_production else str(error)
    }
    
    return jsonify(response), 500

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    app.register_error_handler(APIError, handle_error)
    app.register_error_handler(Exception, handle_error)
```

### Step 2: Register Error Handler

In `backend/app/__init__.py`:

```python
from .utils.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    # ... existing code ...
    
    # Register error handlers
    register_error_handlers(app)
    
    return app
```

### Step 3: Use in Routes

```python
from .utils.error_handler import APIError

@bp.route("/events", methods=["GET"])
def get_events():
    try:
        # ... your code ...
    except ValueError as e:
        raise APIError(str(e), status_code=400, error_code="INVALID_INPUT")
    except Exception as e:
        raise APIError("Failed to fetch events", status_code=500, error_code="SERVER_ERROR")
```

---

## 🧪 Fix #5: Basic Testing Setup (3 hours)

### Step 1: Install Testing Dependencies

```bash
cd backend
source venv/bin/activate
pip install pytest pytest-cov pytest-flask
```

### Step 2: Create Test Structure

Create `backend/tests/` directory:
```
backend/
  tests/
    __init__.py
    conftest.py
    test_auth.py
    test_events.py
```

### Step 3: Create Test Configuration

Create `backend/pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term
```

### Step 4: Create Test Fixtures

`backend/tests/conftest.py`:
```python
import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Create test user and get token
    response = client.post('/api/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    token = response.json['token']
    return {'Authorization': f'Bearer {token}'}
```

### Step 5: Write Sample Test

`backend/tests/test_auth.py`:
```python
import pytest
from app.models import User

def test_signup(client):
    response = client.post('/api/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    assert response.status_code == 200
    assert response.json['success'] == True
    assert 'token' in response.json

def test_login(client):
    # First signup
    client.post('/api/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    # Then login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    assert response.status_code == 200
    assert response.json['success'] == True
    assert 'token' in response.json
```

### Step 6: Run Tests

```bash
cd backend
pytest
```

---

## 📊 Progress Tracking

Use this checklist to track your progress:

### Critical Fixes
- [ ] Centralized API client created
- [ ] All hardcoded URLs replaced (46+ instances)
- [ ] JWT secret key validation added
- [ ] Input sanitization implemented
- [ ] Error handling improved

### High Priority
- [ ] Testing infrastructure set up
- [ ] Code duplication removed
- [ ] Environment configuration validated
- [ ] Database migrations set up

### Quick Wins Completed
- [ ] Error boundary added
- [ ] Database indexes added
- [ ] Basic logging configured

---

## 🎯 Next Steps After Quick Fixes

1. Review the full `PROJECT_IMPROVEMENT_PLAN.md`
2. Prioritize based on your needs
3. Set up CI/CD pipeline
4. Add comprehensive tests
5. Document everything

---

## 💡 Tips

- Fix one issue at a time
- Test after each fix
- Commit frequently with clear messages
- Ask for help if stuck
- Document your changes

Good luck! 🚀

