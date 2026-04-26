import os
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Date,
    Float,
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


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date)
    amount = Column(Numeric(10, 2))
    raw_string = Column(String(255))
    clean_string = Column(String(255))
    predicted_category = Column(String(100))
    confidence_score = Column(Float)
    actual_category = Column(String(100))
    status = Column(String(20), default="pending")  # 'pending' or 'verified'
    embedding = Column(Vector(384))


def init_db():
    """Initializes the database: enables pgvector, creates tables, and indexes."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # Create HNSW index for cosine distance if it doesn't exist
    # SQLAlchemy doesn't natively support HNSW index creation in create_all for pgvector yet in a simple way
    # so we can use a raw SQL command for the index.
    with engine.connect() as conn:
        try:
            conn.execute(
                text(
                    "CREATE INDEX ON transactions USING hnsw (embedding vector_cosine_ops);"
                )
            )
            conn.commit()
        except Exception:
            # If index already exists, this might fail, which is fine for init
            pass


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
            SELECT actual_category, (1 - (embedding <=> CAST(:val AS vector))) as confidence
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
