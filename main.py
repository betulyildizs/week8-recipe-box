"""Recipe Box — starter app for Week 8.

A tiny FastAPI service for recipes and tags, with a static frontend. Use it as the
playground for concurrent multi-agent work and a generator-critic loop.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
    # open http://localhost:8000/
Test:
    pytest
"""
import json
import math
import re
import sqlite3
from contextlib import asynccontextmanager, closing
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE = Path(__file__).parent
DB_PATH = BASE / "recipes.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS recipes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                ingredients TEXT NOT NULL,  -- JSON list of strings
                tags        TEXT NOT NULL   -- JSON list of strings
            )"""
        )
        conn.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Recipe Box", lifespan=lifespan)


class RecipeIn(BaseModel):
    title: str
    ingredients: list[str] = []
    tags: list[str] = []


def _row_to_recipe(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": json.loads(row["ingredients"]),
        "tags": json.loads(row["tags"]),
    }


def _scale_ingredient(ingredient: str, factor: float) -> str:
    match = re.match(r"^(\s*)(\d+(?:\.\d+)?)(?=\s|[A-Za-z]|$)", ingredient)
    if match is None:
        return ingredient

    quantity = Decimal(match.group(2)) * Decimal(str(factor))
    scaled_quantity = format(quantity, "f")
    if "." in scaled_quantity:
        scaled_quantity = scaled_quantity.rstrip("0").rstrip(".")
    return f"{match.group(1)}{scaled_quantity}{ingredient[match.end(2):]}"


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/recipes")
def create_recipe(recipe: RecipeIn):
    with closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO recipes (title, ingredients, tags) VALUES (?, ?, ?)",
            (recipe.title, json.dumps(recipe.ingredients), json.dumps(recipe.tags)),
        )
        conn.commit()
        rid = cur.lastrowid
    return {"id": rid, **recipe.model_dump()}


@app.get("/recipes")
def list_recipes(tag: str | None = None):
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM recipes ORDER BY id").fetchall()
    recipes = [_row_to_recipe(r) for r in rows]
    if tag is None:
        return recipes
    return [recipe for recipe in recipes if tag in recipe["tags"]]


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown recipe")
    return _row_to_recipe(row)


@app.get("/recipes/{recipe_id}/scaled")
def get_scaled_recipe(recipe_id: int, factor: float):
    if not math.isfinite(factor) or factor <= 0:
        raise HTTPException(status_code=422, detail="factor must be a finite positive number")

    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown recipe")

    recipe = _row_to_recipe(row)
    recipe["ingredients"] = [
        _scale_ingredient(ingredient, factor) for ingredient in recipe["ingredients"]
    ]
    return recipe


@app.get("/shopping-list")
def get_shopping_list(ids: str = ""):
    if not ids.strip():
        return []

    try:
        recipe_ids = [int(value.strip()) for value in ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid recipe IDs")
    if any(recipe_id <= 0 for recipe_id in recipe_ids):
        raise HTTPException(status_code=400, detail="invalid recipe IDs")

    unique_ids = list(dict.fromkeys(recipe_ids))
    placeholders = ",".join("?" for _ in unique_ids)
    with closing(get_db()) as conn:
        rows = conn.execute(
            f"SELECT id, ingredients FROM recipes WHERE id IN ({placeholders})",
            unique_ids,
        ).fetchall()
    recipes = {row["id"]: json.loads(row["ingredients"]) for row in rows}

    for recipe_id in recipe_ids:
        if recipe_id not in recipes:
            raise HTTPException(status_code=404, detail="unknown recipe")

    ingredients = []
    seen = set()
    for recipe_id in recipe_ids:
        for ingredient in recipes[recipe_id]:
            if ingredient not in seen:
                ingredients.append(ingredient)
                seen.add(ingredient)
    return ingredients
