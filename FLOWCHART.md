# Winaris Glass LLC — Application Flowchart

## Page & Route Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WINARIS GLASS LLC                          │
│                     http://localhost:5000                           │
└─────────────────────────────────────────────────────────────────────┘

                              │
                    ┌─────────┴──────────┐
                    │    NAVBAR (all pages)│
                    │  Home │ Catalog │    │
                    │  Glass Finder │     │
                    │  Contact │ Cart │   │
                    │  Login/Register │   │
                    │  Admin (if admin)   │
                    └─────────┬──────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    PUBLIC PAGES         AUTH PAGES          ADMIN PAGES
         │                    │                    │
         ▼                    ▼                    ▼

═══════════════════════════════════════════════════════════════════════
                        PUBLIC PAGES (anyone)
═══════════════════════════════════════════════════════════════════════

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  / (HOME)    │    │  /catalog    │    │  /finder     │
│              │    │              │    │              │
│ Hero image   │    │ Search bar   │    │ Step 1: Year │
│ Stats bar    │    │ Category     │──▶│ Step 2: Make │
│ Photo gallery│──▶│ filter       │    │ Step 3: Model│
│ 3-step guide │    │ Sort options  │    │              │
│ Wholesale CTA│    │ Pagination   │    │ (AJAX calls) │
│ Contact info │    │ Product cards│    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   ▼                   ▼
       │            ┌──────────────┐    ┌──────────────┐
       │            │/product/<id> │    │/finder/results│
       │            │              │    │              │
       │            │ Product name │    │ Matched parts│
       │            │ Price, stock │    │ In-stock first│
       │            │ Add to cart  │    │ Out-of-stock │
       │            │ Vehicle info │    │ dimmed       │
       │            └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   ▼                   │
       │            ┌──────────────┐           │
       │            │  /cart       │◀──────────┘
       │            │              │
       │            │ Cart items   │    POST /cart/add/<id>
       │            │ Update qty   │    POST /cart/update/<id>
       │            │ Remove item  │    POST /cart/remove/<id>
       │            │ Clear cart   │    POST /cart/clear
       │            │ Order summary│
       │            └──────┬───────┘
       │                   │
       │                   ▼  (login required)
       │            ┌──────────────┐
       │            │  /checkout   │
       │            │              │
       │            │ Customer info│
       │            │ (auto-filled │
       │            │  from profile│)
       │            │ Order notes  │
       │            │ Place Order  │───▶ Deducts stock
       │            └──────┬───────┘
       │                   │
       │                   ▼
       │            ┌──────────────┐
       │            │/order/<id>   │
       │            │              │
       │            │ Confirmation │
       │            │ Order #, items│
       │            │ Status: Pending│
       │            └──────────────┘
       │
       ▼
┌──────────────┐
│  /contact    │
│              │
│ Address card │
│ Phone card   │
│ Email card   │
│ Google Map   │
│ Business hrs │
└──────────────┘


═══════════════════════════════════════════════════════════════════════
                     AUTH PAGES (login/register)
═══════════════════════════════════════════════════════════════════════

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ /auth/login  │    │/auth/register│    │/auth/profile │
│              │    │              │    │              │
│ Username/    │    │ Username     │    │ Edit name,   │
│ email +      │    │ Email        │    │ email, phone │
│ password     │    │ Password x2  │    │ address      │
│              │    │ Phone, addr  │    │ Change pw    │
│ ──▶ Admin?   │    │              │    │              │
│   /admin/    │    │ Creates      │    │ (login req)  │
│ ──▶ Customer?│    │ "customer"   │    │              │
│   /          │    │ role account │    │              │
└──────────────┘    └──────────────┘    └──────────────┘

                    POST /auth/logout ──▶ clears session


