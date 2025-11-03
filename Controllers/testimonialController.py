from flask import Blueprint, request, jsonify
from Utils.appError import AppError
from Utils.auth_decorator import token_required
from Models.testimonialModel import Testimonial


testimonial_bp = Blueprint('testimonial', __name__, url_prefix='/api/testimonials')


@testimonial_bp.route('', methods=['POST'])
@token_required
def create_testimonial(user):
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()

    if not message:
        raise AppError('Message is required', 400)
    if len(message) > 1000:
        raise AppError('Message is too long (max 1000 characters)', 400)

    # Upsert: if user already has a testimonial, replace its message
    existing = Testimonial.objects(user=user).first()
    if existing:
        existing.message = message
        existing.created_at = existing.created_at  # keep original date
        existing.save()
        t = existing
    else:
        t = Testimonial(user=user, message=message)
        t.save()
    return jsonify({
        'success': True,
        'testimonial': {
            'id': str(t.id),
            'message': t.message,
            'user_name': getattr(user, 'name', 'Anonymous'),
            'user_photo': getattr(user, 'photo', 'default.jpg')
        }
    }), 201


@testimonial_bp.route('', methods=['GET'])
def list_testimonials():
    # Optional: random selection
    try:
        limit = int(request.args.get('limit', 10))
    except Exception:
        limit = 10
    random = request.args.get('random', 'false').lower() in ('1', 'true', 'yes')

    items = []
    if random:
        samples = list(Testimonial.objects.aggregate({"$sample": {"size": limit}}))
        for doc in samples:
            t = Testimonial.objects(id=doc.get('_id')).first()
            if not t or not t.is_public:
                continue
            items.append({
                'id': str(t.id),
                'message': t.message,
                'user_name': getattr(t.user, 'name', 'Anonymous'),
                'user_photo': getattr(t.user, 'photo', 'default.jpg')
            })
    else:
        qs = Testimonial.objects(is_public=True).order_by('-created_at').limit(limit)
        for t in qs:
            items.append({
                'id': str(t.id),
                'message': t.message,
                'user_name': getattr(t.user, 'name', 'Anonymous'),
                'user_photo': getattr(t.user, 'photo', 'default.jpg')
            })

    return jsonify({'success': True, 'items': items}), 200


@testimonial_bp.route('/me', methods=['GET'])
@token_required
def my_testimonial(user):
    t = Testimonial.objects(user=user).first()
    if not t:
        return jsonify({'success': True, 'hasTestimonial': False}), 200
    return jsonify({
        'success': True,
        'hasTestimonial': True,
        'testimonial': {
            'id': str(t.id),
            'message': t.message,
            'user_name': getattr(user, 'name', 'Anonymous'),
            'user_photo': getattr(user, 'photo', 'default.jpg')
        }
    }), 200


