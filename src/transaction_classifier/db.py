import os
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Numeric,
    String,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker

# Database connection configuration
DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://admin:password@localhost:5432/transactions_db"
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"
    name = Column(String(100), primary_key=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date)
    amount = Column(Numeric(10, 2))
    raw_string = Column(String(255))
    clean_string = Column(String(255))
    predicted_category = Column(String(100))
    confidence_score = Column(Float)
    actual_category = Column(
        String(100),
        ForeignKey("categories.name", onupdate="CASCADE", ondelete="SET NULL"),
    )
    status = Column(String(20), default="pending")  # 'pending' or 'verified'
    embedding = Column(Vector(384))


def init_db():
    """Initializes the database: enables pgvector, creates tables, and indexes."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # Seed default categories
    seed_categories()

    # Create HNSW index for cosine distance if it doesn't exist
    # SQLAlchemy doesn't natively support HNSW index creation in create_all
    # for pgvector yet in a simple way so we can use a raw SQL command for the index.
    with engine.connect() as conn:
        try:
            conn.execute(
                text(
                    "CREATE INDEX ON transactions "
                    "USING hnsw (embedding vector_cosine_ops);"
                )
            )
            conn.commit()
        except Exception:
            # If index already exists, this might fail, which is fine for init
            pass


def seed_categories():
    """Seeds default categories if the table is empty."""
    default_categories = [
        "Dining",
        "Groceries",
        "Transport",
        "Utilities",
        "Entertainment",
        "Shopping",
        "Income",
        "Transfer",
    ]
    session = SessionLocal()
    try:
        # Check if table is empty
        if session.query(Category).count() == 0:
            for cat_name in default_categories:
                session.add(Category(name=cat_name))
            session.commit()
    finally:
        session.close()


def insert_transaction(
    date,
    amount,
    raw_string,
    clean_string,
    predicted_category,
    confidence_score,
    embedding,
):
    session = SessionLocal()
    try:
        db_transaction = Transaction(
            date=date,
            amount=amount,
            raw_string=raw_string,
            clean_string=clean_string,
            predicted_category=predicted_category,
            confidence_score=confidence_score,
            embedding=embedding,
            status="pending",
        )
        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)
        return db_transaction
    finally:
        session.close()


def predict_category(embedding_vector):
    """
    Searches for the nearest verified neighbor using cosine distance.
    Returns (actual_category, confidence) or (None, 0.0)
    """
    session = SessionLocal()
    try:
        # Using raw SQL for the specific pgvector query as requested in spec
        # confidence = 1 - cosine_distance
        query = text("""
            SELECT actual_category,
                   (1 - (embedding <=> CAST(:val AS vector))) as confidence
            FROM transactions
            WHERE status = 'verified'
            ORDER BY embedding <=> CAST(:val AS vector)
            LIMIT 1;
        """)
        result = session.execute(query, {"val": embedding_vector}).fetchone()
        if result:
            return result[0], float(result[1])
        return None, 0.0
    finally:
        session.close()


def get_pending_transactions():
    session = SessionLocal()
    try:
        return session.query(Transaction).filter(Transaction.status == "pending").all()
    finally:
        session.close()


def transaction_exists_by_description(raw_string: str) -> bool:
    """
    Checks if a transaction with the same raw_string
    already exists in the database.
    """
    session = SessionLocal()
    try:
        return (
            session.query(Transaction)
            .filter(Transaction.raw_string == raw_string)
            .first()
            is not None
        )
    finally:
        session.close()


def update_transaction(transaction_id, actual_category):
    session = SessionLocal()
    try:
        db_transaction = (
            session.query(Transaction).filter(Transaction.id == transaction_id).first()
        )
        if db_transaction:
            db_transaction.actual_category = actual_category
            db_transaction.status = "verified"
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_all_categories():
    """Returns a sorted list of all category names."""
    session = SessionLocal()
    try:
        results = session.query(Category).order_by(Category.name).all()
        return [c.name for c in results]
    finally:
        session.close()


def add_category(name: str):
    """Adds a new category."""
    session = SessionLocal()
    try:
        new_cat = Category(name=name)
        session.add(new_cat)
        session.commit()
        return new_cat
    finally:
        session.close()


def rename_category(old_name: str, new_name: str):
    """Renames a category. Cascade handles the transactions."""
    session = SessionLocal()
    try:
        cat = session.query(Category).filter(Category.name == old_name).first()
        if cat:
            cat.name = new_name
            session.commit()
            return True
        return False
    finally:
        session.close()


def delete_category(name: str):
    """Deletes a category and resets affected transactions to pending."""
    session = SessionLocal()
    try:
        cat = session.query(Category).filter(Category.name == name).first()
        if cat:
            # Revert affected transactions to pending
            session.query(Transaction).filter(
                Transaction.actual_category == name
            ).update({"status": "pending"})
            session.delete(cat)
            session.commit()
            return True
        return False
    finally:
        session.close()
