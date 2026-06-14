import os
import tempfile
import pytest
from controllers import create_app
import init_db

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.secret_key = 'test-secret-key'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def db(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix='_test.db')
    monkeypatch.setattr('init_db.DB_NAME', db_path)
    init_db.init_db()
    yield
    try:
        os.close(db_fd)
    except OSError:
        pass
    try:
        os.unlink(db_path)
    except (PermissionError, OSError):
        pass

@pytest.fixture
def auth_admin(client):
    with client.session_transaction() as sess:
        sess['user'] = {"id": 1, "username": "admin", "role": "Administrator"}
    return client

@pytest.fixture
def auth_supervisor(client):
    with client.session_transaction() as sess:
        sess['user'] = {"id": 2, "username": "super", "role": "Supervisor"}
    return client

@pytest.fixture
def auth_staff(client):
    with client.session_transaction() as sess:
        sess['user'] = {"id": 3, "username": "staff", "role": "Operational Staff"}
    return client
