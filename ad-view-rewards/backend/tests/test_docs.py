from pathlib import Path


def test_docs_page_accessible(client) -> None:
    response = client.get('/docs')
    assert response.status_code == 200
    assert 'Swagger UI' in response.text


def test_openapi_file_exists() -> None:
    openapi_path = Path(__file__).resolve().parents[3] / 'openapi.json'
    assert openapi_path.exists()
