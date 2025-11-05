from flask import request, jsonify
from Utils.auth_decorator import token_required
from Utils.appError import AppError
from Models.messageModel import Message
from Models.lostItemModel import LostItem
from Models.messageModel import Message as MessageModel
from datetime import datetime, timedelta

@token_required
def create_message(user):
    data = request.get_json() or {}
    item_id = data.get('item_id')
    title = data.get('title')
    body = data.get('body')
    images = data.get('images', [])

    if not item_id or not title or not body:
        raise AppError("Missing required fields", 400)

    item = LostItem.objects(id=item_id).first()
    if not item:
        raise AppError("Item not found", 404)

    receiver = item.reported_by
    if not receiver:
        raise AppError("Item owner not found", 404)

    # --- Anti-duplicate logic: Prevent duplicate messages within 30s ---
    thirty_secs_ago = datetime.utcnow() - timedelta(seconds=30)
    duplicate = Message.objects(
        sender=user,
        receiver=receiver,
        item=item,
        title=title,
        body=body,
        created_at__gte=thirty_secs_ago
    ).first()
    if duplicate:
        raise AppError("Duplicate: You've already sent this message recently.", 429)
    # ---------------------------------------------------------------

    msg = Message(
        sender=user,
        receiver=receiver,
        item=item,
        title=title,
        body=body,
        images=images,
        read=False
    )
    msg.save()

    return jsonify({"success": True, "message": "Message sent"}), 201

@token_required
def get_inbox(user):
    item_id = request.args.get('item_id')
    q = {'receiver': user}
    if item_id:
        q['item'] = item_id
    msgs = Message.objects(**q).order_by('-created_at')
    data = []
    for m in msgs:
        data.append({
            "id": str(m.id),
            "sender_name": f"{getattr(m.sender, 'first_name', '')} {getattr(m.sender, 'last_name', '')}".strip() or getattr(m.sender, 'name', 'Unknown'),
            "title": m.title,
            "body": m.body,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "read": bool(m.read),
            "item_id": str(m.item.id) if m.item else None
        })
    return jsonify({"success": True, "data": data}), 200

@token_required
def mark_read(user, message_id):
    m = Message.objects(id=message_id, receiver=user).first()
    if not m:
        raise AppError("Message not found", 404)
    m.read = True
    m.save()
    return jsonify({"success": True}), 200

@token_required
def reply_message(user):
    data = request.get_json() or {}
    message_id = data.get('message_id')
    title = data.get('title')
    body = data.get('body')
    if not message_id or not title or not body:
        raise AppError("Missing required fields", 400)
    orig = Message.objects(id=message_id).first()
    if not orig:
        raise AppError("Original message not found", 404)
    # Receiver becomes original sender
    msg = Message(
        sender=user,
        receiver=orig.sender,
        item=orig.item,
        title=title,
        body=body,
        read=False
    )
    msg.save()
    return jsonify({"success": True}), 201

