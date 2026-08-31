from app import create_app, db
from app.models import (
    Product,
    Role,
    StockEntry,
    Store,
    StoreInventory,
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

    # Merchant (Unrestricted store access)
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

    print("Seeding product catalog...")
    products = [
        Product(
            name="Jogoo Maize Meal 2kg",
            description="Premium fortified white maize meal flour.",
            category="Groceries",
            buying_price=130.00,
            selling_price=160.00,
            image_url="https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500",
        ),
        Product(
            name="Fresh Fri Cooking Oil 2L",
            description="Pure vegetable cooking oil fortified with Vitamin A.",
            category="Groceries",
            buying_price=520.00,
            selling_price=600.00,
            image_url="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500",
        ),
        Product(
            name="KCC Fresh Milk 500ml",
            description="Pasteurized fresh whole cow milk.",
            category="Dairy",
            buying_price=55.00,
            selling_price=70.00,
            image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500",
        ),
        Product(
            name="Kericho Gold Black Tea 100 Bags",
            description="Premium blend black tea bags.",
            category="Beverages",
            buying_price=280.00,
            selling_price=350.00,
            image_url="https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500",
        ),
        Product(
            name="Mwea Pishori Rice 5kg",
            description="Aromatic pure long-grain grade 1 rice.",
            category="Groceries",
            buying_price=950.00,
            selling_price=1150.00,
            image_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500",
        ),
        Product(
            name="Supa Loaf White Bread 400g",
            description="Freshly baked sliced white bread.",
            category="Bakery",
            buying_price=55.00,
            selling_price=65.00,
            image_url="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
        ),
        Product(
            name="Omo Washing Powder 1kg",
            description="Fast action washing detergent powder.",
            category="Household",
            buying_price=310.00,
            selling_price=380.00,
            image_url="https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=500",
        ),
        Product(
            name="Keringet Still Mineral Water 1.5L",
            description="Natural mineral water from the Great Rift Valley.",
            category="Beverages",
            buying_price=70.00,
            selling_price=100.00,
            image_url="https://images.unsplash.com/photo-1560023907-5f339617ea30?w=500",
        ),
    ]

    db.session.add_all(products)
    db.session.commit()

    print("Seeding store inventories...")
    inventories = [
        # CBD Branch Inventory (Store 1)
        StoreInventory(store_id=store_1.id, product_id=products[0].id, stock_quantity=120, reorder_level=20),
        StoreInventory(store_id=store_1.id, product_id=products[1].id, stock_quantity=45, reorder_level=10),
        StoreInventory(store_id=store_1.id, product_id=products[2].id, stock_quantity=80, reorder_level=15),
        StoreInventory(store_id=store_1.id, product_id=products[3].id, stock_quantity=30, reorder_level=5),
        StoreInventory(store_id=store_1.id, product_id=products[4].id, stock_quantity=50, reorder_level=10),
        StoreInventory(store_id=store_1.id, product_id=products[5].id, stock_quantity=90, reorder_level=20),
        StoreInventory(store_id=store_1.id, product_id=products[6].id, stock_quantity=35, reorder_level=10),
        StoreInventory(store_id=store_1.id, product_id=products[7].id, stock_quantity=150, reorder_level=25),

        # Westlands Outlet Inventory (Store 2)
        StoreInventory(store_id=store_2.id, product_id=products[0].id, stock_quantity=15, reorder_level=20),
        StoreInventory(store_id=store_2.id, product_id=products[1].id, stock_quantity=60, reorder_level=10),
        StoreInventory(store_id=store_2.id, product_id=products[4].id, stock_quantity=40, reorder_level=10),
        StoreInventory(store_id=store_2.id, product_id=products[5].id, stock_quantity=100, reorder_level=25),

        # Kilimani Branch Inventory (Store 3)
        StoreInventory(store_id=store_3.id, product_id=products[6].id, stock_quantity=40, reorder_level=10),
        StoreInventory(store_id=store_3.id, product_id=products[7].id, stock_quantity=200, reorder_level=30),
    ]

    db.session.add_all(inventories)
    db.session.commit()

    print("Seeding stock delivery entries...")
    stock_entries = [
        StockEntry(store_id=store_1.id, product_id=products[0].id, quantity=50),
        StockEntry(store_id=store_1.id, product_id=products[1].id, quantity=20),
        StockEntry(store_id=store_1.id, product_id=products[2].id, quantity=40),
        StockEntry(store_id=store_2.id, product_id=products[5].id, quantity=60),
    ]

    db.session.add_all(stock_entries)
    db.session.commit()

    print("Seeding supply requests...")
    requests = [
        SupplyRequest(
            store_id=store_1.id,
            product_id=products[3].id,  # Kericho Gold Tea
            clerk_id=clerk_cbd.id,
            requested_quantity=30,
            status=SupplyRequestStatus.PENDING.value,
        ),
        SupplyRequest(
            store_id=store_2.id,
            product_id=products[0].id,  # Jogoo Maize Meal
            clerk_id=clerk_westlands.id,
            requested_quantity=50,
            status=SupplyRequestStatus.PENDING.value,
        ),
        SupplyRequest(
            store_id=store_1.id,
            product_id=products[1].id,  # Fresh Fri Oil
            clerk_id=clerk_cbd.id,
            requested_quantity=20,
            status=SupplyRequestStatus.APPROVED.value,
        ),
    ]

    db.session.add_all(requests)
    db.session.commit()

    print("Database successfully seeded with stores, users, inventory, and entries!")