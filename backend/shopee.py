import time, requests
from typing import List, Dict, Any

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://shopee.co.th/",
    "Connection": "keep-alive",
}

SEARCH_ENDPOINT = "https://shopee.co.th/api/v4/search/search_items"

def search_products(keyword: str, limit: int = 60, by: str = "sales", min_pause: float = 1.2) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    step = 60
    newest = 0
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    while len(results) < limit:
        params = {
            "by": by,               # relevancy | sales | price
            "keyword": keyword,
            "limit": min(step, limit - len(results)),
            "newest": newest,
            "order": "desc",
            "page_type": "search",
            "version": 2
        }
        r = session.get(SEARCH_ENDPOINT, params=params, timeout=25)
        if r.status_code != 200:
            break
        data = r.json()
        items = data.get("items") or []
        if not items:
            break
        for it in items:
            base = it.get("item_basic") or {}
            if not base:
                continue
            itemid = base.get("itemid")
            shopid = base.get("shopid")
            img = base.get("image")
            img_url = f"https://cf.shopee.co.th/file/{img}" if img else None
            detail_url = f"https://shopee.co.th/product/{shopid}/{itemid}" if itemid and shopid else None
            results.append({
                "itemid": itemid,
                "shopid": shopid,
                "name": base.get("name"),
                "price": (base.get("price", 0) or 0) / 100000,
                "historical_sold": base.get("historical_sold", 0),
                "rating_star": (base.get("item_rating") or {}).get("rating_star", 0),
                "liked_count": base.get("liked_count", 0),
                "shop_location": base.get("shop_location"),
                "currency": base.get("currency"),
                "image": img_url,
                "url": detail_url,
                "catid": base.get("catid"),
                "ctime": base.get("ctime")
            })
        newest += len(items)
        time.sleep(min_pause)
    return results[:limit]
