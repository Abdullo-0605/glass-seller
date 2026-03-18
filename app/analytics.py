"""Analytics engine — gathers sales data and answers business questions.

Works in two modes:
1. Built-in: pattern-matches the question and returns data-driven answers.
2. LLM-powered: if OPENAI_API_KEY is set, sends the data context + question
   to an OpenAI-compatible API for a natural-language response.
"""
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

from .models import db, Product, Order, OrderItem, WholesaleShipment, ShipmentItem, Invoice


# ---------------------------------------------------------------------------
# Data gathering — builds a snapshot of the business for the LLM / engine
# ---------------------------------------------------------------------------

def _gather_data():
    """Pull all relevant analytics data from the database."""
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    order_items = db.session.query(
        OrderItem.product_id,
        db.func.sum(OrderItem.quantity).label("total_qty"),
        db.func.sum(OrderItem.quantity * OrderItem.price).label("total_rev"),
    ).group_by(OrderItem.product_id).all()

    product_map = {p.id: p for p in products}

    # Top sellers by quantity
    top_by_qty = sorted(order_items, key=lambda r: r.total_qty, reverse=True)
    # Top sellers by revenue
    top_by_rev = sorted(order_items, key=lambda r: r.total_rev, reverse=True)

    # Category breakdown
    cat_sales = defaultdict(lambda: {"qty": 0, "revenue": 0.0})
    for row in order_items:
        p = product_map.get(row.product_id)
        if p:
            cat_sales[p.category]["qty"] += row.total_qty
            cat_sales[p.category]["revenue"] += float(row.total_rev)

    # Car make breakdown
    make_sales = defaultdict(lambda: {"qty": 0, "revenue": 0.0})
    for row in order_items:
        p = product_map.get(row.product_id)
        if p and p.car_make:
            make_sales[p.car_make]["qty"] += row.total_qty
            make_sales[p.car_make]["revenue"] += float(row.total_rev)

    # Stock info
    low_stock = [p for p in products if p.stock_quantity <= 5]
    out_of_stock = [p for p in products if p.stock_quantity <= 0]
    total_inventory_value = sum(p.cost * p.stock_quantity for p in products if p.cost)

    # Order stats
    total_orders = len(orders)
    pending = sum(1 for o in orders if o.status == "PENDING")
    approved = sum(1 for o in orders if o.status == "APPROVED")
    completed = sum(1 for o in orders if o.status == "COMPLETED")
    cancelled = sum(1 for o in orders if o.status == "CANCELLED")
    total_revenue = sum(o.total_amount for o in orders)
    avg_order = total_revenue / total_orders if total_orders else 0

    # Profit margins
    best_margin = []
    for p in products:
        if p.cost and p.cost > 0:
            margin = ((p.price - p.cost) / p.cost) * 100
            best_margin.append((p, margin))
    best_margin.sort(key=lambda x: x[1], reverse=True)

    # Never-sold products
    sold_ids = {row.product_id for row in order_items}
    never_sold = [p for p in products if p.id not in sold_ids]

    return {
        "products": products,
        "product_map": product_map,
        "orders": orders,
        "order_items": order_items,
        "top_by_qty": top_by_qty,
        "top_by_rev": top_by_rev,
        "cat_sales": dict(cat_sales),
        "make_sales": dict(make_sales),
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_inventory_value": total_inventory_value,
        "total_orders": total_orders,
        "pending": pending,
        "approved": approved,
        "completed": completed,
        "cancelled": cancelled,
        "total_revenue": total_revenue,
        "avg_order": avg_order,
        "best_margin": best_margin,
        "never_sold": never_sold,
    }


