from flask import request, jsonify, redirect
from Utils.auth_decorator import token_required
from Models.salesModel import Sale
from Models.userModel import User
from datetime import datetime
import os
import json

try:
    import stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
except Exception:
    stripe = None

try:
    from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
    from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
except Exception:
    OrdersCreateRequest = OrdersCaptureRequest = None
    PayPalHttpClient = SandboxEnvironment = LiveEnvironment = None

from Utils.catalog import validate_and_price_items

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


# ============================
# Stripe Checkout
# ============================
def create_stripe_checkout():
    data = request.get_json() or {}
    items = data.get('items', [])
    # Validate against catalog and compute totals server-side
    try:
        validated_items, total_cents = validate_and_price_items(items)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    total_price = total_cents / 100.0
    # Persist sale using validated snapshot
    items_json = [json.dumps(it) for it in validated_items]
    sale = Sale(items=items_json, total_price=total_price, created_at=datetime.utcnow(), status='created', payment_method='stripe')
    sale.save()

    if not stripe:
        return jsonify({'error': 'Stripe SDK not available'}), 500

    line_items = []
    for it in validated_items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': it['name']},
                'unit_amount': it['unit_price_cents'],
            },
            'quantity': it['qty']
        })

    session = stripe.checkout.Session.create(
        mode='payment',
        line_items=line_items,
        success_url=f"{request.host_url.rstrip('/')}/stripe/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{request.host_url.rstrip('/')}/shop?paid=stripe_cancel",
        metadata={'sale_id': str(sale.id)},
        payment_intent_data={
            'metadata': {'sale_id': str(sale.id)}
        }
    )
    # save session id for later reconciliation
    sale.stripe_id = session.id
    sale.save()
    return jsonify({'url': session.url})


def stripe_success():
    if not stripe:
        return redirect('/shop?paid=stripe_error')
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect('/shop?paid=stripe_error')
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        sale = Sale.objects(stripe_id=session_id).first()
        if session.get('payment_status') == 'paid' and sale:
            sale.status = 'paid'
            sale.save()
        return redirect('/shop?paid=stripe_success')
    except Exception:
        return redirect('/shop?paid=stripe_error')


# ============================
# PayPal Orders v2
# ============================
def _paypal_client():
    env = os.getenv('PAYPAL_ENV', 'sandbox').lower()
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None
    if env == 'live':
        environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
    else:
        environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
    return PayPalHttpClient(environment)


def paypal_create_order():
    data = request.get_json() or {}
    items = data.get('items', [])
    try:
        validated_items, total_cents = validate_and_price_items(items)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    total_price = total_cents / 100.0
    items_json = [json.dumps(it) for it in validated_items]

    client = _paypal_client()
    if client is None:
        return jsonify({'error': 'PayPal not configured'}), 500

    req = OrdersCreateRequest()
    req.prefer('return=representation')
    return_url = f"{request.host_url.rstrip('/')}/paypal/return"
    cancel_url = f"{request.host_url.rstrip('/')}/shop?paid=paypal_cancel"
    req.request_body({
        'intent': 'CAPTURE',
        'purchase_units': [{
            'amount': {'currency_code': 'USD', 'value': f"{total_price:.2f}"}
        }],
        'application_context': {
            'brand_name': 'Lost&Found',
            'return_url': return_url,
            'cancel_url': cancel_url
        }
    })
    try:
        resp = client.execute(req)
        order_id = resp.result.id
        approve_url = next((l.href for l in resp.result.links if l.rel == 'approve'), None)
        sale = Sale(items=items_json, total_price=total_price, created_at=datetime.utcnow(), status='pending', payment_method='paypal', paypal_id=order_id)
        sale.save()
        return jsonify({'id': order_id, 'approve_url': approve_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def paypal_return():
    client = _paypal_client()
    if client is None:
        return redirect('/shop?paid=paypal_error')
    order_id = request.args.get('token') or request.args.get('orderId') or request.args.get('orderID')
    if not order_id:
        return redirect('/shop?paid=paypal_error')
    try:
        capture = client.execute(OrdersCaptureRequest(order_id))
        status = getattr(capture.result, 'status', '')
        sale = Sale.objects(paypal_id=order_id).first()
        if status == 'COMPLETED' and sale:
            # Extract capture id for auditing
            cap_id = None
            try:
                pu = capture.result.purchase_units[0]
                cap_id = pu.payments.captures[0].id
            except Exception:
                cap_id = None
            sale.status = 'paid'
            if cap_id:
                sale.paypal_capture_id = cap_id
            sale.save()
            return redirect('/shop?paid=paypal_success')
        return redirect('/shop?paid=paypal_error')
    except Exception:
        return redirect('/shop?paid=paypal_error')


# ============================
# Stripe Webhook for server-side confirmation
# ============================
def stripe_webhook():
    if not stripe:
        return jsonify({"error": "Stripe SDK not available"}), 500
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        return jsonify({"error": "Webhook secret not configured"}), 500
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return jsonify({"error": "Invalid signature"}), 400

    # Handle events we care about
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')
        payment_intent_id = session.get('payment_intent')
        sale = Sale.objects(stripe_id=session_id).first()
        charge_id = None
        try:
            if payment_intent_id:
                pi = stripe.PaymentIntent.retrieve(payment_intent_id)
                charge_id = pi.get('latest_charge')
        except Exception:
            charge_id = None
        if sale:
            sale.status = 'paid'
            if charge_id:
                sale.stripe_charge_id = charge_id
            sale.save()
    elif event['type'] == 'payment_intent.succeeded':
        pi = event['data']['object']
        charge_id = pi.get('latest_charge')
        # If metadata carried sale_id, reconcile by it
        sale_id = None
        try:
            sale_id = (pi.get('metadata') or {}).get('sale_id')
        except Exception:
            sale_id = None
        if sale_id:
            try:
                sale = Sale.objects.get(id=sale_id)
            except Exception:
                sale = None
        else:
            sale = None
        if sale:
            sale.status = 'paid'
            if charge_id:
                sale.stripe_charge_id = charge_id
            sale.save()
    return jsonify({"received": True})
