import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "recipes.db")
    with TestClient(main.app) as test_client:
        yield test_client


def test_create_and_get_recipe(client):
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


def test_list_recipes(client):
    client.post("/recipes", json={"title": "Toast"})
    r = client.get("/recipes")
    assert r.status_code == 200
    assert any(rec["title"] == "Toast" for rec in r.json())


def test_list_recipes_filters_by_matching_tag(client):
    matching = client.post(
        "/recipes",
        json={"title": "Breakfast Oats", "ingredients": ["oats"], "tags": ["breakfast", "healthy"]},
    ).json()
    client.post(
        "/recipes",
        json={"title": "Dinner Pasta", "ingredients": ["pasta"], "tags": ["dinner"]},
    )

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    assert matching["id"] in [recipe["id"] for recipe in r.json()]
    assert all("breakfast" in recipe["tags"] for recipe in r.json())


def test_list_recipes_tag_with_no_matches(client):
    r = client.get("/recipes", params={"tag": "missing-tag"})

    assert r.status_code == 200
    assert r.json() == []


def test_list_recipes_omitted_tag_preserves_list_behavior(client):
    r = client.get("/recipes")

    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_recipes_excludes_recipes_without_tags(client):
    client.post("/recipes", json={"title": "Untagged Recipe"})

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    assert all("breakfast" in recipe["tags"] for recipe in r.json())
    assert all(recipe["title"] != "Untagged Recipe" for recipe in r.json())


def test_unknown_recipe_404(client):
    r = client.get("/recipes/99999")
    assert r.status_code == 404


def test_scaled_recipe_scales_quantities_and_preserves_recipe(client):
    original = client.post(
        "/recipes",
        json={
            "title": "Bread",
            "ingredients": [
                "200 g flour",
                "1.5 tsp yeast",
                "salt to taste",
                "200g flour",
                "2eggs",
                "Vitamin B12",
                "1/2 cup sugar",
            ],
            "tags": ["baking"],
        },
    ).json()

    response = client.get(f"/recipes/{original['id']}/scaled?factor=2")

    assert response.status_code == 200
    scaled = response.json()
    assert scaled == {
        **original,
        "ingredients": [
            "400 g flour",
            "3 tsp yeast",
            "salt to taste",
            "400g flour",
            "4eggs",
            "Vitamin B12",
            "1/2 cup sugar",
        ],
    }
    assert client.get(f"/recipes/{original['id']}").json() == original


def test_scaled_recipe_supports_decimal_factors(client):
    recipe_id = client.post(
        "/recipes",
        json={"title": "Oats", "ingredients": ["2 cups oats", "1.5g spice"]},
    ).json()["id"]

    response = client.get(f"/recipes/{recipe_id}/scaled?factor=0.25")

    assert response.status_code == 200
    assert response.json()["ingredients"] == ["0.5 cups oats", "0.375g spice"]


def test_scaled_recipe_preserves_precision_for_large_and_long_decimal_quantities(client):
    ingredients = [
        "1234567890123456789012345678901234567890 g flour",
        "0.123456789012345678901234567890123456789 kg sugar",
    ]
    recipe_id = client.post(
        "/recipes",
        json={"title": "Precise Recipe", "ingredients": ingredients},
    ).json()["id"]

    response = client.get(f"/recipes/{recipe_id}/scaled?factor=2")

    assert response.status_code == 200
    assert response.json()["ingredients"] == [
        "2469135780246913578024691357802469135780 g flour",
        "0.246913578024691357802469135780246913578 kg sugar",
    ]


def test_scaled_recipe_factor_one_preserves_exact_quantity_strings(client):
    ingredients = [
        "1234567890123456789012345678901234567890 g flour",
        "0.12345678901234567890123456789012345678900 kg sugar",
        "1.2300 tsp vanilla",
    ]
    recipe_id = client.post(
        "/recipes",
        json={"title": "Unchanged Recipe", "ingredients": ingredients},
    ).json()["id"]

    response = client.get(f"/recipes/{recipe_id}/scaled?factor=1")

    assert response.status_code == 200
    assert response.json()["ingredients"] == ingredients


def test_scaled_recipe_returns_404_for_unknown_recipe(client):
    response = client.get("/recipes/99999/scaled?factor=2")

    assert response.status_code == 404


def test_scaled_recipe_rejects_invalid_factors(client):
    recipe_id = client.post("/recipes", json={"title": "Soup"}).json()["id"]

    for factor in ("", "0", "-1", "inf", "Infinity", "1e309", "nan", "not-a-number"):
        response = client.get(f"/recipes/{recipe_id}/scaled?factor={factor}")
        assert response.status_code == 422


def test_scaled_recipe_requires_factor_parameter(client):
    recipe_id = client.post("/recipes", json={"title": "Soup"}).json()["id"]

    response = client.get(f"/recipes/{recipe_id}/scaled")

    assert response.status_code == 422


def test_shopping_list_merges_ingredients_in_first_seen_order(client):
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


def test_shopping_list_ignores_duplicate_recipe_ids(client):
    recipe_id = client.post(
        "/recipes",
        json={"title": "Repeated", "ingredients": ["butter", "sugar"]},
    ).json()["id"]

    response = client.get(f"/shopping-list?ids={recipe_id},{recipe_id}")

    assert response.status_code == 200
    assert response.json() == ["butter", "sugar"]


def test_shopping_list_empty_input_returns_empty_list(client):
    assert client.get("/shopping-list").json() == []
    assert client.get("/shopping-list?ids=").json() == []


def test_shopping_list_rejects_invalid_ids(client):
    for ids in ("abc", "1,,2", "0", "-1"):
        response = client.get(f"/shopping-list?ids={ids}")
        assert response.status_code == 400


def test_shopping_list_returns_404_for_unknown_recipe(client):
    response = client.get("/shopping-list?ids=2147483647")
    assert response.status_code == 404
