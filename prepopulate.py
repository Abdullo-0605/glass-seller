"""Prepopulate the database with comprehensive car makes, models, and year ranges
for the Glass Finder. All products start as out-of-stock with $0 price.
When files are uploaded, they get mapped to these entries and stock/price updated.
"""
from app.create_app import create_app
from app.models import db, Product

app = create_app()

# Comprehensive vehicle catalog: {Make: {Model: (year_start, year_end)}}
VEHICLES = {
    # --- CLASSICS (1950s-1980s) ---
    "AMC": {
        "Javelin": (1968, 1974), "Gremlin": (1970, 1978), "Pacer": (1975, 1980),
        "Hornet": (1970, 1977), "Eagle": (1980, 1988),
    },
    "Buick": {
        "Skylark": (1953, 1972), "Riviera": (1963, 1999), "Electra": (1959, 1990),
        "LeSabre": (1959, 2005), "Century": (1954, 2005), "Regal": (1973, 2020),
        "Roadmaster": (1991, 1996), "Park Avenue": (1991, 2005),
        "Enclave": (2008, 2026), "Encore": (2013, 2026), "Encore GX": (2020, 2026),
        "Envision": (2016, 2026), "LaCrosse": (2005, 2019),
    },
    "Cadillac": {
        "DeVille": (1959, 2005), "Eldorado": (1953, 2002), "Fleetwood": (1961, 1996),
        "Seville": (1975, 2004), "CTS": (2003, 2019),
        "CT4": (2020, 2026), "CT5": (2020, 2026), "Escalade": (1999, 2026),
        "XT4": (2019, 2026), "XT5": (2017, 2026), "XT6": (2020, 2026),
    },
    "Chevrolet": {
        "Bel Air": (1950, 1975), "Impala": (1958, 2020), "Nova": (1962, 1979),
        "Chevelle": (1964, 1977), "Camaro": (1967, 2024), "Monte Carlo": (1970, 2007),
        "El Camino": (1959, 1987), "Corvette": (1953, 2026), "Caprice": (1965, 1996),
        "C/K Pickup": (1960, 1999), "S-10": (1982, 2004), "Blazer": (1969, 2026),
        "Suburban": (1960, 2026), "Tahoe": (1995, 2026), "Malibu": (1964, 2024),
        "Colorado": (2004, 2026), "Equinox": (2005, 2026), "Traverse": (2009, 2026),
        "Silverado 1500": (1999, 2026), "Silverado 2500": (1999, 2026),
        "Silverado 3500": (1999, 2026), "Cruze": (2011, 2019),
        "Trailblazer": (2002, 2026), "Trax": (2015, 2026),
    },
    "Chrysler": {
        "Imperial": (1955, 1975), "New Yorker": (1950, 1996), "Newport": (1961, 1981),
        "Cordoba": (1975, 1983), "LeBaron": (1977, 1995), "Fifth Avenue": (1982, 1989),
        "PT Cruiser": (2001, 2010), "Sebring": (1995, 2010),
        "200": (2011, 2017), "300": (2005, 2026), "Pacifica": (2017, 2026),
        "Town & Country": (1990, 2016), "Voyager": (2020, 2023),
    },
    "Dodge": {
        "Coronet": (1950, 1976), "Dart": (1960, 2016), "Charger": (1966, 2026),
        "Challenger": (1970, 2026), "Polara": (1960, 1973), "Monaco": (1965, 1978),
        "Diplomat": (1977, 1989), "Aries": (1981, 1989), "Omni": (1978, 1990),
        "Ram 1500": (1981, 2026), "Ram 2500": (1981, 2026), "Ram 3500": (1981, 2026),
        "Dakota": (1987, 2011), "Durango": (1998, 2026), "Grand Caravan": (1984, 2020),
        "Journey": (2009, 2020), "Hornet": (2023, 2026),
    },
    "Ford": {
        "Fairlane": (1955, 1970), "Galaxie": (1959, 1974), "Falcon": (1960, 1970),
        "Mustang": (1964, 2026), "Thunderbird": (1955, 2005), "LTD": (1965, 1986),
        "Pinto": (1971, 1980), "Maverick": (1970, 2026), "Granada": (1975, 1982),
        "Bronco": (1966, 2026), "Bronco Sport": (2021, 2026),
        "F-100": (1953, 1983), "F-150": (1975, 2026), "F-250": (1953, 2026), "F-350": (1953, 2026),
        "Ranger": (1983, 2026), "Explorer": (1991, 2026), "Expedition": (1997, 2026),
        "Escape": (2001, 2026), "Edge": (2007, 2024), "Fusion": (2006, 2020),
        "Focus": (2000, 2018), "Taurus": (1986, 2019), "Fiesta": (1978, 2019),
        "Transit": (2015, 2026), "Transit Connect": (2010, 2023), "EcoSport": (2018, 2022),
        "Flex": (2009, 2019),
    },
    # --- IMPORTS (classics + modern) ---
    "Acura": {
        "Integra": (1986, 2026), "Legend": (1986, 1995), "NSX": (1991, 2022),
        "TL": (1996, 2014), "TSX": (2004, 2014), "ILX": (2013, 2022),
        "MDX": (2001, 2026), "RDX": (2007, 2026), "TLX": (2015, 2026),
    },
    "Audi": {
        "100": (1970, 1994), "4000": (1980, 1987), "5000": (1978, 1988),
        "A3": (1996, 2026), "A4": (1996, 2026), "A5": (2008, 2026), "A6": (1995, 2026),
        "A7": (2012, 2026), "A8": (1997, 2026), "Q3": (2015, 2026), "Q5": (2009, 2026),
        "Q7": (2007, 2026), "Q8": (2019, 2026), "e-tron": (2019, 2026),
    },
    "BMW": {
        "2002": (1968, 1976), "3 Series": (1975, 2026), "5 Series": (1972, 2026),
        "6 Series": (1976, 2026), "7 Series": (1977, 2026),
        "2 Series": (2014, 2026), "4 Series": (2014, 2026),
        "X1": (2013, 2026), "X3": (2004, 2026), "X5": (2000, 2026),
        "X6": (2008, 2026), "X7": (2019, 2026),
    },
    "Datsun": {
        "240Z": (1970, 1973), "260Z": (1974, 1978), "280Z": (1975, 1978),
        "280ZX": (1979, 1983), "510": (1968, 1973), "620 Pickup": (1972, 1979),
    },
    "Genesis": {
        "G70": (2019, 2026), "G80": (2017, 2026), "G90": (2017, 2026),
        "GV70": (2022, 2026), "GV80": (2021, 2026),
    },
    "GMC": {
        "C/K Pickup": (1960, 1999), "Jimmy": (1970, 2001), "S-15": (1982, 1990),
        "Sonoma": (1991, 2004), "Envoy": (1998, 2009),
        "Acadia": (2007, 2026), "Canyon": (2004, 2026), "Terrain": (2010, 2026),
        "Sierra 1500": (1999, 2026), "Sierra 2500": (1999, 2026), "Sierra 3500": (1999, 2026),
        "Yukon": (1992, 2026), "Yukon XL": (2000, 2026),
    },
    "Honda": {
        "Civic": (1973, 2026), "Accord": (1976, 2026), "Prelude": (1979, 2001),
        "CRX": (1984, 1991), "CR-V": (1997, 2026), "Odyssey": (1995, 2026),
        "Element": (2003, 2011), "Fit": (2007, 2020), "HR-V": (2016, 2026),
        "Insight": (2000, 2022), "Passport": (1994, 2026), "Pilot": (2003, 2026),
        "Ridgeline": (2006, 2026), "S2000": (1999, 2009),
    },
    "Hyundai": {
        "Excel": (1986, 1994), "Accent": (1995, 2022), "Elantra": (1992, 2026),
        "Sonata": (1989, 2026), "Santa Fe": (2001, 2026), "Tucson": (2005, 2026),
        "Kona": (2018, 2026), "Palisade": (2020, 2026), "Santa Cruz": (2022, 2026),
        "Ioniq 5": (2022, 2026), "Venue": (2020, 2026), "Veloster": (2012, 2021),
    },
    "Infiniti": {
        "G20": (1991, 2002), "G35": (2003, 2007), "G37": (2008, 2013),
        "Q50": (2014, 2026), "Q60": (2017, 2022), "QX50": (2019, 2026),
        "QX55": (2022, 2026), "QX60": (2013, 2026), "QX80": (2011, 2026),
    },
    "Isuzu": {
        "Trooper": (1984, 2002), "Rodeo": (1991, 2004), "Hombre": (1996, 2000),
    },
    "Jaguar": {
        "XJ": (1968, 2019), "XJS": (1975, 1996), "XK": (1996, 2014),
        "E-Type": (1961, 1975), "F-Type": (2014, 2024),
    },
    "Jeep": {
        "CJ": (1955, 1986), "Wrangler": (1987, 2026), "Cherokee": (1974, 2026),
        "Grand Cherokee": (1993, 2026), "Grand Cherokee L": (2021, 2026),
        "Compass": (2007, 2026), "Gladiator": (2020, 2026),
        "Renegade": (2015, 2026), "Wagoneer": (1963, 2026),
    },
    "Kia": {
        "Sephia": (1994, 2001), "Spectra": (2000, 2009), "Optima": (2001, 2020),
        "Forte": (2010, 2026), "K5": (2021, 2026), "Sorento": (2003, 2026),
        "Sportage": (1995, 2026), "Soul": (2010, 2026), "Telluride": (2020, 2026),
        "Seltos": (2021, 2026), "Niro": (2017, 2026), "EV6": (2022, 2026),
        "Rio": (2001, 2023), "Stinger": (2018, 2023),
    },
    "Land Rover": {
        "Range Rover": (1970, 2026), "Discovery": (1989, 2026), "Defender": (1983, 2026),
        "Range Rover Sport": (2005, 2026), "Freelander": (1997, 2014),
    },
    "Lexus": {
        "ES": (1990, 2026), "GS": (1993, 2020), "IS": (2001, 2026), "LS": (1990, 2026),
        "GX": (2003, 2026), "LX": (1996, 2026), "NX": (2015, 2026),
        "RX": (1999, 2026), "TX": (2024, 2026), "UX": (2019, 2026),
    },
    "Lincoln": {
        "Continental": (1961, 2020), "Town Car": (1981, 2011), "Mark Series": (1956, 1998),
        "Aviator": (2003, 2026), "Corsair": (2020, 2026), "MKC": (2015, 2019),
        "MKZ": (2006, 2020), "Nautilus": (2019, 2026), "Navigator": (1998, 2026),
    },
    "Mazda": {
        "RX-7": (1979, 2002), "RX-8": (2004, 2012), "626": (1979, 2002),
        "MX-5 Miata": (1990, 2026), "Mazda3": (2004, 2026), "Mazda6": (2003, 2021),
        "CX-5": (2013, 2026), "CX-9": (2007, 2023), "CX-30": (2020, 2026),
        "CX-50": (2023, 2026), "CX-90": (2024, 2026),
        "B-Series Pickup": (1972, 2009),
    },
    "Mercedes-Benz": {
        "190": (1959, 1993), "220": (1951, 1973), "230": (1965, 1993),
        "240D": (1974, 1983), "280": (1968, 1981), "300": (1951, 1989),
        "450SL": (1972, 1980), "560SL": (1986, 1989),
        "C-Class": (1994, 2026), "E-Class": (1994, 2026), "S-Class": (1972, 2026),
        "CLA": (2014, 2026), "A-Class": (2019, 2022),
        "GLA": (2015, 2026), "GLB": (2020, 2026), "GLC": (2016, 2026),
        "GLE": (1998, 2026), "GLS": (2017, 2026),
    },
    "Mercury": {
        "Cougar": (1967, 2002), "Grand Marquis": (1975, 2011), "Mountaineer": (1997, 2010),
        "Sable": (1986, 2009), "Villager": (1993, 2002),
    },
    "Mitsubishi": {
        "Eclipse": (1990, 2012), "3000GT": (1991, 1999), "Lancer": (2002, 2017),
        "Galant": (1989, 2012), "Montero": (1983, 2006),
        "Eclipse Cross": (2018, 2026), "Mirage": (1978, 2026), "Outlander": (2003, 2026),
        "Outlander Sport": (2011, 2023),
    },
    "Nissan": {
        "240SX": (1989, 1998), "300ZX": (1984, 1996), "350Z": (2003, 2009),
        "370Z": (2009, 2020), "Stanza": (1982, 1992), "Maxima": (1981, 2023),
        "Altima": (1993, 2026), "Sentra": (1982, 2026), "Pathfinder": (1986, 2026),
        "Frontier": (1998, 2026), "Titan": (2004, 2026), "Armada": (2004, 2026),
        "Rogue": (2008, 2026), "Murano": (2003, 2026), "Kicks": (2018, 2026),
        "Leaf": (2011, 2024), "Versa": (2007, 2023), "Hardbody Pickup": (1986, 1997),
    },
    "Oldsmobile": {
        "Cutlass": (1961, 1999), "442": (1964, 1971), "Delta 88": (1965, 1999),
        "Toronado": (1966, 1992), "Alero": (1999, 2004), "Intrigue": (1998, 2002),
    },
    "Plymouth": {
        "Barracuda": (1964, 1974), "Road Runner": (1968, 1980), "Duster": (1970, 1976),
        "Fury": (1956, 1978), "Valiant": (1960, 1976), "Voyager": (1974, 2000),
        "Neon": (1995, 2001),
    },
    "Pontiac": {
        "GTO": (1964, 2006), "Firebird": (1967, 2002), "Trans Am": (1969, 2002),
        "Grand Prix": (1962, 2008), "Grand Am": (1973, 2005), "Bonneville": (1957, 2005),
        "Catalina": (1950, 1981), "LeMans": (1962, 1981), "Sunbird": (1976, 1994),
        "G6": (2005, 2010), "G8": (2008, 2009), "Vibe": (2003, 2010),
    },
    "Porsche": {
        "356": (1950, 1965), "911": (1964, 2026), "914": (1970, 1976),
        "924": (1977, 1988), "928": (1978, 1995), "944": (1982, 1991),
        "Boxster": (1997, 2026), "Cayenne": (2003, 2026), "Cayman": (2006, 2026),
        "Macan": (2015, 2026), "Panamera": (2010, 2026), "Taycan": (2020, 2026),
    },
    "Ram": {
        "1500": (2011, 2026), "2500": (2011, 2026), "3500": (2011, 2026),
        "ProMaster": (2014, 2026),
    },
    "Saab": {
        "900": (1979, 1998), "9-3": (1999, 2011), "9-5": (1999, 2011),
    },
    "Saturn": {
        "S-Series": (1991, 2002), "Ion": (2003, 2007), "Vue": (2002, 2010),
        "Outlook": (2007, 2010), "Astra": (2008, 2009),
    },
    "Subaru": {
        "Brat": (1978, 1987), "GL": (1972, 1989), "Legacy": (1990, 2026),
        "Impreza": (1993, 2026), "Outback": (2000, 2026), "Forester": (1998, 2026),
        "WRX": (2002, 2026), "BRZ": (2013, 2026), "Crosstrek": (2013, 2026),
        "Ascent": (2019, 2026), "Solterra": (2023, 2026),
    },
    "Suzuki": {
        "Samurai": (1986, 1995), "Sidekick": (1989, 1998), "Grand Vitara": (1999, 2013),
        "Swift": (1989, 2001),
    },
    "Tesla": {
        "Model S": (2012, 2026), "Model X": (2016, 2026), "Model 3": (2017, 2026),
        "Model Y": (2020, 2026), "Cybertruck": (2024, 2026),
    },
    "Toyota": {
        "Land Cruiser": (1958, 2026), "Corolla": (1966, 2026), "Camry": (1983, 2026),
        "Celica": (1971, 2005), "Supra": (1979, 2026), "MR2": (1985, 2005),
        "4Runner": (1984, 2026), "Pickup/Hilux": (1964, 1995), "Tacoma": (1995, 2026),
        "Tundra": (2000, 2026), "RAV4": (1996, 2026), "Highlander": (2001, 2026),
        "Sienna": (1998, 2026), "Sequoia": (2001, 2026), "Avalon": (1995, 2022),
        "Prius": (2001, 2026), "Venza": (2009, 2026), "Tercel": (1978, 1999),
        "Corolla Cross": (2022, 2026), "GR86": (2022, 2026), "GR Supra": (2020, 2026),
    },
    "Volkswagen": {
        "Beetle": (1950, 2019), "Bus/Van": (1950, 1979), "Karmann Ghia": (1955, 1974),
        "Golf": (1975, 2021), "GTI": (1983, 2026), "Jetta": (1980, 2026),
        "Passat": (1990, 2022), "Rabbit": (1975, 1984), "Scirocco": (1974, 1988),
        "Corrado": (1990, 1995), "Cabrio": (1995, 2002),
        "Atlas": (2018, 2026), "Atlas Cross Sport": (2020, 2026),
        "ID.4": (2021, 2026), "Taos": (2022, 2026), "Tiguan": (2009, 2026),
    },
    "Volvo": {
        "140": (1967, 1974), "240": (1975, 1993), "740": (1985, 1992),
        "850": (1993, 1997), "S40": (1995, 2012), "S60": (2001, 2026),
        "S70": (1997, 2000), "S80": (1999, 2016), "S90": (2017, 2026),
        "V60": (2015, 2026), "XC40": (2019, 2026), "XC60": (2010, 2026),
        "XC90": (2003, 2026),
    },
}

