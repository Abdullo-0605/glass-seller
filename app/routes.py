"""All Flask routes for the Glass Seller application."""
import os
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, send_file, jsonify, current_app,
)
from werkzeug.utils import secure_filename

from .models import db, Product, WholesaleShipment, ShipmentItem, Order, OrderItem, Invoice
from .auth import login_required, admin_required
from .analytics import answer_question
from .import_utils import (
    parse_pdf_invoice, parse_excel_products,
    export_products_to_excel, export_invoices_to_excel, export_orders_to_excel,
)

main = Blueprint("main", __name__)
admin = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_PDF = {"pdf"}
ALLOWED_EXCEL = {"xlsx", "xls"}


def _allowed(filename, extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


# ---------------------------------------------------------------------------
# CATALOG / STOREFRONT
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    sort = request.args.get("sort", "name")

    query = Product.query
    if category:
        query = query.filter(Product.category == category)
    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(term),
                Product.part_number.ilike(term),
                Product.car_make.ilike(term),
                Product.car_model.ilike(term),
                Product.description.ilike(term),
            )
        )

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())

    products = query.all()
    categories = [r[0] for r in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    cart = session.get("cart", {})
    cart_count = sum(cart.values())

    return render_template(
        "catalog.html",
        products=products,
        categories=categories,
        current_category=category,
        search=search,
        sort=sort,
        cart_count=cart_count,
    )


@main.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template("product_detail.html", product=product, cart_count=cart_count)


# ---------------------------------------------------------------------------
# CART
# ---------------------------------------------------------------------------

@main.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        product = db.session.get(Product, int(pid_str))
        if product:
            line = product.price * qty
            total += line
            items.append({"product": product, "quantity": qty, "line_total": line})
    cart_count = sum(cart.values())
    return render_template("cart.html", items=items, total=total, cart_count=cart_count)


@main.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = db.get_or_404(Product, product_id)
    qty = int(request.form.get("quantity", 1))
    cart = session.get("cart", {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + qty
    session["cart"] = cart
    flash(f"Added {qty}x {product.name} to cart.", "success")
    return redirect(request.referrer or url_for("main.index"))


@main.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    qty = int(request.form.get("quantity", 0))
    cart = session.get("cart", {})
    key = str(product_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    session["cart"] = cart
    flash("Cart updated.", "info")
    return redirect(url_for("main.view_cart"))


@main.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Item removed from cart.", "info")
    return redirect(url_for("main.view_cart"))


@main.route("/cart/clear", methods=["POST"])
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared.", "info")
    return redirect(url_for("main.view_cart"))


# ---------------------------------------------------------------------------
# CHECKOUT (order creation — no payment)
# ---------------------------------------------------------------------------

@main.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        email = request.form.get("customer_email", "").strip()
        phone = request.form.get("customer_phone", "").strip()
        address = request.form.get("customer_address", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("Customer name is required.", "danger")
            return redirect(url_for("main.checkout"))

        order = Order(
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=address,
            notes=notes,
            status="PENDING",
            total_amount=0.0,
        )
        db.session.add(order)
        db.session.flush()

        total = 0.0
        for pid_str, qty in cart.items():
            product = db.session.get(Product, int(pid_str))
            if product:
                line = product.price * qty
                total += line
                oi = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    price=product.price,
                )
                db.session.add(oi)
                product.stock_quantity = max(0, product.stock_quantity - qty)

        order.total_amount = total
        db.session.commit()
        session.pop("cart", None)
        flash(f"Order #{order.id} placed successfully!", "success")
        return redirect(url_for("main.order_confirmation", order_id=order.id))

    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        product = db.session.get(Product, int(pid_str))
        if product:
            line = product.price * qty
            total += line
            items.append({"product": product, "quantity": qty, "line_total": line})
    cart_count = sum(cart.values())
    return render_template("checkout.html", items=items, total=total, cart_count=cart_count)


@main.route("/order/<int:order_id>")
def order_confirmation(order_id):
    order = db.get_or_404(Order, order_id)
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template("order_confirmation.html", order=order, cart_count=cart_count)


# ---------------------------------------------------------------------------
# ADMIN — DASHBOARD
# ---------------------------------------------------------------------------

@admin.route("/")
@admin_required
def dashboard():
    product_count = Product.query.count()
    order_count = Order.query.count()
    pending_orders = Order.query.filter_by(status="PENDING").count()
    shipment_count = WholesaleShipment.query.count()
    invoice_count = Invoice.query.count()
    low_stock = Product.query.filter(Product.stock_quantity <= 5).count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    low_stock_products = Product.query.filter(Product.stock_quantity <= 5).order_by(Product.stock_quantity.asc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        product_count=product_count,
        order_count=order_count,
        pending_orders=pending_orders,
        shipment_count=shipment_count,
        invoice_count=invoice_count,
        low_stock=low_stock,
        total_revenue=total_revenue,
        recent_orders=recent_orders,
        low_stock_products=low_stock_products,
    )


# ---------------------------------------------------------------------------
# ADMIN — PRODUCTS
# ---------------------------------------------------------------------------

@admin.route("/products")
@admin_required
def products():
    category = request.args.get("category", "")
    query = Product.query
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.name).all()
    categories = [r[0] for r in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    return render_template("admin/products.html", products=products, categories=categories, current_category=category)


@admin.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            description=request.form.get("description", ""),
            category=request.form.get("category", "General"),
            car_make=request.form.get("car_make", ""),
            car_model=request.form.get("car_model", ""),
            car_year_start=_int_or_none(request.form.get("car_year_start")),
            car_year_end=_int_or_none(request.form.get("car_year_end")),
            part_number=request.form.get("part_number", ""),
            price=float(request.form.get("price", 0)),
            cost=float(request.form.get("cost", 0)),
            stock_quantity=int(request.form.get("stock_quantity", 0)),
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Product '{p.name}' added.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", product=None)


@admin.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form.get("description", "")
        product.category = request.form.get("category", "General")
        product.car_make = request.form.get("car_make", "")
        product.car_model = request.form.get("car_model", "")
        product.car_year_start = _int_or_none(request.form.get("car_year_start"))
        product.car_year_end = _int_or_none(request.form.get("car_year_end"))
        product.part_number = request.form.get("part_number", "")
        product.price = float(request.form.get("price", 0))
        product.cost = float(request.form.get("cost", 0))
        product.stock_quantity = int(request.form.get("stock_quantity", 0))
        db.session.commit()
        flash(f"Product '{product.name}' updated.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", product=product)


@admin.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted.", "warning")
    return redirect(url_for("admin.products"))


# ---------------------------------------------------------------------------
# ADMIN — ORDERS
# ---------------------------------------------------------------------------

@admin.route("/orders")
@admin_required
def orders():
    status = request.args.get("status", "")
    query = Order.query
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=orders, current_status=status)


@admin.route("/orders/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("admin/order_detail.html", order=order)


@admin.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = db.get_or_404(Order, order_id)
    new_status = request.form.get("status", order.status)
    order.status = new_status
    db.session.commit()
    flash(f"Order #{order.id} status updated to {new_status}.", "success")
    return redirect(url_for("admin.order_detail", order_id=order.id))


@admin.route("/orders/export")
@admin_required
def export_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    buf = export_orders_to_excel(orders)
    return send_file(buf, download_name="orders.xlsx", as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ---------------------------------------------------------------------------
# ADMIN — SHIPMENTS
# ---------------------------------------------------------------------------

@admin.route("/shipments")
@admin_required
def shipments():
    shipments = WholesaleShipment.query.order_by(WholesaleShipment.created_at.desc()).all()
    return render_template("admin/shipments.html", shipments=shipments)


@admin.route("/shipments/add", methods=["GET", "POST"])
@admin_required
def add_shipment():
    if request.method == "POST":
        s = WholesaleShipment(
            supplier=request.form["supplier"],
            invoice_number=request.form.get("invoice_number", ""),
            total_cost=float(request.form.get("total_cost", 0)),
            status=request.form.get("status", "PENDING"),
            notes=request.form.get("notes", ""),
        )
        db.session.add(s)
        db.session.commit()
        flash(f"Shipment from '{s.supplier}' created.", "success")
        return redirect(url_for("admin.shipments"))
    return render_template("admin/shipment_form.html", shipment=None)


@admin.route("/shipments/<int:shipment_id>")
@admin_required
def shipment_detail(shipment_id):
    shipment = db.get_or_404(WholesaleShipment, shipment_id)
    return render_template("admin/shipment_detail.html", shipment=shipment)


@admin.route("/shipments/<int:shipment_id>/receive", methods=["POST"])
@admin_required
def receive_shipment(shipment_id):
    shipment = db.get_or_404(WholesaleShipment, shipment_id)
    shipment.status = "RECEIVED"
    for item in shipment.items:
        item.product.stock_quantity += item.quantity
    db.session.commit()
    flash(f"Shipment '{shipment.invoice_number}' marked as received. Stock updated.", "success")
    return redirect(url_for("admin.shipment_detail", shipment_id=shipment.id))


# ---------------------------------------------------------------------------
# ADMIN — INVOICES & IMPORT
# ---------------------------------------------------------------------------

@admin.route("/invoices")
@admin_required
def invoices():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template("admin/invoices.html", invoices=invoices)


@admin.route("/invoices/<int:invoice_id>")
@admin_required
def invoice_detail(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    return render_template("admin/invoice_detail.html", invoice=invoice)


@admin.route("/invoices/export")
@admin_required
def export_invoices():
    invs = Invoice.query.order_by(Invoice.created_at.desc()).all()
    buf = export_invoices_to_excel(invs)
    return send_file(buf, download_name="invoices.xlsx", as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@admin.route("/import", methods=["GET", "POST"])
@admin_required
def import_data():
    if request.method == "POST":
        import_type = request.form.get("import_type", "")

        if import_type == "pdf_invoice":
            return _handle_pdf_import()
        elif import_type == "excel_products":
            return _handle_excel_import()
        else:
            flash("Unknown import type.", "danger")

    return render_template("admin/import.html")


@admin.route("/products/export")
@admin_required
def export_products():
    products = Product.query.order_by(Product.name).all()
    buf = export_products_to_excel(products)
    return send_file(buf, download_name="products.xlsx", as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _handle_pdf_import():
    file = request.files.get("file")
    if not file or not _allowed(file.filename, ALLOWED_PDF):
        flash("Please upload a valid PDF file.", "danger")
        return redirect(url_for("admin.import_data"))

    try:
        result = parse_pdf_invoice(file)

        upload_dir = os.path.join(current_app.instance_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.seek(0)
        file.save(filepath)

        inv = Invoice(
            invoice_number=result["invoice_number"],
            supplier=result["supplier"],
            total_amount=result["total"],
            raw_text=result["raw_text"],
            file_path=filepath,
            status="IMPORTED",
        )
        db.session.add(inv)

        created = 0
        for item_data in result["items"]:
            existing = None
            if item_data.get("part_number"):
                existing = Product.query.filter_by(part_number=item_data["part_number"]).first()

            if existing:
                existing.cost = item_data["unit_cost"]
                existing.stock_quantity += item_data["quantity"]
            else:
                p = Product(
                    name=item_data["name"],
                    part_number=item_data.get("part_number", ""),
                    cost=item_data["unit_cost"],
                    price=round(item_data["unit_cost"] * 1.5, 2),
                    stock_quantity=item_data["quantity"],
                    category="Imported",
                )
                db.session.add(p)
                created += 1

        shipment = WholesaleShipment(
            supplier=result["supplier"],
            invoice_number=result["invoice_number"],
            total_cost=result["total"],
            status="RECEIVED",
            notes=f"Auto-imported from PDF: {filename}",
        )
        db.session.add(shipment)
        db.session.commit()

        inv.status = "PROCESSED"
        db.session.commit()

        flash(
            f"PDF imported: {len(result['items'])} items found, {created} new products created. "
            f"Invoice #{result['invoice_number']} recorded.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing PDF: {str(e)}", "danger")

    return redirect(url_for("admin.import_data"))


def _handle_excel_import():
    file = request.files.get("file")
    if not file or not _allowed(file.filename, ALLOWED_EXCEL):
        flash("Please upload a valid Excel (.xlsx) file.", "danger")
        return redirect(url_for("admin.import_data"))

    try:
        products = parse_excel_products(file)
        created = 0
        updated = 0

        for pdata in products:
            existing = None
            if pdata.get("part_number"):
                existing = Product.query.filter_by(part_number=pdata["part_number"]).first()

            if existing:
                for key, val in pdata.items():
                    if val and val != "" and val != 0:
                        setattr(existing, key, val)
                updated += 1
            else:
                p = Product(**pdata)
                db.session.add(p)
                created += 1

        db.session.commit()
        flash(f"Excel imported: {created} products created, {updated} updated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing Excel: {str(e)}", "danger")

    return redirect(url_for("admin.import_data"))


# ---------------------------------------------------------------------------
# ADMIN — AI CHAT (Analytics Assistant)
# ---------------------------------------------------------------------------

@admin.route("/chat", methods=["GET"])
@admin_required
def chat():
    return render_template("admin/chat.html")


@admin.route("/chat/ask", methods=["POST"])
@admin_required
def chat_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"answer": "Please ask a question.", "used_llm": False})

    try:
        answer, used_llm = answer_question(question)
        return jsonify({"answer": answer, "used_llm": used_llm})
    except Exception as e:
        return jsonify({"answer": f"Error: {str(e)}", "used_llm": False}), 500


@admin.route("/chat/clear", methods=["POST"])
@admin_required
def chat_clear():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int_or_none(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
