from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

# Create tables
models.Base.metadata.create_all(bind=engine)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ SCHEMA ------------------

class BankBase(BaseModel):
    name: str
    balance: float


class Transaction(BaseModel):
    amount: float

# ------------------ DATABASE ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# ------------------ ROUTES ------------------

@app.get("/")
async def root():
    return {"message": "Bank API is running. Visit /docs to test endpoints."}

# CREATE ACCOUNT
@app.post("/accounts/")
async def create_account(account: BankBase, db: db_dependency):
    db_account = models.Bank(
        name=account.name,
        balance=account.balance
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account

# READ ALL ACCOUNTS
@app.get("/accounts/")
async def read_all_accounts(db: db_dependency):
    return db.query(models.Bank).all()

# READ ONE ACCOUNT
@app.get("/accounts/{account_id}")
async def read_account(account_id: int, db: db_dependency):
    account = db.query(models.Bank).filter(models.Bank.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account

# UPDATE ACCOUNT
@app.put("/accounts/{account_id}")
async def update_account(account_id: int, updated_account: BankBase, db: db_dependency):
    db_account = db.query(models.Bank).filter(models.Bank.id == account_id).first()

    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    db_account.name = updated_account.name
    db_account.balance = updated_account.balance

    db.commit()
    db.refresh(db_account)

    return {
        "message": "Account updated successfully",
        "account": db_account
    }

# DELETE ACCOUNT
@app.delete("/accounts/{account_id}")
async def delete_account(account_id: int, db: db_dependency):
    db_account = db.query(models.Bank).filter(models.Bank.id == account_id).first()

    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(db_account)
    db.commit()

    return {"message": f"Account ID {account_id} has been deleted"}

# ------------------ DEPOSIT ------------------

@app.put("/accounts/{account_id}/deposit")
async def deposit_money(
    account_id: int,
    transaction: Transaction,
    db: db_dependency
):
    account = db.query(models.Bank).filter(models.Bank.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit must be > 0")

    account.balance = float(account.balance) + transaction.amount

    db.commit()
    db.refresh(account)

    return {
        "message": "Deposit successful",
        "balance": account.balance
    }


# ------------------ WITHDRAW ------------------

@app.put("/accounts/{account_id}/withdraw")
async def withdraw_money(
    account_id: int,
    transaction: Transaction,
    db: db_dependency
):
    account = db.query(models.Bank).filter(models.Bank.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Withdraw must be > 0")

    if account.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    account.balance = float(account.balance) - transaction.amount

    db.commit()
    db.refresh(account)

    return {
        "message": "Withdraw successful",
        "balance": account.balance
    }