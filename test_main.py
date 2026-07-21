"""
Zabacode Comprehensive Unit Tests

Run: pytest test_main.py -v
"""

import json
import pytest
from main import app, execute_code_isolated, _is_package_installed, _normalize_code, KNOWN_LIBRARIES, AUTH_TOKEN


@pytest.fixture
def client():
    """Create test client with X-Zabacode-Token header."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        client.environ_base['HTTP_X_ZABACODE_TOKEN'] = AUTH_TOKEN
        yield client


class TestCodeExecution:
    """Test code execution & isolation."""
    
    def test_simple_print(self):
        """Test simple print statement."""
        result = execute_code_isolated('print("hello")')
        assert result["ok"] is True
        assert "hello" in result["stdout"]
    
    def test_syntax_error(self):
        """Test syntax error handling."""
        result = execute_code_isolated('print("missing quote')
        assert result["ok"] is False
        assert "SyntaxError" in result["stderr"] or "syntax" in result["stderr"].lower()
    
    def test_timeout(self):
        """Test timeout handling."""
        result = execute_code_isolated('while True: pass', timeout=2)
        assert result["timeout"] is True
        assert result["ok"] is False

    def test_import_standard_lib(self):
        """Test standard library import and __file__ definition."""
        result = execute_code_isolated('import sys, os\nprint("file:", os.path.exists("_active_run.py"))')
        assert result["ok"] is True
        assert "True" in result["stdout"]
    
    def test_windows_line_endings_normalized(self):
        """Test that Windows line endings are handled correctly."""
        code_windows = 'print("test 1")\r\nprint("test 2")\r\n'
        normalized = _normalize_code(code_windows)
        assert '\r\n' not in normalized
        assert '\r' not in normalized
        result = execute_code_isolated(code_windows)
        assert result["ok"] is True
    
    def test_trailing_whitespace_normalized(self):
        """Test that trailing whitespace is cleaned."""
        code = 'print("test")   \nprint("next")   \n'
        normalized = _normalize_code(code)
        lines = normalized.split('\n')
        assert lines[0] == 'print("test")'
        assert lines[1] == 'print("next")'
    
    def test_bom_removed(self):
        """Test that BOM is removed from code."""
        code_with_bom = '\ufeffprint("hello")'
        normalized = _normalize_code(code_with_bom)
        assert not normalized.startswith('\ufeff')
        assert normalized.startswith('print')


class TestHTTPRoutes:
    """Test Flask HTTP routes."""
    
    def test_index(self, client):
        """Test root route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'zabacode' in response.data.lower()
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert data["version"] == "0.3.5"
        assert "providers" in data
    
    def test_run_code_api(self, client):
        """Test /api/run endpoint with auth token."""
        response = client.post('/api/run',
            data=json.dumps({"code": "print('test')"}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert "test" in data["stdout"]

    def test_unauthorized_access(self):
        """Test blocking unauthorized requests without token."""
        with app.test_client() as unauth_client:
            response = unauth_client.post('/api/run',
                data=json.dumps({"code": "print('fail')"}),
                content_type='application/json')
            assert response.status_code == 401
    
    def test_list_libraries(self, client):
        """Test /api/libraries endpoint."""
        response = client.get('/api/libraries')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "requests" in data
        assert "fastapi" in data
        assert "tinydb" in data
        assert data["requests"]["tier"] in ["runtime", "buildtime"]
    
    def test_keys_status(self, client):
        """Test /api/keys/status endpoint."""
        response = client.get('/api/keys/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        providers = ["openrouter", "gemini", "groq", "mistral"]
        for provider in providers:
            assert provider in data
            assert isinstance(data[provider], bool)
    
    def test_list_themes(self, client):
        """Test /api/themes endpoint."""
        response = client.get('/api/themes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "themes" in data
        assert "retro" in data["themes"]
        assert "cyberpunk" in data["themes"]
    
    def test_code_check_valid(self, client):
        """Test /api/check endpoint with valid code."""
        response = client.post('/api/check',
            data=json.dumps({"code": "print('hello')\nprint('world')"}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert data["valid"] is True
        assert len(data["issues"]) == 0
    
    def test_code_check_unbalanced_parens(self, client):
        """Test /api/check detects unbalanced parentheses."""
        response = client.post('/api/check',
            data=json.dumps({"code": "print('hello'"}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert data["valid"] is False
        assert any("()" in issue for issue in data["issues"])
    
    def test_code_check_unbalanced_brackets(self, client):
        """Test /api/check detects unbalanced brackets."""
        response = client.post('/api/check',
            data=json.dumps({"code": "x = [1, 2, 3"}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert data["valid"] is False
        assert any("[]" in issue for issue in data["issues"])


class TestFileManager:
    """Test file manager functionality."""
    
    def test_save_file(self, client):
        """Test saving a file."""
        response = client.post('/api/files/test_save',
            data=json.dumps({"content": "print('test')"}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert "test_save" in data["filename"]
    
    def test_read_file(self, client):
        """Test reading a file."""
        client.post('/api/files/test_read',
            data=json.dumps({"content": "print('hello')"}),
            content_type='application/json')
        
        response = client.get('/api/files/test_read.py')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert "hello" in data["content"]
    
    def test_invalid_filename(self, client):
        """Test invalid filename & dotfile security handling."""
        response = client.get('/api/files/../etc/passwd')
        assert response.status_code == 400
        
        response_dot = client.get('/api/files/.zabacode_keys.json')
        assert response_dot.status_code == 400


class TestLibraryManager:
    """Test library management."""
    
    def test_known_libraries_complete(self):
        """Test that KNOWN_LIBRARIES has extensive packages across categories."""
        required = ["requests", "beautifulsoup4", "numpy", "tinydb", "fastapi", "rich"]
        for lib in required:
            assert lib in KNOWN_LIBRARIES
    
    def test_library_tier_validation(self):
        """Test library tier is valid."""
        for name, info in KNOWN_LIBRARIES.items():
            assert info["tier"] in ["runtime", "buildtime"]
            assert "category" in info
            assert "reason" in info


class TestSecurityBoundaries:
    """Test security & isolation."""
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal attack prevention."""
        response = client.get('/api/files/../../secret')
        assert response.status_code == 400
    
    def test_no_file_extension_bypass(self, client):
        """Test that non-.py files are auto-appended with .py safely."""
        response = client.post('/api/files/script_file',
            data=json.dumps({"content": "print(1)"}),
            content_type='application/json')
        assert response.status_code == 200
        assert response.get_json()["filename"] == "script_file.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
