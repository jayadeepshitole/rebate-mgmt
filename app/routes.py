from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
from werkzeug.utils import secure_filename
from app import db
from app.models import Session, SupplierAgreement, Transaction, ClaimedRebate
from app.utils import allowed_file, process_csv, analyze_rebates
import os
import uuid

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        new_session = Session(session_id=session['session_id'])
        db.session.add(new_session)
        db.session.commit()

    if request.method == 'POST':
        file = request.files['file']
        file_type = request.form.get('file_type')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            session_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session['session_id'])
            if not os.path.exists(session_upload_folder):
                os.makedirs(session_upload_folder)
            file_path = os.path.join(session_upload_folder, filename)
            file.save(file_path)
            
            process_csv(file_path, file_type, session['session_id'])
            return jsonify({"status": "success", "message": f"{file_type} uploaded and processed successfully"})
        return jsonify({"status": "error", "message": "Invalid file"})
    return render_template('index.html')

@main.route('/report')
def report():
    if 'session_id' not in session:
        flash("Please upload your data first.")
        return redirect(url_for('main.index'))
    
    analysis = analyze_rebates(session['session_id'])
    if not analysis:
        flash("No data available for analysis. Please upload all required files.")
        return redirect(url_for('main.index'))
    
    total_eligible = sum(item['eligible_amount'] for item in analysis)
    total_claimed = sum(item['claimed_amount'] for item in analysis)
    
    return render_template('report.html', analysis=analysis, total_eligible=total_eligible, total_claimed=total_claimed)

@main.route('/check_uploads')
def check_uploads():
    if 'session_id' not in session:
        return jsonify({
            "supplier_agreements": False,
            "transactions": False,
            "claimed_rebates": False
        })
    
    session_id = session['session_id']
    return jsonify({
        "supplier_agreements": bool(SupplierAgreement.query.filter_by(session_id=session_id).first()),
        "transactions": bool(Transaction.query.filter_by(session_id=session_id).first()),
        "claimed_rebates": bool(ClaimedRebate.query.filter_by(session_id=session_id).first())
    })

@main.route('/remove_file', methods=['POST'])
def remove_file():
    if 'session_id' not in session:
        return jsonify({"status": "error", "message": "No active session"}), 400
    
    file_type = request.json.get('file_type')
    session_id = session['session_id']

    if file_type == 'supplier_agreements':
        SupplierAgreement.query.filter_by(session_id=session_id).delete()
    elif file_type == 'transactions':
        Transaction.query.filter_by(session_id=session_id).delete()
    elif file_type == 'claimed_rebates':
        ClaimedRebate.query.filter_by(session_id=session_id).delete()
    else:
        return jsonify({"status": "error", "message": "Invalid file type"}), 400

    db.session.commit()
    return jsonify({"status": "success", "message": "File removed"})