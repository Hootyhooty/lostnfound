from flask import request, jsonify
from Utils.auth_decorator import token_required
from Models.salesModel import Sale
from Models.userModel import User
from datetime import datetime

@token_required  # allow guest checkout
def create_sale(user):
    data = request.get_json() or {}
    items = data.get('items', [])
    total_price = data.get('total_price')
    payment_method = data.get('payment_method', '')
    # Simple validation
    if not (items and total_price is not None):
        return jsonify({'success': False, 'message': 'Missing basket info'}), 400
    # Store as JSON-encoded string to preserve all basket fields
    import json
    items_json = [json.dumps(it) for it in items]
    sale = Sale(
        user=user ,
        items=items_json,
        total_price=total_price,
        created_at=datetime.utcnow(),
        status='created',
        payment_method=payment_method
    )
    sale.save()
    return jsonify({'success': True, 'sale_id': str(sale.id)})
