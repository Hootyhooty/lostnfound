CATALOG = {
    # product_code: { name, unit_price_usd_cents }
    "mug": {"name": "Lost&Found Mug", "price_cents": 1200},
    "shirt": {"name": "Lost&Found Shirt", "price_cents": 2000},
    "cap": {"name": "Lost&Found Cap", "price_cents": 1500},
}

def validate_and_price_items(client_items):
    """Validate incoming client items against the catalog and compute totals.

    Returns (validated_items, total_cents). Raises ValueError if an item is invalid.
    """
    validated = []
    total_cents = 0
    for raw in client_items or []:
        code = (raw.get("product_code") or raw.get("code") or raw.get("item") or "").strip()
        qty = int(raw.get("qty", 1))
        if qty < 1:
            raise ValueError("Invalid quantity")
        if code not in CATALOG:
            raise ValueError(f"Unknown product code: {code}")
        entry = CATALOG[code]
        line_cents = entry["price_cents"] * qty
        total_cents += line_cents
        validated.append({
            "product_code": code,
            "name": entry["name"],
            "unit_price_cents": entry["price_cents"],
            "qty": qty,
            "line_total_cents": line_cents,
        })
    return validated, total_cents