═══════════════════════════════════════════════════════════════════════
                  ADMIN PAGES (admin role required)
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│                    /admin/ (Dashboard)                       │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Products │ │Pending  │ │Total    │ │Revenue  │          │
│  │ count   │ │Orders   │ │Orders   │ │  $$$    │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                             │
│  Recent Orders table    │    Low Stock Alert table          │
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │ DANGER ZONE: Reset All Stock & Prices       │           │
│  │ Type "RESET STOCK" to confirm               │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
       │
       ├──▶ /admin/products ──────────────────────────────────┐
       │    │ Product table with inline edit (cost/price/qty) │
       │    │ Quick save ✓ button per row                     │
       │    │ Filter by category                              │
       │    ├──▶ /admin/products/add (form)                   │
       │    ├──▶ /admin/products/<id>/edit (form)             │
       │    ├──▶ /admin/products/<id>/quick-update (AJAX)     │
       │    └──▶ /admin/products/<id>/delete                  │
       │
       ├──▶ /admin/orders ────────────────────────────────────┐
       │    │ Order table, filter by status                    │
       │    ├──▶ /admin/orders/<id> (detail + status update)  │
       │    │    └──▶ Cancel ──▶ RESTORES STOCK               │
       │    │    └──▶ Un-cancel ──▶ RE-DEDUCTS STOCK          │
       │    └──▶ /admin/orders/export?fmt=xlsx|csv|ods        │
       │
       ├──▶ /admin/shipments ─────────────────────────────────┐
       │    │ Shipment table                                   │
       │    ├──▶ /admin/shipments/add (form)                  │
       │    ├──▶ /admin/shipments/<id> (detail)               │
       │    └──▶ /admin/shipments/<id>/receive                │
       │         └──▶ Marks received, ADDS stock              │
       │
       ├──▶ /admin/invoices ──────────────────────────────────┐
       │    │ Invoice table                                    │
       │    ├──▶ /admin/invoices/<id> (detail + raw text)     │
       │    └──▶ /admin/invoices/export?fmt=xlsx|csv|ods      │
       │
       ├──▶ /admin/chat ──────────────────────────────────────┐
       │    │ AI Analytics Assistant                           │
       │    │ "What's selling best?" "Sales by category"      │
       │    ├──▶ POST /admin/chat/ask (AJAX, returns JSON)    │
       │    └──▶ POST /admin/chat/clear                       │
       │
       └──▶ /admin/import ────────────────────────────────────┐
            │                                                  │
            │  ┌─────────────┐    ┌──────────────────┐        │
            │  │ PDF Invoice │    │ Spreadsheet      │        │
            │  │ Upload      │    │ Upload           │        │
            │  │ (.pdf)      │    │ (.xlsx .csv .ods)│        │
            │  └──────┬──────┘    └────────┬─────────┘        │
            │         │                    │                   │
            │         ▼                    ▼                   │
            │  Auto-extracts        ┌──────────────────┐      │
            │  items, creates       │ REVIEW PAGE      │      │
            │  invoice record,      │                  │      │
            │  creates shipment     │ Shows all parsed │      │
            │                       │ rows with:       │      │
            │                       │ • Matched vs New │      │
            │                       │ • File price/qty │      │
            │                       │ • Current DB vals│      │
            │                       │ • Editable final │      │
            │                       │   price/cost/qty │      │
            │                       │ • % Markup tool  │      │
            │                       │ • Skip checkbox  │      │
            │                       └────────┬─────────┘      │
            │                                │                 │
            │                                ▼                 │
            │                       POST /admin/import/confirm │
            │                       • Matched ──▶ ADD to qty,  │
            │                         update price/cost        │
            │                       • New ──▶ CREATE product   │
            │                                                  │
            │  Export buttons: Products/Orders/Invoices        │
            │  Each in 3 formats: XLSX, CSV, ODS              │
            └──────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
                    GLASS FINDER API (AJAX/JSON)
═══════════════════════════════════════════════════════════════════════

  /finder (page)
      │
      │  JavaScript fetch() calls:
      │
      ├──▶ GET /finder/api/years ──▶ returns [2026, 2025, ... 1950]
      │         (filtered: 1950-2026, car_make not empty)
      │
      ├──▶ GET /finder/api/makes?year=2020 ──▶ returns ["Acura","BMW",...]
      │
      ├──▶ GET /finder/api/models?year=2020&make=Toyota ──▶ ["Camry","Corolla",...]
      │
      └──▶ Redirects to /finder/results?year=2020&make=Toyota&model=Camry
              (server-rendered page with product cards)


═══════════════════════════════════════════════════════════════════════
                      DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  Browser │────▶│  Flask   │────▶│SQLAlchemy│────▶│  SQLite  │
  │  (HTML,  │◀────│  Routes  │◀────│  ORM     │◀────│  DB      │
  │  JS,CSS) │     │          │     │          │     │          │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                │
       │  AJAX calls    │  Jinja2 templates
       │  (fetch JSON)  │  (server-side render)
       │                │
       │  • Finder API  │  • All page HTML
       │  • Chat API    │  • Forms, tables
       │  • Quick-update│  • Flash messages
       │                │
       │                │  Session (cookies)
       │                │  • user_id (auth)
       │                │  • cart items
       │                │  • import_review_id


═══════════════════════════════════════════════════════════════════════
                      DATABASE MODELS
═══════════════════════════════════════════════════════════════════════

  User ─────────── (auth: admin or customer)
    │
  Product ──────── (car glass part, with make/model/year/price/stock)
    │       │
    │       ├──── OrderItem ──── Order (customer purchase)
    │       │
    │       └──── ShipmentItem ── WholesaleShipment (supplier delivery)
    │
  Invoice ──────── (imported PDF record with raw text)


═══════════════════════════════════════════════════════════════════════
                    STOCK FLOW
═══════════════════════════════════════════════════════════════════════

  Stock INCREASES when:
    • Admin imports file (adds qty from file)
    • Admin marks shipment as "Received"
    • Admin cancels an order (restores qty)
    • Admin manually edits stock in products table

  Stock DECREASES when:
    • Customer places an order (checkout deducts qty)
    • Admin un-cancels a previously cancelled order

  Stock RESETS when:
    • Admin uses "Reset All Stock & Prices" (sets all to 0)
```