def _build_context_text(data):
    """Build a concise text summary for LLM context."""
    pm = data["product_map"]
    lines = [
        "=== Winaris Glass LLC — Business Analytics Snapshot ===",
        f"Total products: {len(data['products'])}",
        f"Total orders: {data['total_orders']}  (Pending: {data['pending']}, "
        f"Approved: {data['approved']}, Completed: {data['completed']}, "
        f"Cancelled: {data['cancelled']})",
        f"Total revenue: ${data['total_revenue']:.2f}",
        f"Average order value: ${data['avg_order']:.2f}",
        f"Inventory value (at cost): ${data['total_inventory_value']:.2f}",
        f"Low stock items (<=5): {len(data['low_stock'])}",
        f"Out of stock: {len(data['out_of_stock'])}",
        "",
        "--- Top Sellers by Quantity ---",
    ]
    for row in data["top_by_qty"][:10]:
        p = pm.get(row.product_id)
        if p:
            lines.append(f"  {p.name} [{p.category}] — {row.total_qty} units, ${float(row.total_rev):.2f} revenue")

    lines.append("")
    lines.append("--- Top Sellers by Revenue ---")
    for row in data["top_by_rev"][:10]:
        p = pm.get(row.product_id)
        if p:
            lines.append(f"  {p.name} — ${float(row.total_rev):.2f}")

    lines.append("")
    lines.append("--- Sales by Category ---")
    for cat, info in sorted(data["cat_sales"].items(), key=lambda x: x[1]["revenue"], reverse=True):
        lines.append(f"  {cat}: {info['qty']} units, ${info['revenue']:.2f}")

    lines.append("")
    lines.append("--- Sales by Car Make ---")
    for make, info in sorted(data["make_sales"].items(), key=lambda x: x[1]["revenue"], reverse=True):
        lines.append(f"  {make}: {info['qty']} units, ${info['revenue']:.2f}")

    lines.append("")
    lines.append("--- Best Profit Margins ---")
    for p, margin in data["best_margin"][:8]:
        lines.append(f"  {p.name}: {margin:.1f}% margin (cost ${p.cost:.2f}, sell ${p.price:.2f})")

    if data["low_stock"]:
        lines.append("")
        lines.append("--- Low Stock Alert ---")
        for p in data["low_stock"][:10]:
            lines.append(f"  {p.name}: {p.stock_quantity} left")

    if data["never_sold"]:
        lines.append("")
        lines.append("--- Products Never Sold ---")
        for p in data["never_sold"][:10]:
            lines.append(f"  {p.name} (stock: {p.stock_quantity})")

    lines.append("")
    lines.append("--- All Products ---")
    for p in data["products"]:
        lines.append(
            f"  [{p.id}] {p.name} | {p.category} | "
            f"{p.car_make} {p.car_model} {p.year_range} | "
            f"Part#: {p.part_number} | "
            f"Price: ${p.price:.2f} | Cost: ${p.cost:.2f} | Stock: {p.stock_quantity}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in pattern-matching engine (no LLM needed)
# ---------------------------------------------------------------------------

_PATTERNS = [
    (r"(?:top|best)\s*sell", "top_sellers"),
    (r"what.*sell.*(?:best|most|top)", "top_sellers"),
    (r"most\s*(?:sold|popular|ordered)", "top_sellers"),
    (r"highest\s*revenue", "top_revenue"),
    (r"most\s*revenue", "top_revenue"),
    (r"revenue\s*(?:by|per)\s*(?:product|item)", "top_revenue"),
    (r"categor", "category_breakdown"),
    (r"(?:by|per)\s*category", "category_breakdown"),
    (r"(?:car|vehicle)\s*make", "make_breakdown"),
    (r"(?:by|per)\s*make", "make_breakdown"),
    (r"(?:which|what)\s*make", "make_breakdown"),
    (r"low\s*stock", "low_stock"),
    (r"out\s*of\s*stock", "out_of_stock"),
    (r"restock|reorder|need.*order", "low_stock"),
    (r"inventory\s*(?:value|worth)", "inventory_value"),
    (r"(?:total|overall)\s*(?:revenue|sales|income)", "total_revenue"),
    (r"(?:average|avg)\s*order", "avg_order"),
    (r"order\s*(?:status|summary|stats|breakdown)", "order_status"),
    (r"pending\s*order", "order_status"),
    (r"profit\s*margin", "margins"),
    (r"(?:best|highest)\s*margin", "margins"),
    (r"never\s*sold", "never_sold"),
    (r"not\s*sell", "never_sold"),
    (r"slow\s*mov", "never_sold"),
    (r"(?:summary|overview|report|snapshot|everything|all\s*data)", "summary"),
    (r"(?:help|what\s*can|how\s*do|commands)", "help"),
    (r"(?:trend|forecast|predict)", "trends"),
    (r"(?:honda|toyota|ford|chevrolet|chevy|tesla|bmw|jeep)", "specific_make"),
    (r"windshield|window|quarter|sunroof|accessor", "specific_category"),
]


def _match_intent(question):
    q = question.lower().strip()
    for pattern, intent in _PATTERNS:
        if re.search(pattern, q):
            return intent, q
    return "unknown", q


def _builtin_answer(question, data):
    """Answer using pattern matching + real DB data."""
    intent, q = _match_intent(question)
    pm = data["product_map"]

    if intent == "top_sellers":
        if not data["top_by_qty"]:
            return "No sales data yet. Once orders come in, I'll be able to tell you what's selling best."
        lines = ["**Top Selling Products (by units sold):**\n"]
        for i, row in enumerate(data["top_by_qty"][:7], 1):
            p = pm.get(row.product_id)
            if p:
                lines.append(f"{i}. **{p.name}** — {row.total_qty} units sold (${float(row.total_rev):.2f} revenue)")
        return "\n".join(lines)

    elif intent == "top_revenue":
        if not data["top_by_rev"]:
            return "No revenue data yet."
        lines = ["**Top Products by Revenue:**\n"]
        for i, row in enumerate(data["top_by_rev"][:7], 1):
            p = pm.get(row.product_id)
            if p:
                lines.append(f"{i}. **{p.name}** — ${float(row.total_rev):.2f} ({row.total_qty} units)")
        return "\n".join(lines)

    elif intent == "category_breakdown":
        if not data["cat_sales"]:
            return "No category sales data yet."
        lines = ["**Sales by Category:**\n"]
        for cat, info in sorted(data["cat_sales"].items(), key=lambda x: x[1]["revenue"], reverse=True):
            lines.append(f"- **{cat}**: {info['qty']} units, ${info['revenue']:.2f} revenue")
        best_cat = max(data["cat_sales"].items(), key=lambda x: x[1]["revenue"])
        lines.append(f"\n*Best performing category: **{best_cat[0]}** with ${best_cat[1]['revenue']:.2f} in sales.*")
        return "\n".join(lines)

    elif intent == "make_breakdown":
        if not data["make_sales"]:
            return "No vehicle make sales data yet."
        lines = ["**Sales by Car Make:**\n"]
        for make, info in sorted(data["make_sales"].items(), key=lambda x: x[1]["revenue"], reverse=True):
            lines.append(f"- **{make}**: {info['qty']} units, ${info['revenue']:.2f} revenue")
        best = max(data["make_sales"].items(), key=lambda x: x[1]["revenue"])
        lines.append(f"\n*Most popular make: **{best[0]}** with ${best[1]['revenue']:.2f} in sales.*")
        return "\n".join(lines)

    elif intent == "low_stock":
        if not data["low_stock"]:
            return "All products are well-stocked (above 5 units). No restocking needed right now."
        lines = ["**Low Stock Alert** (5 or fewer units):\n"]
        for p in sorted(data["low_stock"], key=lambda x: x.stock_quantity):
            status = "OUT OF STOCK" if p.stock_quantity <= 0 else f"{p.stock_quantity} left"
            lines.append(f"- **{p.name}** — {status} (Part#: {p.part_number})")
        lines.append(f"\n*{len(data['low_stock'])} products need restocking.*")
        return "\n".join(lines)

    elif intent == "out_of_stock":
        if not data["out_of_stock"]:
            return "No products are currently out of stock."
        lines = ["**Out of Stock Products:**\n"]
        for p in data["out_of_stock"]:
            lines.append(f"- **{p.name}** (Part#: {p.part_number})")
        return "\n".join(lines)

    elif intent == "inventory_value":
        return (
            f"**Current Inventory Value:** ${data['total_inventory_value']:.2f} (at cost)\n\n"
            f"Total products: {len(data['products'])}\n"
            f"Total units in stock: {sum(p.stock_quantity for p in data['products'])}"
        )

    elif intent == "total_revenue":
        return (
            f"**Total Revenue:** ${data['total_revenue']:.2f}\n"
            f"**Total Orders:** {data['total_orders']}\n"
            f"**Average Order Value:** ${data['avg_order']:.2f}"
        )

    elif intent == "avg_order":
        return f"**Average Order Value:** ${data['avg_order']:.2f} across {data['total_orders']} orders."

    elif intent == "order_status":
        return (
            f"**Order Status Breakdown:**\n\n"
            f"- **Pending:** {data['pending']}\n"
            f"- **Approved:** {data['approved']}\n"
            f"- **Completed:** {data['completed']}\n"
            f"- **Cancelled:** {data['cancelled']}\n"
            f"- **Total:** {data['total_orders']}\n\n"
            f"Total revenue: ${data['total_revenue']:.2f}"
        )

    elif intent == "margins":
        if not data["best_margin"]:
            return "No margin data available (product costs may not be set)."
        lines = ["**Best Profit Margins:**\n"]
        for p, margin in data["best_margin"][:7]:
            lines.append(f"- **{p.name}** — {margin:.1f}% margin (cost ${p.cost:.2f} → sell ${p.price:.2f})")
        return "\n".join(lines)

    elif intent == "never_sold":
        if not data["never_sold"]:
            return "Every product has been sold at least once!"
        lines = ["**Products That Have Never Been Sold:**\n"]
        for p in data["never_sold"]:
            lines.append(f"- **{p.name}** — {p.stock_quantity} in stock, priced at ${p.price:.2f}")
        lines.append(f"\n*Consider promoting or discounting these {len(data['never_sold'])} products.*")
        return "\n".join(lines)

    elif intent == "trends":
        lines = ["**Sales Trends & Insights:**\n"]
        if data["top_by_qty"]:
            top = pm.get(data["top_by_qty"][0].product_id)
            if top:
                lines.append(f"- Your **#1 best seller** is **{top.name}** with {data['top_by_qty'][0].total_qty} units sold.")
        if data["cat_sales"]:
            best_cat = max(data["cat_sales"].items(), key=lambda x: x[1]["revenue"])
            lines.append(f"- **{best_cat[0]}** is your highest-revenue category at ${best_cat[1]['revenue']:.2f}.")
        if data["make_sales"]:
            best_make = max(data["make_sales"].items(), key=lambda x: x[1]["qty"])
            lines.append(f"- **{best_make[0]}** vehicles generate the most demand ({best_make[1]['qty']} units).")
        if data["never_sold"]:
            lines.append(f"- {len(data['never_sold'])} products have never sold — consider price adjustments.")
        if data["low_stock"]:
            lines.append(f"- {len(data['low_stock'])} products are low on stock — order soon to avoid stockouts.")
        lines.append(f"- Average order value is **${data['avg_order']:.2f}**.")
        return "\n".join(lines)

    elif intent == "specific_make":
        make_match = None
        for make in data["make_sales"]:
            if make.lower() in q:
                make_match = make
                break
        if not make_match:
            search = q
            for make in ["honda", "toyota", "ford", "chevrolet", "tesla", "bmw", "jeep"]:
                if make in q:
                    make_match = make.capitalize()
                    if make == "chevrolet" or "chevy" in q:
                        make_match = "Chevrolet"
                    break
        if make_match and make_match in data["make_sales"]:
            info = data["make_sales"][make_match]
            lines = [f"**{make_match} Sales Data:**\n"]
            lines.append(f"- Units sold: {info['qty']}")
            lines.append(f"- Revenue: ${info['revenue']:.2f}")
            related = [p for p in data["products"] if p.car_make == make_match]
            lines.append(f"- Products in catalog: {len(related)}")
            for p in related:
                lines.append(f"  - {p.name} (stock: {p.stock_quantity}, price: ${p.price:.2f})")
            return "\n".join(lines)
        return f"I don't have specific sales data for that make yet. Try asking about top sellers or sales by make."

    elif intent == "specific_category":
        cat_match = None
        for cat in data["cat_sales"]:
            if cat.lower() in q:
                cat_match = cat
                break
        if not cat_match:
            for kw, cat_name in [("windshield", "Windshield"), ("window", "Side Window"),
                                  ("quarter", "Quarter Glass"), ("sunroof", "Sunroof"),
                                  ("accessor", "Accessories")]:
                if kw in q:
                    for cat in data["cat_sales"]:
                        if cat_name.lower() in cat.lower():
                            cat_match = cat
                            break
                    break
        if cat_match and cat_match in data["cat_sales"]:
            info = data["cat_sales"][cat_match]
            lines = [f"**{cat_match} Sales Data:**\n"]
            lines.append(f"- Units sold: {info['qty']}")
            lines.append(f"- Revenue: ${info['revenue']:.2f}")
            related = [p for p in data["products"] if p.category == cat_match]
            lines.append(f"- Products in catalog: {len(related)}")
            return "\n".join(lines)
        return "I don't have specific data for that category yet."

    elif intent == "summary":
        return _full_summary(data)

    elif intent == "help":
        return (
            "**I can answer questions like:**\n\n"
            "- What's selling best?\n"
            "- Show me top sellers by revenue\n"
            "- Sales breakdown by category\n"
            "- Which car make sells the most?\n"
            "- What products are low stock?\n"
            "- Total revenue and order stats\n"
            "- Best profit margins\n"
            "- Products that never sold\n"
            "- Sales trends and insights\n"
            "- How are Honda / Toyota / Ford doing?\n"
            "- Give me a full summary\n"
            "- Inventory value\n\n"
            "*Just ask naturally — I'll pull the data from your database!*"
        )

    else:
        return _full_summary(data) + (
            "\n\n---\n*I wasn't sure exactly what you meant. "
            "Above is a full summary. Try asking things like "
            "\"what's selling best?\" or \"show me sales by category\" or type **help**.*"
        )


def _full_summary(data):
    pm = data["product_map"]
    lines = [
        "**Winaris Glass LLC — Business Summary**\n",
        f"**Revenue:** ${data['total_revenue']:.2f} across {data['total_orders']} orders "
        f"(avg ${data['avg_order']:.2f}/order)",
        f"**Inventory:** {len(data['products'])} products, "
        f"${data['total_inventory_value']:.2f} value at cost",
        f"**Orders:** {data['pending']} pending, {data['approved']} approved, "
        f"{data['completed']} completed, {data['cancelled']} cancelled",
    ]
    if data["top_by_qty"]:
        top = pm.get(data["top_by_qty"][0].product_id)
        if top:
            lines.append(f"\n**#1 Best Seller:** {top.name} ({data['top_by_qty'][0].total_qty} units)")
    if data["cat_sales"]:
        best_cat = max(data["cat_sales"].items(), key=lambda x: x[1]["revenue"])
        lines.append(f"**Top Category:** {best_cat[0]} (${best_cat[1]['revenue']:.2f})")
    if data["make_sales"]:
        best_make = max(data["make_sales"].items(), key=lambda x: x[1]["revenue"])
        lines.append(f"**Top Car Make:** {best_make[0]} (${best_make[1]['revenue']:.2f})")
    if data["low_stock"]:
        lines.append(f"\n**{len(data['low_stock'])} products low on stock.**")
    if data["never_sold"]:
        lines.append(f"**{len(data['never_sold'])} products have never been sold.**")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM integration (optional — uses OpenAI-compatible API)
# ---------------------------------------------------------------------------

def _try_llm(question, context_text):
    """Try to answer via LLM. Returns None if no API key is configured."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI

        base_url = os.environ.get("OPENAI_BASE_URL", None)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        client = OpenAI(api_key=api_key, base_url=base_url)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the business analytics assistant for Winaris Glass LLC, "
                    "a car glass parts company in Calgary, Alberta. "
                    "Answer the admin's question using ONLY the data provided below. "
                    "Be concise, use bullet points and bold for key numbers. "
                    "Format with markdown. If the data doesn't contain what they asked, say so.\n\n"
                    f"{context_text}"
                ),
            },
            {"role": "user", "content": question},
        ]

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"*LLM error: {e}. Falling back to built-in analytics.*\n\n" + None.__class__.__name__


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def answer_question(question):
    """Main entry point — answer a business question about sales/trends."""
    data = _gather_data()
    context_text = _build_context_text(data)

    # Try LLM first if configured
    llm_answer = _try_llm(question, context_text)
    if llm_answer:
        return llm_answer, True  # (answer, used_llm)

    # Fall back to built-in engine
    return _builtin_answer(question, data), False
