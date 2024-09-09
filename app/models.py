from app import db
from datetime import datetime

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupplierAgreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)
    supplier_id = db.Column(db.Integer, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    contract_start = db.Column(db.Date, nullable=False)
    contract_end = db.Column(db.Date, nullable=False)
    rebate_type = db.Column(db.String(50), nullable=False)
    rebate_condition = db.Column(db.String(200), nullable=False)
    product_category = db.Column(db.String(100), nullable=False)
    tier_1_threshold = db.Column(db.Float, nullable=True)
    tier_1_percentage = db.Column(db.Float, nullable=True)
    tier_2_threshold = db.Column(db.Float, nullable=True)
    tier_2_percentage = db.Column(db.Float, nullable=True)
    tier_3_threshold = db.Column(db.Float, nullable=True)
    tier_3_percentage = db.Column(db.Float, nullable=True)
    growth_target_percentage = db.Column(db.Float, nullable=True)
    mix_target_percentage = db.Column(db.Float, nullable=True)
    retention_period = db.Column(db.Integer, nullable=True)
    flat_percentage = db.Column(db.Float, nullable=True)
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('session.session_id'), nullable=False)
    transaction_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    supplier_id = db.Column(db.Integer, nullable=False)
    product_sku = db.Column(db.String(50), nullable=False)
    product_category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class ClaimedRebate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('session.session_id'), nullable=False)
    claim_id = db.Column(db.Integer, nullable=False)
    supplier_id = db.Column(db.Integer, nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    amount_claimed = db.Column(db.Float, nullable=False)
    date_claimed = db.Column(db.Date, nullable=False)

class HistoricalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('session.session_id'), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)