# loader.py
from datetime import datetime
from models import (
    SessionLocal, Base, engine,
    Scenario, Product, Retailer, Promotion,
    ScenarioPromotion, FinanceAssumption, SupplyAssumption
)

# Initialize DB (create tables)
def init_db_schema():
    Base.metadata.drop_all(bind=engine)  # optional: reset DB
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema created/reset using SQLAlchemy.")

# -----------------------------
# Domain-specific loaders
# -----------------------------

def load_tpo_data(db):
    # Products
    products = [
        Product(brand="BrandA", sku="SKU123", category="Beverages"),
        Product(brand="BrandB", sku="SKU456", category="Snacks")
    ]
    db.add_all(products)
    db.commit()

    # Retailers
    retailers = [
        Retailer(name="Walmart", region="US"),
        Retailer(name="Costco", region="US")
    ]
    db.add_all(retailers)
    db.commit()

    # Promotions
    promotions = [
        Promotion(
            product_id=products[0].id,
            retailer_id=retailers[0].id,
            week=32,
            discount_depth=0.2,
            tactic="price_discount",
            est_incremental_units=1000,
            est_incremental_revenue=5000,
            est_incremental_profit=2000
        ),
        Promotion(
            product_id=products[1].id,
            retailer_id=retailers[1].id,
            week=40,
            discount_depth=0.15,
            tactic="feature",
            est_incremental_units=800,
            est_incremental_revenue=4000,
            est_incremental_profit=1500
        )
    ]
    db.add_all(promotions)
    db.commit()

    # Scenario
    scenario = Scenario(
        name="Baseline TPO",
        description="Test trade promotion optimization",
        type="tpo",
        created_at=datetime.utcnow()
    )
    db.add(scenario)
    db.commit()

    # Link promotions to scenario
    scenario_promos = [
        ScenarioPromotion(scenario_id=scenario.scenario_id, promotion_id=promotions[0].id, selected=True),
        ScenarioPromotion(scenario_id=scenario.scenario_id, promotion_id=promotions[1].id, selected=False)
    ]
    db.add_all(scenario_promos)
    db.commit()


def load_finance_data(db):
    scenario = Scenario(
        name="Annual Finance Plan",
        description="Finance planning AOP scenario",
        type="finance",
        created_at=datetime.utcnow()
    )
    db.add(scenario)
    db.commit()

    finance_assumptions = [
        FinanceAssumption(scenario_id=scenario.scenario_id, key="roi_target", value='{"value":0.12}'),
        FinanceAssumption(scenario_id=scenario.scenario_id, key="capex_limit", value='{"value":100000}')
    ]
    db.add_all(finance_assumptions)
    db.commit()


def load_supply_data(db):
    scenario = Scenario(
        name="Supply Stress Test",
        description="Service level stress test",
        type="supply",
        created_at=datetime.utcnow()
    )
    db.add(scenario)
    db.commit()

    supply_assumptions = [
        SupplyAssumption(scenario_id=scenario.scenario_id, key="capacity_limit", value='{"value":10000}'),
        SupplyAssumption(scenario_id=scenario.scenario_id, key="lead_time", value='{"days":14}')
    ]
    db.add_all(supply_assumptions)
    db.commit()


# -----------------------------
# Master loader
# -----------------------------
def init_db():
    init_db_schema()
    db = SessionLocal()

    try:
        load_tpo_data(db)
        load_finance_data(db)
        load_supply_data(db)
        print("✅ All domains loaded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
