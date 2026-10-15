def pytest_configure(config):
    config.addinivalue_line("markers", "lento: ejecuta la cadena completa (1-2 min); se omite con -m 'not lento'")
