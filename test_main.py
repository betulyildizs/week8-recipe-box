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


def test_list_recipes_filters_by_matching_tag():
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


def test_list_recipes_tag_with_no_matches():
    r = client.get("/recipes", params={"tag": "missing-tag"})

    assert r.status_code == 200
    assert r.json() == []


def test_list_recipes_omitted_tag_preserves_list_behavior():
    r = client.get("/recipes")

    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_recipes_excludes_recipes_without_tags():
    client.post("/recipes", json={"title": "Untagged Recipe"})

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    assert all("breakfast" in recipe["tags"] for recipe in r.json())
    assert all(recipe["title"] != "Untagged Recipe" for recipe in r.json())


def test_unknown_recipe_404():
    r = client.get("/recipes/99999")
    assert r.status_code == 404
