"""All Flask routes for the Glass Seller application."""
import os
import json
import uuid
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, send_file, jsonify, current_app,
)
from werkzeug.utils import secure_filename

from .models import db, Product, WholesaleShipment, ShipmentItem, Order, OrderItem, Invoice, User, NAGS_PREFIXES, nags_category
from .auth import login_required, approved_required, admin_required
from .analytics import answer_question
from .import_utils import (
    parse_pdf_invoice, parse_products_file,
    export_products, export_orders, export_invoices,
)

main = Blueprint("main", __name__)
admin = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_PDF = {"pdf"}
ALLOWED_SPREADSHEET = {"xlsx", "xls", "csv", "ods"}


def _allowed(filename, extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


def _get_ext(filename):
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


# ---------------------------------------------------------------------------
# AUTO GLASS FINDER (Step-by-step wizard)
# ---------------------------------------------------------------------------

@main.route("/finder")
def finder():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template("finder.html", step="year", cart_count=cart_count)


MIN_VALID_YEAR = 1950
MAX_VALID_YEAR = 2026


@main.route("/finder/api/years")
def finder_years():
    products = Product.query.filter(
        Product.car_year_start.isnot(None),
        Product.car_year_start >= MIN_VALID_YEAR,
        Product.car_year_end <= MAX_VALID_YEAR,
        Product.car_make != "",
    ).all()
    years_set = set()
    for p in products:
        if p.car_year_start and p.car_year_end:
            s = max(p.car_year_start, MIN_VALID_YEAR)
            e = min(p.car_year_end, MAX_VALID_YEAR)
            for y in range(s, e + 1):
                years_set.add(y)
    years = sorted(years_set, reverse=True)
    return jsonify(years)


@main.route("/finder/api/makes")
def finder_makes():
    year = request.args.get("year", type=int)
    query = Product.query.filter(
        Product.car_make != "",
        Product.car_year_start >= MIN_VALID_YEAR,
        Product.car_year_end <= MAX_VALID_YEAR,
    )
    if year and MIN_VALID_YEAR <= year <= MAX_VALID_YEAR:
        query = query.filter(
            Product.car_year_start <= year,
            Product.car_year_end >= year,
        )
    makes = sorted(set(r.car_make for r in query.all() if r.car_make))
    return jsonify(makes)


@main.route("/finder/api/models")
def finder_models():
    year = request.args.get("year", type=int)
    make = request.args.get("make", "")
    query = Product.query.filter(
        Product.car_make == make,
        Product.car_model != "",
        Product.car_year_start >= MIN_VALID_YEAR,
        Product.car_year_end <= MAX_VALID_YEAR,
    )
    if year and MIN_VALID_YEAR <= year <= MAX_VALID_YEAR:
        query = query.filter(
            Product.car_year_start <= year,
            Product.car_year_end >= year,
        )
    models = sorted(set(r.car_model for r in query.all() if r.car_model))
    return jsonify(models)


@main.route("/finder/results")
@login_required
def finder_results():
    year = request.args.get("year", type=int)
    make = request.args.get("make", "")
    model = request.args.get("model", "")

    # Primary: products with proper make/model/year fields
    query = Product.query
    if year:
        query = query.filter(Product.car_year_start <= year, Product.car_year_end >= year)
    if make:
        query = query.filter(Product.car_make == make)
    if model:
        query = query.filter(Product.car_model == model)
    results = query.all()

    # Also find imported products that mention this make+model in their name
    # (catches orphan imports that didn't get proper make/model fields)
    if make and model:
        name_matches = Product.query.filter(
            Product.name.ilike(f"%{make}%"),
            Product.name.ilike(f"%{model}%"),
            Product.price > 0,
        ).all()
        existing_ids = {p.id for p in results}
        for p in name_matches:
            if p.id not in existing_ids:
                results.append(p)

    # Sort: in-stock first, then by price (highest first), then name
    results.sort(key=lambda p: (0 if p.stock_quantity > 0 else 1, -p.price, p.name))

    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template(
        "finder_results.html",
        products=results, year=year, make=make, model=model, cart_count=cart_count,
    )


# ---------------------------------------------------------------------------
# HOMEPAGE & CONTACT
# ---------------------------------------------------------------------------

@main.route("/")
def home():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    product_count = Product.query.count()
    make_count = db.session.query(Product.car_make).filter(Product.car_make != "").distinct().count()
    in_stock = Product.query.filter(Product.stock_quantity > 0).count()
    return render_template("home.html", cart_count=cart_count,
                           product_count=product_count, make_count=make_count, in_stock=in_stock)


@main.route("/contact")
def contact():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template("contact.html", cart_count=cart_count)


# ---------------------------------------------------------------------------
# CATALOG / STOREFRONT
# ---------------------------------------------------------------------------

@main.route("/catalog")
@login_required
def index():
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    nags_filter = request.args.get("nags", "")
    sort = request.args.get("sort", "name")
    page = request.args.get("page", 1, type=int)
    per_page = 24

    query = Product.query
    if category:
        query = query.filter(Product.category == category)
    if nags_filter:
        query = query.filter(Product.nags_code.ilike(f"{nags_filter}%"))
    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(term),
                Product.part_number.ilike(term),
                Product.nags_code.ilike(term),
                Product.car_make.ilike(term),
                Product.car_model.ilike(term),
            )
        )

    # Always show in-stock first, then apply sort within each group
    in_stock_first = db.case((Product.stock_quantity > 0, 0), else_=1)

    if sort == "price_asc":
        query = query.order_by(in_stock_first, Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(in_stock_first, Product.price.desc())
    elif sort == "newest":
        query = query.order_by(in_stock_first, Product.created_at.desc())
    else:
        query = query.order_by(in_stock_first, Product.name.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = [r[0] for r in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    cart = session.get("cart", {})
    cart_count = sum(cart.values())

    return render_template(
        "catalog.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category,
        search=search,
        nags_filter=nags_filter,
        nags_prefixes=NAGS_PREFIXES,
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
# CHECKOUT — payment options, pickup/delivery, multi-address
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
        notes = request.form.get("notes", "").strip()

        # Payment method
        payment_method = request.form.get("payment_method", "cash")  # cash | zelle_echeck

        # Fulfillment type
        fulfillment_type = request.form.get("fulfillment_type", "pickup")  # pickup | delivery

        # Pickup details
        pickup_time = request.form.get("pickup_time", "").strip()

        # Delivery details — collect multiple addresses
        delivery_time = request.form.get("delivery_time", "").strip()
        delivery_note = request.form.get("delivery_note", "").strip()
        delivery_addresses_list = []
        for i in range(1, 11):
            addr = request.form.get(f"delivery_address_{i}", "").strip()
            if addr:
                delivery_addresses_list.append(addr)

        if not name:
            flash("Full name is required.", "danger")
            return redirect(url_for("main.checkout"))

        if fulfillment_type == "pickup" and not pickup_time:
            flash("Please provide an approximate pickup time.", "danger")
            return redirect(url_for("main.checkout"))

        if fulfillment_type == "delivery" and not delivery_addresses_list:
            flash("Please provide at least one delivery address.", "danger")
            return redirect(url_for("main.checkout"))

        order = Order(
            user_id=g.user.id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=delivery_addresses_list[0] if delivery_addresses_list else "",
            payment_method=payment_method,
            payment_status="unpaid",
            fulfillment_type=fulfillment_type,
            pickup_time=pickup_time if fulfillment_type == "pickup" else "",
            delivery_addresses=json.dumps(delivery_addresses_list) if fulfillment_type == "delivery" else "",
            delivery_time=delivery_time if fulfillment_type == "delivery" else "",
            delivery_note=delivery_note,
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

    pending_users = User.query.filter_by(approval_status="pending").count()

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
        pending_users=pending_users,
    )


# ---------------------------------------------------------------------------
# ADMIN — USER APPROVAL
# ---------------------------------------------------------------------------

@admin.route("/users")
@admin_required
def manage_users():
    status_filter = request.args.get("status", "pending")
    if status_filter == "all":
        users = User.query.filter(User.role != "admin").order_by(User.created_at.desc()).all()
    else:
        users = User.query.filter_by(approval_status=status_filter).filter(User.role != "admin").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, current_status=status_filter)


@admin.route("/users/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_user(user_id):
    user = db.get_or_404(User, user_id)
    user.is_approved = True
    user.approval_status = "approved"
    db.session.commit()
    flash(f"User '{user.full_name or user.username}' has been approved.", "success")
    return redirect(url_for("admin.manage_users"))


@admin.route("/users/<int:user_id>/reject", methods=["POST"])
@admin_required
def reject_user(user_id):
    user = db.get_or_404(User, user_id)
    user.is_approved = False
    user.approval_status = "rejected"
    db.session.commit()
    flash(f"User '{user.full_name or user.username}' has been rejected.", "warning")
    return redirect(url_for("admin.manage_users"))


@admin.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.is_admin:
        flash("Cannot delete admin users.", "danger")
        return redirect(url_for("admin.manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "warning")
    return redirect(url_for("admin.manage_users"))


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


@admin.route("/products/<int:product_id>/quick-update", methods=["POST"])
@admin_required
def quick_update_product(product_id):
    product = db.get_or_404(Product, product_id)
    new_price = request.form.get("price")
    new_cost = request.form.get("cost")
    new_qty = request.form.get("stock_quantity")
    if new_price is not None and new_price.strip():
        product.price = float(new_price)
    if new_cost is not None and new_cost.strip():
        product.cost = float(new_cost)
    if new_qty is not None and new_qty.strip():
        product.stock_quantity = int(new_qty)
    db.session.commit()
    flash(f"Updated {product.name}.", "success")
    return redirect(request.referrer or url_for("admin.products"))


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
    old_status = order.status
    new_status = request.form.get("status", order.status)

    # If cancelling a non-cancelled order, restore stock
    if new_status == "CANCELLED" and old_status != "CANCELLED":
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
        flash(f"Order #{order.id} cancelled — stock restored.", "warning")
    # If un-cancelling (reactivating a cancelled order), deduct stock again
    elif old_status == "CANCELLED" and new_status != "CANCELLED":
        for item in order.items:
            if item.product:
                item.product.stock_quantity = max(0, item.product.stock_quantity - item.quantity)
        flash(f"Order #{order.id} reactivated — stock deducted.", "info")
    else:
        flash(f"Order #{order.id} status updated to {new_status}.", "success")

    order.status = new_status
    db.session.commit()
    return redirect(url_for("admin.order_detail", order_id=order.id))


@admin.route("/orders/export")
@admin_required
def export_orders_route():
    fmt = request.args.get("fmt", "xlsx")
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    buf, filename, mimetype = export_orders(all_orders, fmt)
    return send_file(buf, download_name=filename, as_attachment=True, mimetype=mimetype)


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
def export_invoices_route():
    fmt = request.args.get("fmt", "xlsx")
    invs = Invoice.query.order_by(Invoice.created_at.desc()).all()
    buf, filename, mimetype = export_invoices(invs, fmt)
    return send_file(buf, download_name=filename, as_attachment=True, mimetype=mimetype)


@admin.route("/import", methods=["GET", "POST"])
@admin_required
def import_data():
    if request.method == "POST":
        import_type = request.form.get("import_type", "")

        if import_type == "pdf_invoice":
            return _handle_pdf_import()
        elif import_type == "spreadsheet_products":
            return _handle_spreadsheet_import()
        else:
            flash("Unknown import type.", "danger")

    return render_template("admin/import.html")


@admin.route("/clear-database", methods=["POST"])
@admin_required
def clear_database():
    confirm = request.form.get("confirm", "")
    if confirm != "RESET STOCK":
        flash("You must type 'RESET STOCK' to confirm.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Reset all stock to 0 and prices to 0 — keeps products, orders, and finder intact
    Product.query.update({Product.stock_quantity: 0, Product.price: 0.0, Product.cost: 0.0})
    db.session.commit()
    count = Product.query.count()
    flash(f"Stock reset. All {count} products set to 0 stock and $0 price. Orders and products preserved.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin.route("/products/export")
@admin_required
def export_products_route():
    fmt = request.args.get("fmt", "xlsx")
    products = Product.query.order_by(Product.name).all()
    buf, filename, mimetype = export_products(products, fmt)
    return send_file(buf, download_name=filename, as_attachment=True, mimetype=mimetype)


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


def _find_existing_product(pdata):
    """Find an existing product matching the import data."""
    pn = (pdata.get("part_number") or "").strip()
    make = (pdata.get("car_make") or "").strip()
    model = (pdata.get("car_model") or "").strip()
    name = (pdata.get("name") or "").strip()

    if pn:
        existing = Product.query.filter_by(part_number=pn).first()
        if existing:
            return existing

    if make and model:
        q = Product.query.filter(
            db.func.lower(Product.car_make) == make.lower(),
            db.func.lower(Product.car_model) == model.lower(),
        )
        if pdata.get("car_year_start"):
            q = q.filter(Product.car_year_start <= pdata["car_year_start"],
                         Product.car_year_end >= pdata["car_year_start"])
        existing = q.first()
        if existing:
            return existing

    if name:
        existing = Product.query.filter(db.func.lower(Product.name) == name.lower()).first()
        if existing:
            return existing

    return None


def _handle_spreadsheet_import():
    """Step 1: Parse file and show review page for admin to edit prices."""
    file = request.files.get("file")
    if not file or not _allowed(file.filename, ALLOWED_SPREADSHEET):
        flash("Please upload a valid file (.xlsx, .csv, or .ods).", "danger")
        return redirect(url_for("admin.import_data"))

    try:
        filename = secure_filename(file.filename)
        parsed = parse_products_file(file, filename)

        review_items = []
        for i, pdata in enumerate(parsed):
            existing = _find_existing_product(pdata)

            file_qty = pdata.get("stock_quantity") or 0
            file_cost = pdata.get("cost") or 0.0
            file_price = pdata.get("price") or 0.0
            if isinstance(file_qty, str):
                file_qty = int(float(file_qty)) if file_qty.strip() else 0
            if isinstance(file_cost, str):
                file_cost = float(file_cost) if file_cost.strip() else 0.0
            if isinstance(file_price, str):
                file_price = float(file_price) if file_price.strip() else 0.0

            review_items.append({
                "idx": i,
                "name": pdata.get("name", ""),
                "part_number": pdata.get("part_number", ""),
                "car_make": pdata.get("car_make", ""),
                "car_model": pdata.get("car_model", ""),
                "car_year_start": pdata.get("car_year_start"),
                "car_year_end": pdata.get("car_year_end"),
                "category": pdata.get("category", "Auto Glass"),
                "file_qty": file_qty,
                "file_cost": file_cost,
                "file_price": file_price,
                "matched": existing is not None,
                "matched_id": existing.id if existing else None,
                "matched_name": existing.name if existing else None,
                "current_qty": existing.stock_quantity if existing else 0,
                "current_price": existing.price if existing else 0.0,
                "current_cost": existing.cost if existing else 0.0,
            })

        # Save to temp file (session cookies are too small for this data)
        review_id = str(uuid.uuid4())
        tmp_dir = os.path.join(current_app.instance_path, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, f"review_{review_id}.json")
        with open(tmp_path, "w") as f:
            json.dump(review_items[:500], f)
        session["import_review_id"] = review_id

        matched = sum(1 for r in review_items if r["matched"])
        new = sum(1 for r in review_items if not r["matched"])

        return render_template(
            "admin/import_review.html",
            items=review_items[:500],
            total_rows=len(parsed),
            matched_count=matched,
            new_count=new,
            review_id=review_id,
        )
    except Exception as e:
        flash(f"Error parsing file: {str(e)}", "danger")
        return redirect(url_for("admin.import_data"))


@admin.route("/import/confirm", methods=["POST"])
@admin_required
def import_confirm():
    """Step 2: Apply reviewed import data with admin-edited prices."""
    review_id = session.pop("import_review_id", "")
    if not review_id:
        flash("No import data to confirm. Please upload a file first.", "warning")
        return redirect(url_for("admin.import_data"))

    tmp_path = os.path.join(current_app.instance_path, "tmp", f"review_{review_id}.json")
    if not os.path.exists(tmp_path):
        flash("Import data expired. Please upload the file again.", "warning")
        return redirect(url_for("admin.import_data"))

    with open(tmp_path, "r") as f:
        review_items = json.load(f)
    os.remove(tmp_path)

    if not review_items:
        flash("No import data to confirm.", "warning")
        return redirect(url_for("admin.import_data"))

    created = 0
    updated = 0

    for item in review_items:
        idx = item["idx"]
        # Get admin-edited values from the form
        final_price = float(request.form.get(f"price_{idx}", item["file_price"]) or 0)
        final_cost = float(request.form.get(f"cost_{idx}", item["file_cost"]) or 0)
        final_qty = int(request.form.get(f"qty_{idx}", item["file_qty"]) or 0)
        skip = request.form.get(f"skip_{idx}")

        if skip:
            continue

        if item["matched"] and item["matched_id"]:
            existing = db.session.get(Product, item["matched_id"])
            if existing:
                if final_qty > 0:
                    existing.stock_quantity += final_qty
                if final_cost > 0:
                    existing.cost = final_cost
                if final_price > 0:
                    existing.price = final_price
                if not existing.part_number and item.get("part_number"):
                    existing.part_number = item["part_number"]
                if not existing.car_make and item.get("car_make"):
                    existing.car_make = item["car_make"]
                if not existing.car_model and item.get("car_model"):
                    existing.car_model = item["car_model"]
                updated += 1
        else:
            p = Product(
                name=item["name"],
                part_number=item.get("part_number", ""),
                car_make=item.get("car_make", ""),
                car_model=item.get("car_model", ""),
                car_year_start=item.get("car_year_start"),
                car_year_end=item.get("car_year_end"),
                category=item.get("category", "Auto Glass"),
                price=final_price,
                cost=final_cost,
                stock_quantity=final_qty,
                description=item.get("name", ""),
            )
            db.session.add(p)
            created += 1

    db.session.commit()
    flash(f"Import confirmed: {created} new products added, {updated} existing products updated.", "success")
    return redirect(url_for("admin.products"))


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
