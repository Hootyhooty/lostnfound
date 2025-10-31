import logging
import os

from flask import request, jsonify, send_file
import io
import uuid
from PIL import Image

from Models.allImgsModel import AllImgs
from Controllers.viewController import view_bp
from Models.allImgsModel import AllImgs
from Utils.appError import AppError
from Utils.auth_decorator import token_required

logger = logging.getLogger(__name__)

def upload_image_to_all_imgs():
    try:
        # ✅ Accept both 'image' and 'file' keys
        if "image" in request.files:
            image_file = request.files["image"]
        elif "file" in request.files:
            image_file = request.files["file"]
        else:
            raise AppError("No image file provided", 400)

        mime_type = image_file.mimetype
        if mime_type not in ["image/png", "image/jpeg"]:
            raise AppError("Only PNG and JPEG formats are supported", 400)

        image = Image.open(image_file)
        file_extension = "png" if mime_type == "image/png" else "jpg"

        # ✅ Keep original filename, normalize extension
        original_name = os.path.splitext(image_file.filename)[0]
        filename = f"{original_name}.{file_extension}"

        # ✅ If filename already exists in DB, append a unique suffix
        existing = AllImgs.objects(filename=filename).first()
        if existing:
            unique_suffix = uuid.uuid4().hex[:8]
            filename = f"{original_name}_{unique_suffix}.{file_extension}"

        image = image.convert("RGB")
        image = image.resize((800, 800))

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="JPEG" if file_extension == "jpg" else "PNG")
        img_byte_arr.seek(0)

        # ✅ Save into MongoDB GridFS
        img_doc = AllImgs(filename=filename, content_type=mime_type)
        img_doc.file.put(img_byte_arr, content_type=mime_type)
        img_doc.save()

        logger.info(f"✅ Uploaded image: {filename}")
        return jsonify({
            "status": "success",
            "message": "Image uploaded successfully",
            "data": {
                "filename": filename,
                "id": str(img_doc.id)
            }
        }), 201

    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise AppError(f"Error uploading image: {str(e)}", 500)


def get_image_from_all_imgs(filename):
    try:
        img_doc = AllImgs.objects(filename=filename).first()
        if not img_doc:
            raise AppError("Image not found", 404)

        img_data = img_doc.file.read()
        return send_file(
            io.BytesIO(img_data),
            mimetype=img_doc.content_type,
            as_attachment=False,
            download_name=filename
        )
    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving image {filename}: {str(e)}")
        raise AppError(f"Error retrieving image: {str(e)}", 500)

def upload_default_image_to_all_imgs():
    """
    Automatically find and upload '../images/default.jpg' into all_imgs collection.
    """
    try:
        # Find project root and resolve path to default.jpg
        project_root = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(project_root, "..", "images", "default.jpg")
        default_path = os.path.normpath(default_path)

        if not os.path.exists(default_path):
            raise AppError(f"Default image not found at: {default_path}", 404)

        with open(default_path, "rb") as f:
            existing = AllImgs.objects(filename="default.jpg").first()
            if existing:
                logger.info("♻️ Replacing existing default.jpg in all_imgs")
                existing.file.replace(f, content_type="image/jpeg")
                existing.save()
            else:
                img_doc = AllImgs(filename="default.jpg", content_type="image/jpeg")
                img_doc.file.put(f, content_type="image/jpeg")
                img_doc.save()

        logger.info(f"✅ Uploaded default.jpg to all_imgs from {default_path}")
        return jsonify({
            "status": "success",
            "message": "Default image uploaded successfully",
            "path": default_path
        }), 201

    except AppError as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading default image: {str(e)}")
        raise AppError(f"Error uploading default image: {str(e)}", 500)


@view_bp.route("/uploads/<filename>")
def get_image(filename):
    img = AllImgs.objects(filename=filename).first()
    if not img:
        raise AppError("Image not found", 404)

    gridout = img.file.get()
    return send_file(
        io.BytesIO(gridout.read()),
        mimetype=img.content_type or "image/jpeg"
    )

@token_required
def get_me(current_user):
    try:
        user_data = {
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
            "photo": current_user.photo if current_user.photo else "default.jpg",
            "profile_slug": current_user.profile_slug
        }
        return jsonify({"success": True, "user": user_data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@token_required
def update_profile(current_user):
    try:
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'alternate_email' in data:
            current_user.alternate_email = data['alternate_email']
        if 'address_line1' in data:
            current_user.address_line1 = data['address_line1']
        if 'address_line2' in data:
            current_user.address_line2 = data['address_line2']
        if 'city' in data:
            current_user.city = data['city']
        if 'state' in data:
            current_user.state = data['state']
        if 'zipcode' in data:
            current_user.zipcode = data['zipcode']
        if 'country' in data:
            current_user.country = data['country']
        if 'display_phone' in data:
            current_user.display_phone = bool(data['display_phone'])
        
        current_user.save()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": current_user.to_json()
        }), 200
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@token_required
def deactivate_account(current_user):
    try:
        current_user.active = False
        current_user.save()
        
        return jsonify({
            "success": True,
            "message": "Account deactivated successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error deactivating account: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500