import csv
import io
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request

from api import db, mapping, ml

app = FastAPI(title="Transaction Classifier API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"Request failed: {e}")
        raise

@app.get("/")
def read_root():
    return {"message": "Transaction Classifier API is running"}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CategoryBase(BaseModel):
    name: str


class BulkUpdate(BaseModel):
    ids: List[UUID]
    category: str


@app.on_event("startup")
def startup_event():
    try:
        db.init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/categories")
def list_categories():
    return db.get_all_categories()


@app.post("/api/categories")
def add_category(cat: CategoryBase):
    try:
        db.add_category(cat.name)
        return {"message": f"Category {cat.name} added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/categories/{old_name}")
def rename_category(old_name: str, new_cat: CategoryBase):
    if db.rename_category(old_name, new_cat.name):
        return {"message": f"Renamed {old_name} to {new_cat.name}"}
    raise HTTPException(status_code=404, detail="Category not found")


@app.delete("/api/categories/{name}")
def delete_category(name: str):
    if db.delete_category(name):
        return {"message": f"Deleted category {name}"}
    raise HTTPException(status_code=404, detail="Category not found")


@app.get("/api/transactions")
def get_transactions(
    search: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    offset = (page - 1) * limit
    transactions, total = db.get_transactions(
        search=search, status=status, category=category, limit=limit, offset=offset
    )
    return {
        "transactions": [
            {
                "id": t.id,
                "date": t.date,
                "amount": float(t.amount),
                "raw_string": t.raw_string,
                "predicted_category": t.predicted_category,
                "confidence_score": t.confidence_score,
                "actual_category": t.actual_category,
                "status": t.status,
            }
            for t in transactions
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@app.put("/api/transactions/bulk")
def bulk_update_transactions(update: BulkUpdate):
    if db.update_transactions_bulk(update.ids, update.category):
        return {"message": f"Updated {len(update.ids)} transactions"}
    raise HTTPException(status_code=400, detail="Failed to update transactions")


@app.get("/api/stats")
def get_stats():
    return db.get_category_stats()


@app.post("/api/upload")
async def upload_csv(
    file: UploadFile = File(...),
    date_col: Optional[str] = Form(None),
    amount_col: Optional[str] = Form(None),
    description_col: Optional[str] = Form(None),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    decoded = content.decode("utf-8")
    f = io.StringIO(decoded)
    reader = csv.DictReader(f)
    fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]

    if not fieldnames:
        raise HTTPException(status_code=400, detail="CSV has no headers")

    header_mapping = None
    if date_col and amount_col and description_col:
        header_mapping = {
            "date": date_col,
            "amount": amount_col,
            "description": description_col,
        }
        mapping.save_mapping(fieldnames, header_mapping)
    else:
        header_mapping = mapping.get_mapping_for_headers(fieldnames)

    if not header_mapping:
        print(f"Mapping required for headers: {fieldnames}")
        return {
            "status": "mapping_required",
            "headers": fieldnames,
            "message": "Column mapping required. Please use the CLI to map these headers first.",
        }

    print(f"Starting ingestion with mapping: {header_mapping}")
    added_count = 0
    skipped_count = 0

    for row in reader:
        row = {k.strip(): v for k, v in row.items()}
        raw_string = row.get(header_mapping["description"])
        if not raw_string:
            continue

        if db.transaction_exists_by_description(raw_string):
            skipped_count += 1
            continue

        print(f"Processing transaction: {raw_string[:50]}...")
        raw_date = row.get(header_mapping["date"])
        raw_amount = row.get(header_mapping["amount"])

        clean_string = ml.clean_text(raw_string)
        embedding = ml.get_embedding(clean_string)
        predicted_category, confidence = db.predict_category(embedding)

        date_obj = None
        if raw_date:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    date_obj = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue

        db.insert_transaction(
            date=date_obj,
            amount=float(raw_amount) if raw_amount else 0.0,
            raw_string=raw_string,
            clean_string=clean_string,
            predicted_category=predicted_category or "Unknown",
            confidence_score=confidence or 0.0,
            embedding=embedding,
        )
        added_count += 1

    print(f"Ingestion complete. Added: {added_count}, Skipped: {skipped_count}")
    return {
        "status": "success",
        "added": added_count,
        "skipped": skipped_count,
        "message": f"Added {added_count} new transactions, skipped {skipped_count} duplicates.",
    }


@app.get("/api/download")
def download_csv():
    transactions = db.get_all_transactions()
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "date",
            "amount",
            "description",
            "category",
            "confidence",
            "status",
        ],
    )
    writer.writeheader()
    for t in transactions:
        writer.writerow(
            {
                "date": t.date,
                "amount": t.amount,
                "description": t.raw_string,
                "category": t.actual_category or t.predicted_category,
                "confidence": t.confidence_score,
                "status": t.status,
            }
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_export.csv"},
    )
