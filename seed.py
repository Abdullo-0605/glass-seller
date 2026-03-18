"""Seed the database with sample car glass products."""
from app.create_app import create_app
from app.models import db, User, Product, WholesaleShipment, ShipmentItem, Order, OrderItem

app = create_app()

PRODUCTS = [
    {
        "name": "Front Windshield - Toyota Camry 2020-2024",
        "description": "OEM-quality laminated front windshield glass for Toyota Camry models 2020-2024. UV protection and acoustic dampening.",
        "category": "Windshield",
        "car_make": "Toyota",
        "car_model": "Camry",
        "car_year_start": 2020,
        "car_year_end": 2024,
        "part_number": "WS-TCAM-2024",
        "price": 289.99,
        "cost": 145.00,
        "stock_quantity": 15,
    },
    {
        "name": "Rear Windshield - Honda Civic 2019-2023",
        "description": "Tempered rear glass with defroster grid for Honda Civic sedan.",
        "category": "Windshield",
        "car_make": "Honda",
        "car_model": "Civic",
        "car_year_start": 2019,
        "car_year_end": 2023,
        "part_number": "WS-HCIV-R2023",
        "price": 199.99,
        "cost": 100.00,
        "stock_quantity": 8,
    },
    {
        "name": "Driver Front Window - Ford F-150 2018-2023",
        "description": "Tempered driver-side front window. Power window compatible with anti-pinch technology.",
        "category": "Side Window",
        "car_make": "Ford",
        "car_model": "F-150",
        "car_year_start": 2018,
        "car_year_end": 2023,
        "part_number": "SW-FF150-DF",
        "price": 149.99,
        "cost": 75.00,
        "stock_quantity": 22,
    },
    {
        "name": "Passenger Front Window - Ford F-150 2018-2023",
        "description": "Tempered passenger-side front window for Ford F-150.",
        "category": "Side Window",
        "car_make": "Ford",
        "car_model": "F-150",
        "car_year_start": 2018,
        "car_year_end": 2023,
        "part_number": "SW-FF150-PF",
        "price": 149.99,
        "cost": 75.00,
        "stock_quantity": 18,
    },
    {
        "name": "Front Windshield - Chevrolet Silverado 2019-2024",
        "description": "OEM laminated front windshield for Chevy Silverado 1500/2500/3500.",
        "category": "Windshield",
        "car_make": "Chevrolet",
        "car_model": "Silverado",
        "car_year_start": 2019,
        "car_year_end": 2024,
        "part_number": "WS-CSIL-2024",
        "price": 319.99,
        "cost": 160.00,
        "stock_quantity": 10,
    },
    {
        "name": "Quarter Glass - Chevrolet Suburban 2021+",
        "description": "Fixed quarter glass panel for rear side windows. OEM-spec tinted tempered glass.",
        "category": "Quarter Glass",
        "car_make": "Chevrolet",
        "car_model": "Suburban",
        "car_year_start": 2021,
        "car_year_end": 2025,
        "part_number": "QG-CSUB-2021",
        "price": 89.99,
        "cost": 45.00,
        "stock_quantity": 18,
    },
    {
        "name": "Rear Windshield - Tesla Model 3 2017-2024",
        "description": "Tempered rear glass for Tesla Model 3. Includes defroster elements.",
        "category": "Windshield",
        "car_make": "Tesla",
        "car_model": "Model 3",
        "car_year_start": 2017,
        "car_year_end": 2024,
        "part_number": "WS-TM3-R24",
        "price": 399.99,
        "cost": 200.00,
        "stock_quantity": 6,
    },
    {
        "name": "Panoramic Sunroof Glass - Tesla Model Y 2020-2024",
        "description": "Full panoramic sunroof replacement glass for Tesla Model Y.",
        "category": "Sunroof",
        "car_make": "Tesla",
        "car_model": "Model Y",
        "car_year_start": 2020,
        "car_year_end": 2024,
        "part_number": "SR-TMY-PAN24",
        "price": 599.99,
        "cost": 300.00,
        "stock_quantity": 4,
    },
    {
        "name": "Front Windshield - Honda Accord 2018-2022",
        "description": "Laminated front windshield with rain sensor bracket area.",
        "category": "Windshield",
        "car_make": "Honda",
        "car_model": "Accord",
        "car_year_start": 2018,
        "car_year_end": 2022,
        "part_number": "WS-HACC-2022",
        "price": 259.99,
        "cost": 130.00,
        "stock_quantity": 12,
    },
    {
        "name": "Rear Window - Jeep Wrangler 2018-2024",
        "description": "Tempered rear window glass for Jeep Wrangler JL. Heated.",
        "category": "Rear Window",
        "car_make": "Jeep",
        "car_model": "Wrangler",
        "car_year_start": 2018,
        "car_year_end": 2024,
        "part_number": "RW-JWRN-2024",
        "price": 179.99,
        "cost": 90.00,
        "stock_quantity": 9,
    },
    {
        "name": "Windshield Repair Kit - Professional",
        "description": "Complete windshield chip repair kit. Includes resin, injector, curing strips, and UV light.",
        "category": "Accessories",
        "car_make": "",
        "car_model": "",
        "part_number": "ACC-REPAIR-PRO",
        "price": 34.99,
        "cost": 15.00,
        "stock_quantity": 40,
    },
    {
        "name": "Glass Suction Cup Lifter - Triple Cup",
        "description": "Heavy-duty triple suction cup glass lifter. Rated for up to 150 lbs.",
        "category": "Accessories",
        "car_make": "",
        "car_model": "",
        "part_number": "ACC-SUCTION-3",
        "price": 49.99,
        "cost": 22.00,
        "stock_quantity": 25,
    },
    {
        "name": "Safety Glass Film Roll - 60\" Wide",
        "description": "Clear safety glass film, 60 inches wide, per linear foot. ANSI Z97.1 certified.",
        "category": "Accessories",
        "car_make": "",
        "car_model": "",
        "part_number": "ACC-FILM-60",
        "price": 12.99,
        "cost": 5.00,
        "stock_quantity": 100,
    },
    {
        "name": "Front Windshield - BMW 3 Series 2019-2025",
        "description": "Laminated front windshield with HUD projection area for BMW 3 Series G20.",
        "category": "Windshield",
        "car_make": "BMW",
        "car_model": "3 Series",
        "car_year_start": 2019,
        "car_year_end": 2025,
        "part_number": "WS-BMW3-G20",
        "price": 449.99,
        "cost": 225.00,
        "stock_quantity": 5,
    },
    {
        "name": "Rear Quarter Glass - Toyota RAV4 2019-2024",
        "description": "Fixed rear quarter window glass for Toyota RAV4. Privacy tinted.",
        "category": "Quarter Glass",
        "car_make": "Toyota",
        "car_model": "RAV4",
        "car_year_start": 2019,
        "car_year_end": 2024,
        "part_number": "QG-TRAV4-2024",
        "price": 109.99,
        "cost": 55.00,
        "stock_quantity": 14,
    },
]