# Glass types to create for each vehicle
GLASS_TYPES = [
    ("Front Windshield", "Windshield"),
    ("Rear Windshield", "Windshield"),
    ("Driver Front Window", "Side Window"),
    ("Passenger Front Window", "Side Window"),
    ("Driver Rear Window", "Side Window"),
    ("Passenger Rear Window", "Side Window"),
    ("Driver Quarter Glass", "Quarter Glass"),
    ("Passenger Quarter Glass", "Quarter Glass"),
]


def prepopulate():
    with app.app_context():
        count_before = Product.query.count()
        print(f"Products before: {count_before}")

        created = 0
        skipped = 0

        for make, models in VEHICLES.items():
            for model, (yr_start, yr_end) in models.items():
                for glass_name, category in GLASS_TYPES:
                    name = f"{glass_name} - {make} {model} {yr_start}-{yr_end}"
                    # Check if exists already
                    exists = Product.query.filter(
                        db.func.lower(Product.car_make) == make.lower(),
                        db.func.lower(Product.car_model) == model.lower(),
                        db.func.lower(Product.name).contains(glass_name.lower()),
                    ).first()

                    if exists:
                        skipped += 1
                        continue

                    p = Product(
                        name=name,
                        category=category,
                        car_make=make,
                        car_model=model,
                        car_year_start=yr_start,
                        car_year_end=yr_end,
                        part_number="",
                        price=0.0,
                        cost=0.0,
                        stock_quantity=0,
                        description=f"{glass_name} for {make} {model} ({yr_start}-{yr_end})",
                    )
                    db.session.add(p)
                    created += 1

                    if created % 500 == 0:
                        db.session.flush()
                        print(f"  ...{created} created so far")

        db.session.commit()
        total = Product.query.count()
        print(f"\nDone! Created {created} new products, skipped {skipped} existing.")
        print(f"Total products in DB: {total}")


if __name__ == "__main__":
    prepopulate()
