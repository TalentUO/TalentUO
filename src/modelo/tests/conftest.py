def pytest_configure(config):
    config.addinivalue_line("markers", "lento: ejecuta la cadena completa (varios minutos); se omite con -m 'not lento'")
