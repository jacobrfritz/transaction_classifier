import logging
import os
import random
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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker

# Database connection configuration
DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://admin:password@localhost:5432/transactions_db"
)

logger = logging.getLogger(__name__)

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
    Searches for the 5 nearest verified neighbors using cosine distance.
    Uses distance-weighted voting to determine the best category.
    Returns (predicted_category, average_confidence)
    """
    session = SessionLocal()
    try:
        query = text("""
            SELECT actual_category,
                   (1 - (embedding <=> CAST(:val AS vector))) as confidence
            FROM transactions
            WHERE status = 'verified'
            ORDER BY embedding <=> CAST(:val AS vector)
            LIMIT 5;
        """)
        results = session.execute(query, {"val": embedding_vector}).fetchall()

        if not results:
            # Fallback: if no verified transactions, assign a random category
            categories = get_all_categories()
            if categories:
                return random.choice(categories), 0.0
            return None, 0.0

        # Weighted voting
        category_scores = {}
        category_counts = {}
        for cat, conf in results:
            category_scores[cat] = category_scores.get(cat, 0.0) + float(conf)
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Select category with the highest total confidence score
        winner = max(category_scores, key=category_scores.get)
        avg_confidence = category_scores[winner] / category_counts[winner]

        return winner, avg_confidence
    finally:
        session.close()


def get_pending_transactions():
    session = SessionLocal()
    try:
        return session.query(Transaction).filter(Transaction.status == "pending").all()
    finally:
        session.close()


def get_transactions(
    search: str = None,
    status: str = None,
    category: str = None,
    limit: int = 100,
    offset: int = 0,
):
    session = SessionLocal()
    try:
        query = session.query(Transaction)
        if search:
            query = query.filter(Transaction.raw_string.ilike(f"%{search}%"))
        if status:
            query = query.filter(Transaction.status == status)
        if category:
            query = query.filter(
                (Transaction.actual_category == category)
                | (
                    (Transaction.actual_category == None)
                    & (Transaction.predicted_category == category)
                )
            )

        total = query.count()
        results = (
            query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()
        )
        return results, total
    finally:
        session.close()


def get_all_transactions():
    session = SessionLocal()
    try:
        return session.query(Transaction).order_by(Transaction.date.desc()).all()
    finally:
        session.close()


def transaction_exists_by_description(raw_string: str) -> bool:
    """Checks if a transaction already exists in the database."""
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


def update_transactions_bulk(transaction_ids, actual_category):
    session = SessionLocal()
    try:
        session.query(Transaction).filter(Transaction.id.in_(transaction_ids)).update(
            {"actual_category": actual_category, "status": "verified"},
            synchronize_session=False,
        )
        session.commit()
        return True
    finally:
        session.close()


def get_category_stats():
    session = SessionLocal()
    try:
        category_col = func.coalesce(
            Transaction.actual_category, Transaction.predicted_category
        )
        results = (
            session.query(category_col, func.count(Transaction.id))
            .group_by(category_col)
            .all()
        )
        total = session.query(Transaction).count()
        return {
            "total": total,
            "breakdown": [
                {
                    "category": cat or "Unknown",
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0,
                }
                for cat, count in results
            ],
        }
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
            session.query(Transaction).filter(
                Transaction.actual_category == name
            ).update({"status": "pending"})
            session.delete(cat)
            session.commit()
            return True
        return False
    finally:
        session.close()