def seed():
    with app.app_context():
        print("Clearing existing data...")
        OrderItem.query.delete()
        Order.query.delete()
        ShipmentItem.query.delete()
        WholesaleShipment.query.delete()
        Product.query.delete()
        User.query.delete()
        db.session.commit()

        print("Creating users...")
        admin_user = User(
            username="admin",
            email="admin@winarisglass.com",
            full_name="Winaris Admin",
            phone="(403) 555-0100",
            address="Calgary, AB",
            role="admin",
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)

        customer_user = User(
            username="customer",
            email="customer@example.com",
            full_name="Mike Johnson",
            phone="(403) 555-6543",
            address="456 Oak Ave, Calgary, AB T2P 1A1",
            role="customer",
        )
        customer_user.set_password("customer123")
        db.session.add(customer_user)
        db.session.flush()
        print("  Admin  -> username: admin      password: admin123")
        print("  User   -> username: customer   password: customer123")

        print("Creating products...")
        products = []
        for pdata in PRODUCTS:
            p = Product(**pdata)
            db.session.add(p)
            products.append(p)
        db.session.flush()

        print(f"Created {len(products)} products.")

        shipment = WholesaleShipment(
            supplier="Pacific Glass Distributors",
            invoice_number="PGD-2024-0312",
            total_cost=2450.00,
            status="RECEIVED",
            notes="March 2024 restock order",
        )
        db.session.add(shipment)
        db.session.flush()

        for i, (qty, cost) in enumerate([(10, 145.00), (5, 100.00), (10, 75.00)]):
            si = ShipmentItem(
                shipment_id=shipment.id,
                product_id=products[i].id,
                quantity=qty,
                unit_cost=cost,
            )
            db.session.add(si)

        print(f"Created shipment: {shipment.invoice_number}")

        order = Order(
            customer_name="Mike Johnson",
            customer_email="mike.johnson@email.com",
            customer_phone="(555) 987-6543",
            customer_address="456 Oak Ave, Springfield, IL 62704",
            total_amount=579.97,
            status="PENDING",
            notes="Need installation by Friday if possible.",
        )
        db.session.add(order)
        db.session.flush()

        for pid, qty, price in [(0, 1, 289.99), (5, 1, 89.99), (2, 1, 149.99)]:
            oi = OrderItem(
                order_id=order.id,
                product_id=products[pid].id,
                quantity=qty,
                price=price,
            )
            db.session.add(oi)

        print(f"Created order from {order.customer_name}")

        db.session.commit()
        print("\nSeed complete!")


if __name__ == "__main__":
    seed()
