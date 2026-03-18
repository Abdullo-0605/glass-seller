"""Utilities for importing product data from PDF invoices and Excel files."""
import re
from io import BytesIO
from datetime import datetime

import pdfplumber
from openpyxl import Workbook, load_workbook


# ---------------------------------------------------------------------------
# PDF Invoice Parsing
# ---------------------------------------------------------------------------

def parse_pdf_invoice(file_storage):
    """
    Read a PDF invoice and extract structured line-item data.

    Attempts to find tabular data first; falls back to regex-based extraction
    from raw text.  Returns a dict with metadata and a list of item dicts.
    """
    raw_text = ""
    tables = []

    pdf_bytes = file_storage.read()
    file_storage.seek(0)

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            raw_text += page_text + "\n"

            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)

    result = {
        "invoice_number": _extract_invoice_number(raw_text),
        "supplier": _extract_supplier(raw_text),
        "date": _extract_date(raw_text),
        "raw_text": raw_text.strip(),
        "items": [],
        "total": 0.0,
    }

    if tables:
        result["items"] = _parse_table_items(tables)
    else:
        result["items"] = _parse_text_items(raw_text)

    result["total"] = sum(
        (item.get("quantity", 0) * item.get("unit_cost", 0)) for item in result["items"]
    )

    return result


