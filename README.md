# AutoGlass Pro — Car Glass Parts Inventory & Sales

A pure Python (Flask) web application for tracking, selling, and managing car glass parts inventory.

## Features

- **Product Catalog** — Browse, search, and filter car glass parts by category, make, model, year
- **Shopping Cart** — Add to cart, update quantities, checkout with customer info (no payment processing)
- **Order Management** — Track orders with status workflow (Pending → Approved → Completed)
- **Wholesale Shipments** — Track incoming shipments from suppliers, auto-update stock on receipt
- **PDF Invoice Import** — Upload supplier PDF invoices to auto-extract products and create records
- **Excel Import/Export** — Import product catalogs from Excel, export products/orders/invoices to Excel
- **Invoice Tracker** — Record and view all imported invoices with extracted raw text
- **Admin Dashboard** — Stats overview, low stock alerts, recent orders at a glance

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** Jinja2, Bootstrap 5, Bootstrap Icons
- **Import:** pdfplumber (PDF), openpyxl (Excel)

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the database with sample data
python seed.py

# 4. Run the app
python run.py
```

Open **http://localhost:5000** in your browser.

## Project Structure

```
glass-seller/
├── app/
│   ├── __init__.py
│   ├── create_app.py       # Flask app factory
│   ├── models.py           # SQLAlchemy models
│   ├── routes.py           # All routes (catalog, cart, admin)
│   └── import_utils.py     # PDF & Excel import/export
├── templates/
│   ├── base.html           # Base layout
│   ├── catalog.html        # Product catalog
│   ├── cart.html            # Shopping cart
│   ├── checkout.html       # Checkout form
│   ├── product_detail.html
│   ├── order_confirmation.html
│   └── admin/              # Admin panel templates
├── instance/               # SQLite DB (auto-created)
├── requirements.txt
├── seed.py                 # Database seeder
└── run.py                  # Entry point
```

## Importing Data

### PDF Invoices
Go to **Admin → Import Data → Import PDF Invoice**. Upload a supplier PDF and the system will:
- Parse tables and text for line items
- Create/update products by part number
- Record the invoice and create a shipment

### Excel Products
Go to **Admin → Import Data → Import Products from Excel**. Columns are auto-matched:
`Name`, `Category`, `Make`, `Model`, `Year Start`, `Year End`, `Part Number`, `Price`, `Cost`, `Stock`, `Description`
