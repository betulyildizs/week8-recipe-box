from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_get_recipe():
    r = client.post(
        "/recipes",
        json={"title": "Pancakes", "ingredients": ["flour", "milk"], "tags": ["breakfast"]},
    )
    assert r.status_code == 200
    rid = r.json()["id"]
    r2 = client.get(f"/recipes/{rid}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Pancakes"
    assert r2.json()["tags"] == ["breakfast"]


def test_list_recipes():
    client.post("/recipes", json={"title": "Toast"})
    r = client.get("/recipes")
    assert r.status_code == 200
    assert any(rec["title"] == "Toast" for rec in r.json())


def test_unknown_recipe_404():
    r = client.get("/recipes/99999")
    assert r.status_code == 404


def test_shopping_list_merges_ingredients_in_first_seen_order():
    first = client.post(
        "/recipes",
        json={"title": "First", "ingredients": ["flour", "milk", "flour"]},
    ).json()["id"]
    second = client.post(
        "/recipes",
        json={"title": "Second", "ingredients": ["milk", "eggs"]},
    ).json()["id"]

    response = client.get(f"/shopping-list?ids={first},{second}")

    assert response.status_code == 200
    assert response.json() == ["flour", "milk", "eggs"]


def test_shopping_list_ignores_duplicate_recipe_ids():
    recipe_id = client.post(
        "/recipes",
        json={"title": "Repeated", "ingredients": ["butter", "sugar"]},
    ).json()["id"]

    response = client.get(f"/shopping-list?ids={recipe_id},{recipe_id}")

    assert response.status_code == 200
    assert response.json() == ["butter", "sugar"]


def test_shopping_list_empty_input_returns_empty_list():
    assert client.get("/shopping-list").json() == []
    assert client.get("/shopping-list?ids=").json() == []


def test_shopping_list_rejects_invalid_ids():
    for ids in ("abc", "1,,2", "0", "-1"):
        response = client.get(f"/shopping-list?ids={ids}")
        assert response.status_code == 400


def test_shopping_list_returns_404_for_unknown_recipe():
    response = client.get("/shopping-list?ids=2147483647")
    assert response.status_code == 404
