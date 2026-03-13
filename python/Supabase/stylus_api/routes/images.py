from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from .profile import supabase
from ..utils.auth import get_current_user_id

images_bp = Blueprint('images', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@images_bp.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload an image to Supabase Storage

    Form data:
    - file: image file
    - type: "outfit" | "wardrobe" | "trending"
    - category: "event" | "item" etc.
    - event_name: (optional) name of event
    - reference_id: (optional) UUID of related item
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    # Validate file exists
    if 'file' not in request.files:
        return jsonify({"error": "no file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "no file selected"}), 400

    # Validate file type and size
    if not allowed_file(file.filename):
        return jsonify({"error": "file type not allowed"}), 400

    file_size = len(file.read())
    file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": "file too large"}), 413

    # Get upload parameters
    image_type = request.form.get('type', 'outfit')
    category = request.form.get('category', 'event')
    event_name = request.form.get('event_name')
    reference_id = request.form.get('reference_id')

    # Generate unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())
    storage_path = f"users/{user_id}/{image_type}/{unique_id}.{file_ext}"

    try:
        # Upload to Supabase Storage
        response = supabase.storage.from_('images').upload(
            storage_path,
            file.read(),
            {
                'content-type': file.content_type,
                'upsert': False
            }
        )

        # Get public URL
        public_url = supabase.storage.from_('images').get_public_url(storage_path)

        # Save metadata to database
        image_record = {
            'user_id': user_id,
            'type': image_type,
            'category': category,
            'reference_id': reference_id,
            'storage_path': storage_path,
            'public_url': public_url['publicURL'],
            'file_name': secure_filename(file.filename),
            'file_size': file_size,
            'mime_type': file.content_type,
            'event_name': event_name,
            'event_date': datetime.now().date(),
        }

        db_response = supabase.table('images').insert(image_record).execute()

        if not db_response.data:
            return jsonify({"error": "failed to save metadata"}), 500

        return jsonify({
            "success": True,
            "image": {
                "id": db_response.data[0]['id'],
                "public_url": public_url['publicURL'],
                "storage_path": storage_path,
                "file_name": image_record['file_name']
            }
        }), 201

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@images_bp.route('/list/<image_type>', methods=['GET'])
def list_images(image_type):
    """
    Get all images of a certain type for current user

    Example: GET /api/images/list/outfit
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    try:
        response = supabase.table('images') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('type', image_type) \
            .order('created_at', desc=True) \
            .execute()

        return jsonify({"images": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@images_bp.route('/delete/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """
    Delete an image from storage and database
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    try:
        # Get image record
        image_record = supabase.table('images') \
            .select('*') \
            .eq('id', image_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        if not image_record.data:
            return jsonify({"error": "image not found"}), 404

        # Delete from storage
        supabase.storage.from_('images').remove([image_record.data['storage_path']])

        # Delete from database
        supabase.table('images').delete().eq('id', image_id).execute()

        return jsonify({"success": True, "message": "Image deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500