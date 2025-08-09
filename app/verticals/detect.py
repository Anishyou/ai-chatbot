def detect_vertical(html: str) -> str:
    """
    Very basic heuristic for business vertical.
    """
    text = html.lower()
    if "menu" in text and ("restaurant" in text or "cafe" in text or "bar" in text):
        return "restaurant"
    if "products" in text or "shop" in text:
        return "ecommerce"
    return "generic"
