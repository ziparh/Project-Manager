# Import all fixtures from submodules to make them available globally
pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.auth",
    "tests.fixtures.client",
]


def pytest_configure(config):
    """
    Configure pytest markers.
    Allows using custom markers like @pytest.mark.unit
    """
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, no database or external dependencies)",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (use database, may be slower)",
    )
