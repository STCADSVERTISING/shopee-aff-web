import time, hmac, hashlib, requests, csv, io
from typing import Dict, List, Any

class CommissionResolver:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        # Internal "manual" CSV store in memory
        self.manual: Dict[str, float] = {}

    def update_config(self, cfg: dict):
        self.cfg = cfg or {}

    # ---- Manual CSV ----
    def ingest_manual_csv(self, file_bytes: bytes) -> int:
        f = io.StringIO(file_bytes.decode("utf-8", errors="ignore"))
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            itemid = str(row.get("itemid") or "").strip()
            rate = row.get("commission_rate")
            if not itemid or rate is None:
                continue
            try:
                self.manual[itemid] = float(rate)
                count += 1
            except:
                continue
        return count

    # ---- Shopee Affiliate GraphQL ----
    def _affiliate_signature(self, app_id: str, secret: str, ts: int) -> str:
        msg = f"{app_id}{ts}"
        return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    def resolve_commissions(self, itemids: List[str]) -> Dict[str, float]:
        # 1) Manual has highest priority
        result: Dict[str, float] = {}
        for iid in itemids:
            if iid in self.manual:
                result[iid] = self.manual[iid]

        # 2) Shopee Affiliate GraphQL (if enabled)
        aff = (self.cfg or {}).get("affiliate") or {}
        if aff.get("enabled"):
            endpoint = aff.get("endpoint")
            app_id = aff.get("app_id")
            secret = aff.get("secret")
            if endpoint and app_id and secret:
                session = requests.Session()
                session.headers.update({"Content-Type": "application/json","Accept": "application/json"})
                ts = int(time.time())
                sig = self._affiliate_signature(app_id, secret, ts)
                chunks = [ [iid for iid in itemids if iid not in result][i:i+40] for i in range(0, len([iid for iid in itemids if iid not in result]), 40) ]
                for chunk in chunks:
                    if not chunk:
                        continue
                    payload = {
                        "query": """
                        query OfferList($itemIds: [String!]!) {
                          offerList(itemIds: $itemIds) {
                            itemId
                            commissionRate
                          }
                        }
                        """,
                        "variables": {"itemIds": chunk}
                    }
                    headers = {
                        "x-app-id": app_id,
                        "x-timestamp": str(ts),
                        "x-signature": sig
                    }
                    try:
                        r = session.post(endpoint, headers=headers, json=payload, timeout=25)
                        if r.status_code == 200:
                            j = r.json()
                            data = (j.get("data") or {}).get("offerList") or []
                            for row in data:
                                try:
                                    result[str(row["itemId"])] = float(row.get("commissionRate") or 0.0)
                                except:
                                    pass
                    except Exception as e:
                        # just skip on failure
                        pass
                    time.sleep(0.6)
        return result