def _extract_invoice_number(text):
    patterns = [
        r"(?:Invoice|Inv)[\s#.:]*(\S+)",
        r"(?:Invoice Number|Invoice No)[:\s]*(\S+)",
        r"#\s*(\d{3,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return f"PDF-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _extract_supplier(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        return lines[0][:120]
    return "Unknown Supplier"


def _extract_date(text):
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"(?:Date)[:\s]*(\S+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return datetime.now().strftime("%Y-%m-%d")


def _parse_table_items(tables):
    """Extract items from PDF table data."""
    items = []
    for table in tables:
        if not table or len(table) < 2:
            continue
        header = [str(c).lower().strip() if c else "" for c in table[0]]

        name_idx = _find_col(header, ["description", "item", "product", "name", "part"])
        qty_idx = _find_col(header, ["qty", "quantity", "count"])
        cost_idx = _find_col(header, ["price", "cost", "unit", "rate", "amount"])
        part_idx = _find_col(header, ["part no", "part #", "part number", "sku", "code"])

        for row in table[1:]:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            item = {
                "name": _safe_cell(row, name_idx),
                "quantity": _safe_int(row, qty_idx, 1),
                "unit_cost": _safe_float(row, cost_idx, 0.0),
                "part_number": _safe_cell(row, part_idx),
            }
            if item["name"]:
                items.append(item)
    return items


def _parse_text_items(text):
    """Fallback: extract items from raw text using regex patterns."""
    items = []
    patterns = [
        r"(.+?)\s+(\d+)\s+\$?([\d,]+\.?\d*)",
        r"(\d+)\s*x\s+(.+?)\s+@?\s*\$?([\d,]+\.?\d*)",
    ]
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for pat in patterns:
            m = re.match(pat, line)
            if m:
                groups = m.groups()
                if pat == patterns[0]:
                    items.append({
                        "name": groups[0].strip(),
                        "quantity": int(groups[1]),
                        "unit_cost": float(groups[2].replace(",", "")),
                        "part_number": "",
                    })
                else:
                    items.append({
                        "name": groups[1].strip(),
                        "quantity": int(groups[0]),
                        "unit_cost": float(groups[2].replace(",", "")),
                        "part_number": "",
                    })
                break
    return items


def _find_col(header, keywords):
    for i, h in enumerate(header):
        for kw in keywords:
            if kw in h:
                return i
    return None


def _safe_cell(row, idx):
    if idx is not None and idx < len(row) and row[idx]:
        return str(row[idx]).strip()
    return ""


def _safe_int(row, idx, default=0):
    try:
        return int(float(_safe_cell(row, idx)))
    except (ValueError, TypeError):
        return default


def _safe_float(row, idx, default=0.0):
    try:
        return float(_safe_cell(row, idx).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Excel Import / Export
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = {
    "name": ["name", "product", "description", "item", "part name", "glass type"],
    "category": ["category", "type", "glass category"],
    "car_make": ["make", "car make", "vehicle make", "manufacturer"],
    "car_model": ["model", "car model", "vehicle model"],
    "car_year_start": ["year start", "year from", "from year", "start year"],
    "car_year_end": ["year end", "year to", "to year", "end year"],
    "part_number": ["part number", "part no", "part #", "sku", "code", "oem number"],
    "price": ["price", "sell price", "selling price", "retail price"],
    "cost": ["cost", "unit cost", "buy price", "wholesale price"],
    "stock_quantity": ["stock", "quantity", "qty", "inventory", "stock quantity"],
    "description": ["description", "notes", "details", "info"],
}


def parse_excel_products(file_storage):
    """
    Parse an Excel (.xlsx) file and return a list of product dicts.
    Auto-maps column headers to product fields using fuzzy matching.
    """
    wb = load_workbook(filename=BytesIO(file_storage.read()), read_only=True, data_only=True)
    file_storage.seek(0)

    ws = wb.active
    if ws is None:
        return []

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return []

    header = [str(c).lower().strip() if c else "" for c in rows[0]]
    col_map = _map_columns(header)

    products = []
    for row in rows[1:]:
        if all(c is None or str(c).strip() == "" for c in row):
            continue

        product = {}
        for field, col_idx in col_map.items():
            val = row[col_idx] if col_idx < len(row) else None
            if val is None:
                val = ""
            product[field] = val

        if not product.get("name"):
            continue

        product["price"] = _to_float(product.get("price", 0))
        product["cost"] = _to_float(product.get("cost", 0))
        product["stock_quantity"] = _to_int(product.get("stock_quantity", 0))
        product["car_year_start"] = _to_int(product.get("car_year_start"))
        product["car_year_end"] = _to_int(product.get("car_year_end"))
        product.setdefault("category", "General")
        product.setdefault("description", "")

        products.append(product)

    wb.close()
    return products


def _map_columns(header):
    """Map header columns to product fields using keyword matching."""
    col_map = {}
    for field, keywords in EXPECTED_COLUMNS.items():
        for i, h in enumerate(header):
            for kw in keywords:
                if kw in h:
                    col_map[field] = i
                    break
            if field in col_map:
                break
    return col_map


def _to_float(val):
    try:
        return float(str(val).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _to_int(val):
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Excel Export
# ---------------------------------------------------------------------------

def export_products_to_excel(products):
    """Export a list of product dicts/objects to an in-memory Excel file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = [
        "ID", "Name", "Category", "Car Make", "Car Model",
        "Year Start", "Year End", "Part Number",
        "Price", "Cost", "Stock Qty", "Description",
    ]
    ws.append(headers)

    for p in products:
        ws.append([
            p.id, p.name, p.category, p.car_make, p.car_model,
            p.car_year_start, p.car_year_end, p.part_number,
            p.price, p.cost, p.stock_quantity, p.description,
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def export_invoices_to_excel(invoices):
    """Export invoices list to an in-memory Excel file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"

    headers = ["ID", "Invoice #", "Supplier", "Date", "Total", "Status", "Notes"]
    ws.append(headers)

    for inv in invoices:
        ws.append([
            inv.id, inv.invoice_number, inv.supplier,
            inv.date.strftime("%Y-%m-%d") if inv.date else "",
            inv.total_amount, inv.status, inv.notes,
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def export_orders_to_excel(orders):
    """Export orders list to an in-memory Excel file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    headers = [
        "Order ID", "Customer", "Email", "Phone", "Address",
        "Status", "Total", "Items", "Date", "Notes",
    ]
    ws.append(headers)

    for o in orders:
        item_summary = "; ".join(
            f"{it.product.name} x{it.quantity}" for it in o.items if it.product
        )
        ws.append([
            o.id, o.customer_name, o.customer_email, o.customer_phone,
            o.customer_address, o.status, o.total_amount, item_summary,
            o.created_at.strftime("%Y-%m-%d") if o.created_at else "",
            o.notes,
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
