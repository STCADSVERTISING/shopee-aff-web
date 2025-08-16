import os, json
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from shopee import search_products
from commission_providers import CommissionResolver

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app = FastAPI(title="Shopee Aff Web")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config_from_file() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"affiliate": {"enabled": False}}

def load_env_overrides(cfg: dict) -> dict:
    # Environment overrides
    enabled = os.getenv("AFF_ENABLED")
    endpoint = os.getenv("AFF_ENDPOINT")
    app_id = os.getenv("AFF_APP_ID")
    secret = os.getenv("AFF_SECRET")
    aff = cfg.get("affiliate", {}) if cfg else {}
    if enabled is not None:
        # Treat "1", "true", "True" as True
        aff["enabled"] = enabled.lower() in ("1","true","yes","on")
    if endpoint: aff["endpoint"] = endpoint
    if app_id: aff["app_id"] = app_id
    if secret: aff["secret"] = secret
    cfg["affiliate"] = aff
    return cfg

def load_config() -> dict:
    cfg = load_config_from_file()
    cfg = load_env_overrides(cfg)
    return cfg

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

cfg = load_config()
resolver = CommissionResolver(cfg)

# Models
class SearchQuery(BaseModel):
    keyword: str
    limit: int = 120
    min_rating: float = 4.5
    min_sold: int = 100
    sort: str = "sold"  # sold | score

class ConfigModel(BaseModel):
    affiliate: Dict[str, Any]

@app.get("/api/config")
def get_config():
    return load_config()

@app.post("/api/config")
def set_config(model: ConfigModel):
    save_config(model.dict())
    resolver.update_config(model.dict())
    return {"ok": True}

@app.get("/api/categories")
def get_categories():
    cats_path = os.path.join(BASE_DIR, "categories.json")
    with open(cats_path, "r", encoding="utf-8") as f:
        cats = json.load(f)
    return {"categories": cats}

@app.post("/api/search")
def api_search(q: SearchQuery):
    items = search_products(q.keyword, limit=q.limit, by="sales")
    # filter
    filtered = []
    for it in items:
        if (it.get("rating_star") or 0) < q.min_rating:
            continue
        if (it.get("historical_sold") or 0) < q.min_sold:
            continue
        filtered.append(it)

    # commission enrich
    commissions = resolver.resolve_commissions([str(x["itemid"]) for x in filtered if x.get("itemid")])
    for it in filtered:
        iid = str(it.get("itemid"))
        it["commission_rate"] = commissions.get(iid)
        it["score"] = (it.get("commission_rate") or 0.0) * float(it.get("historical_sold") or 0)

    # sort
    if q.sort == "score":
        filtered.sort(key=lambda x: (x["score"] is not None, x["score"]), reverse=True)
    else:
        filtered.sort(key=lambda x: x.get("historical_sold", 0), reverse=True)

    return {"items": filtered, "count": len(filtered)}

@app.post("/api/top-by-category")
def top_by_category(limit_per_cat: int = 20, min_rating: float = 4.5, min_sold: int = 100, use_score: bool = True):
    # Iterate categories and use first matched keyword to search
    cats_path = os.path.join(BASE_DIR, "categories.json")
    with open(cats_path, "r", encoding="utf-8") as f:
        cats = json.load(f)

    results = []
    for cat in cats:
        keyword = (cat.get("keywords") or [""])[0]
        items = search_products(keyword, limit=limit_per_cat, by="sales")

        # Filter
        filtered = []
        for it in items:
            if (it.get("rating_star") or 0) < min_rating: continue
            if (it.get("historical_sold") or 0) < min_sold: continue
            filtered.append(it)

        # Commission enrich
        commissions = resolver.resolve_commissions([str(x["itemid"]) for x in filtered if x.get("itemid")])
        for it in filtered:
            iid = str(it.get("itemid"))
            it["commission_rate"] = commissions.get(iid)
            it["score"] = (it.get("commission_rate") or 0.0) * float(it.get("historical_sold") or 0)

        # Sort per category
        if use_score:
            filtered.sort(key=lambda x: (x["score"] is not None, x["score"]), reverse=True)
        else:
            filtered.sort(key=lambda x: x.get("historical_sold", 0), reverse=True)

        top1 = filtered[0] if filtered else None
        results.append({"category": cat, "top": top1, "items": filtered})

    return {"categories": results}

@app.post("/api/commission/upload")
async def upload_commission(file: UploadFile = File(...)):
    data = await file.read()
    count = resolver.ingest_manual_csv(data)
    return {"ok": True, "ingested": count}

# Serve static frontend
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
