from app import create_app, db
from app.models import (
    PaymentStatus,
    Product,
    Role,
    StockEntry,
    Store,
    SupplyRequest,
    SupplyRequestStatus,
    User,
)

app = create_app()

with app.app_context():
    print("Clearing existing data...")
    db.drop_all()
    db.create_all()

    print("Seeding stores...")
    store_1 = Store(name="CBD Main Branch", location="Moi Avenue, Nairobi")
    store_2 = Store(name="Westlands Outlet", location="Woodvale Grove, Nairobi")
    store_3 = Store(name="Kilimani Branch", location="Argwings Kodhek, Nairobi")

    db.session.add_all([store_1, store_2, store_3])
    db.session.commit()

    print("Seeding users...")
    # Clerk assigned to CBD Branch (Store 1)
    clerk_cbd = User(
        email="clerk@myduka.com",
        username="clerk_cbd",
        full_name="Jane Wambui",
        role=Role.CLERK,
        store_id=store_1.id,
        is_active=True,
    )
    clerk_cbd.set_password("Password123!")

    # Clerk assigned to Westlands Outlet (Store 2)
    clerk_westlands = User(
        email="clerk2@myduka.com",
        username="clerk_westlands",
        full_name="Peter Otieno",
        role=Role.CLERK,
        store_id=store_2.id,
        is_active=True,
    )
    clerk_westlands.set_password("Password123!")

    # Merchant (unrestricted store access)
    merchant = User(
        email="merchant@myduka.com",
        username="merchant_boss",
        full_name="Andrew Macharia",
        role=Role.MERCHANT,
        store_id=None,
        is_active=True,
    )
    merchant.set_password("Password123!")

    # Admin assigned to Store 1
    admin = User(
        email="admin@myduka.com",
        username="admin_user",
        full_name="System Admin",
        role=Role.ADMIN,
        store_id=store_1.id,
        is_active=True,
    )
    admin.set_password("Password123!")

    db.session.add_all([clerk_cbd, clerk_westlands, merchant, admin])
    db.session.commit()

    print("Seeding products per store...")
    # Catalog: (name, category, buy_price, sell_price, image_url)
    catalog = [
        ("Jogoo Maize Meal 2kg", "Groceries", 130.00, 160.00,
         "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500"),
        ("Fresh Fri Cooking Oil 2L", "Groceries", 520.00, 600.00,
         "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500"),
        ("KCC Fresh Milk 500ml", "Dairy", 55.00, 70.00,
         "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500"),
        ("Kericho Gold Black Tea 100 Bags", "Beverages", 280.00, 350.00,
         "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500"),
        ("Mwea Pishori Rice 5kg", "Groceries", 950.00, 1150.00,
         "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500"),
        ("Supa Loaf White Bread 400g", "Bakery", 55.00, 65.00,
         "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"),
        ("Omo Washing Powder 1kg", "Household", 310.00, 380.00,
         "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=500"),
        ("Keringet Still Mineral Water 1.5L", "Beverages", 70.00, 100.00,
         "https://images.unsplash.com/photo-1560023907-5f339617ea30?w=500"),
    ]

    # Per-store stock quantities. A store only carries a product if it's
    # listed here (mirrors which items were previously in that store's
    # inventory).
    store_stock = {
        store_1.id: {0: 120, 1: 45, 2: 80, 3: 30, 4: 50, 5: 90, 6: 35, 7: 150},
        store_2.id: {0: 15, 1: 60, 4: 40, 5: 100},
        store_3.id: {6: 40, 7: 200},
    }

    # products[store_id][catalog_index] -> Product
    products = {}
    for store_id, stock_by_index in store_stock.items():
        products[store_id] = {}
        for idx, qty in stock_by_index.items():
            name, category, buy_price, sell_price, image_url = catalog[idx]
            product = Product(
                name=name,
                category=category,
                store_id=store_id,
                buy_price=buy_price,
                sell_price=sell_price,
                quantity_in_stock=qty,
                image_url=image_url,
                is_active=True,
            )
            db.session.add(product)
            products[store_id][idx] = product

    db.session.commit()

    print("Seeding stock delivery entries...")
    stock_entries = [
        StockEntry(
            store_id=store_1.id,
            product_id=products[store_1.id][0].id,
            clerk_id=clerk_cbd.id,
            quantity_received=50,
            stock_quantity=120,
            spoilt_quantity=0,
            buy_price=130.00,
            sell_price=160.00,
            payment_status=PaymentStatus.PAID,
        ),
        StockEntry(
            store_id=store_1.id,
            product_id=products[store_1.id][1].id,
            clerk_id=clerk_cbd.id,
            quantity_received=20,
            stock_quantity=45,
            spoilt_quantity=1,
            buy_price=520.00,
            sell_price=600.00,
            payment_status=PaymentStatus.NOT_PAID,
        ),
        StockEntry(
            store_id=store_1.id,
            product_id=products[store_1.id][2].id,
            clerk_id=clerk_cbd.id,
            quantity_received=40,
            stock_quantity=80,
            spoilt_quantity=0,
            buy_price=55.00,
            sell_price=70.00,
            payment_status=PaymentStatus.PAID,
        ),
        StockEntry(
            store_id=store_2.id,
            product_id=products[store_2.id][5].id,
            clerk_id=clerk_westlands.id,
            quantity_received=60,
            stock_quantity=100,
            spoilt_quantity=2,
            buy_price=310.00,
            sell_price=380.00,
            payment_status=PaymentStatus.NOT_PAID,
        ),
    ]

    db.session.add_all(stock_entries)
    db.session.commit()

    print("Seeding supply requests...")
    requests = [
        SupplyRequest(
            store_id=store_1.id,
            product_id=products[store_1.id][3].id,  # Kericho Gold Tea
            clerk_id=clerk_cbd.id,
            quantity_requested=30,
            status=SupplyRequestStatus.PENDING,
        ),
        SupplyRequest(
            store_id=store_2.id,
            product_id=products[store_2.id][0].id,  # Jogoo Maize Meal
            clerk_id=clerk_westlands.id,
            quantity_requested=50,
            status=SupplyRequestStatus.PENDING,
        ),
        SupplyRequest(
            store_id=store_1.id,
            product_id=products[store_1.id][1].id,  # Fresh Fri Oil
            clerk_id=clerk_cbd.id,
            quantity_requested=20,
            status=SupplyRequestStatus.APPROVED,
            reviewed_by_id=admin.id,
        ),
    ]

    db.session.add_all(requests)
    db.session.commit()

    print("Database successfully seeded with stores, users, products, stock entries, and supply requests!")