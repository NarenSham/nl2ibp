from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# -------------------------
# Database setup
# -------------------------
DATABASE_URL = "sqlite:///db/optiguide.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# =========================
# Core Scenario
# =========================
class Scenario(Base):
    __tablename__ = "scenario"
    scenario_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # e.g., tpo, finance, supply
    created_at = Column(DateTime, default=datetime.utcnow)

    overrides = relationship("ScenarioOverride", back_populates="scenario", cascade="all, delete-orphan")
    tpo_promotions = relationship("ScenarioPromotion", back_populates="scenario", cascade="all, delete-orphan")
    finance_assumptions = relationship("FinanceAssumption", back_populates="scenario", cascade="all, delete-orphan")
    supply_assumptions = relationship("SupplyAssumption", back_populates="scenario", cascade="all, delete-orphan")

# -------------------------
# Generic scenario override
# -------------------------
class ScenarioOverride(Base):
    __tablename__ = "scenario_override"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario.scenario_id", ondelete="CASCADE"), nullable=False)
    table_name = Column(String, nullable=False)
    row_id = Column(Integer, nullable=False)
    column_name = Column(String, nullable=False)
    override_value = Column(Text, nullable=False)

    scenario = relationship("Scenario", back_populates="overrides")

# -------------------------
# TPO Promotion mapping
# -------------------------
class ScenarioPromotion(Base):
    __tablename__ = "scenario_promotion"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario.scenario_id", ondelete="CASCADE"), nullable=False)
    promotion_id = Column(Integer, ForeignKey("promotion.id", ondelete="CASCADE"), nullable=False)
    selected = Column(Boolean, default=False)

    scenario = relationship("Scenario", back_populates="tpo_promotions")
    promotion = relationship("Promotion", back_populates="scenarios")

# -------------------------
# Finance assumptions
# -------------------------
class FinanceAssumption(Base):
    __tablename__ = "finance_assumption"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario.scenario_id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)

    scenario = relationship("Scenario", back_populates="finance_assumptions")

# -------------------------
# Supply assumptions
# -------------------------
class SupplyAssumption(Base):
    __tablename__ = "supply_assumption"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario.scenario_id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)

    scenario = relationship("Scenario", back_populates="supply_assumptions")

# -------------------------
# Products
# -------------------------
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    brand = Column(String)
    sku = Column(String)
    category = Column(String)

    promotions = relationship("Promotion", back_populates="product")

# -------------------------
# Retailers
# -------------------------
class Retailer(Base):
    __tablename__ = "retailer"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    region = Column(String)

    promotions = relationship("Promotion", back_populates="retailer")

# -------------------------
# Promotions
# -------------------------
class Promotion(Base):
    __tablename__ = "promotion"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"))
    retailer_id = Column(Integer, ForeignKey("retailer.id", ondelete="CASCADE"))
    week = Column(Integer)
    discount_depth = Column(Float)
    tactic = Column(String)
    est_incremental_units = Column(Integer)
    est_incremental_revenue = Column(Float)
    est_incremental_profit = Column(Float)

    product = relationship("Product", back_populates="promotions")
    retailer = relationship("Retailer", back_populates="promotions")
    scenarios = relationship("ScenarioPromotion", back_populates="promotion")

# =========================
# Initialize DB helper
# =========================
def init_db():
    Base.metadata.create_all(bind=engine)
