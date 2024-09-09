import os
import pandas as pd
import logging
from app import db
from app.models import SupplierAgreement, Transaction, ClaimedRebate, HistoricalData
import json

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv(file_path, file_type, session_id):
    df = pd.read_csv(file_path)
    
    # Save historical data
    historical_data = HistoricalData(
        session_id=session_id,
        file_type=file_type,
        data=json.loads(df.to_json(orient='records'))
    )
    db.session.add(historical_data)
    
    # Clear existing data for this session and file type
    if file_type == 'supplier_agreements':
        SupplierAgreement.query.filter_by(session_id=session_id).delete()
    elif file_type == 'transactions':
        Transaction.query.filter_by(session_id=session_id).delete()
    elif file_type == 'claimed_rebates':
        ClaimedRebate.query.filter_by(session_id=session_id).delete()
    
    # Now add the new data
    if file_type == 'supplier_agreements':
        for _, row in df.iterrows():
            agreement = SupplierAgreement(
                session_id=session_id,
                supplier_id=row['supplier_id'],
                supplier_name=row['supplier_name'],
                contract_start=pd.to_datetime(row['contract_start']).date(),
                contract_end=pd.to_datetime(row['contract_end']).date(),
                rebate_type=row['rebate_type'],
                rebate_condition=row['rebate_condition'],
                product_category=row['product_category'],
                tier_1_threshold=row['tier_1_threshold'],
                tier_1_percentage=row['tier_1_percentage'],
                tier_2_threshold=row['tier_2_threshold'],
                tier_2_percentage=row['tier_2_percentage'],
                tier_3_threshold=row['tier_3_threshold'],
                tier_3_percentage=row['tier_3_percentage'],
                growth_target_percentage=row['growth_target_percentage'],
                mix_target_percentage=row['mix_target_percentage'],
                retention_period=row['retention_period'],
                flat_percentage=row['flat_percentage']
            )
            db.session.add(agreement)
    
    elif file_type == 'transactions':
        for _, row in df.iterrows():
            transaction = Transaction(
                session_id=session_id,
                transaction_id=row['transaction_id'],
                date=pd.to_datetime(row['date']).date(),
                supplier_id=row['supplier_id'],
                product_sku=row['product_sku'],
                product_category=row['product_category'],
                quantity=row['quantity'],
                price=row['price']
            )
            db.session.add(transaction)
    
    elif file_type == 'claimed_rebates':
        for _, row in df.iterrows():
            claimed_rebate = ClaimedRebate(
                session_id=session_id,
                claim_id=row['claim_id'],
                supplier_id=row['supplier_id'],
                period_start=pd.to_datetime(row['period_start']).date(),
                period_end=pd.to_datetime(row['period_end']).date(),
                amount_claimed=row['amount_claimed'],
                date_claimed=pd.to_datetime(row['date_claimed']).date()
            )
            db.session.add(claimed_rebate)
    
    db.session.commit()

def analyze_rebates(session_id):
    agreements = SupplierAgreement.query.filter_by(session_id=session_id).all()
    transactions = Transaction.query.filter_by(session_id=session_id).all()
    claimed_rebates = ClaimedRebate.query.filter_by(session_id=session_id).all()

    if not agreements or not transactions or not claimed_rebates:
        return []

    analysis = []
    for agreement in agreements:
        supplier_transactions = [t for t in transactions if t.supplier_id == agreement.supplier_id and agreement.contract_start <= t.date <= agreement.contract_end]
        total_purchase = sum(t.quantity * t.price for t in supplier_transactions)
        
        eligible_amount = calculate_rebate(agreement, supplier_transactions, total_purchase)
        
        claimed_amount = sum(cr.amount_claimed for cr in claimed_rebates if cr.supplier_id == agreement.supplier_id)
        
        analysis.append({
            'supplier_name': agreement.supplier_name,
            'supplier_id': agreement.supplier_id,
            'total_purchase': total_purchase,
            'rebate_type': agreement.rebate_type,
            'rebate_condition': agreement.rebate_condition,
            'eligible_amount': eligible_amount,
            'claimed_amount': claimed_amount,
            'difference': eligible_amount - claimed_amount
        })

    return analysis

def calculate_rebate(agreement, transactions, total_purchase):
    if agreement.rebate_type == 'Volume':
        return calculate_volume_rebate(agreement, total_purchase)
    elif agreement.rebate_type == 'Growth':
        return calculate_growth_rebate(agreement, total_purchase)
    elif agreement.rebate_type == 'Mix':
        return calculate_mix_rebate(agreement, transactions)
    elif agreement.rebate_type == 'Retention':
        return calculate_retention_rebate(agreement, transactions)
    elif agreement.rebate_type == 'Percentage':
        return calculate_percentage_rebate(agreement, total_purchase)
    else:
        return 0

def calculate_volume_rebate(agreement, total_purchase):
    if total_purchase > agreement.tier_3_threshold:
        return total_purchase * agreement.tier_3_percentage / 100
    elif total_purchase > agreement.tier_2_threshold:
        return total_purchase * agreement.tier_2_percentage / 100
    elif total_purchase > agreement.tier_1_threshold:
        return total_purchase * agreement.tier_1_percentage / 100
    return 0

def calculate_growth_rebate(agreement, total_purchase):
    growth_target = agreement.tier_1_threshold * (1 + agreement.growth_target_percentage / 100)
    if total_purchase >= growth_target:
        return total_purchase * agreement.tier_1_percentage / 100
    return 0

def calculate_mix_rebate(agreement, transactions):
    high_margin_purchases = sum(t.quantity * t.price for t in transactions if t.product_category == 'High Margin')
    total_purchases = sum(t.quantity * t.price for t in transactions)
    if total_purchases > 0 and (high_margin_purchases / total_purchases) >= agreement.mix_target_percentage / 100:
        return total_purchases * agreement.tier_1_percentage / 100
    return 0

def calculate_retention_rebate(agreement, transactions):
    # Simplified retention calculation - assumes continuous purchases over the retention period
    if len(set(t.date for t in transactions)) >= agreement.retention_period:
        total_purchases = sum(t.quantity * t.price for t in transactions)
        return total_purchases * agreement.flat_percentage / 100
    return 0

def calculate_percentage_rebate(agreement, total_purchase):
    return total_purchase * agreement.flat_percentage / 100