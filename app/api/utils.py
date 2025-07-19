
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask.json import jsonify
from pydantic import BaseModel
from flask import request
from pathlib import Path
from uuid import uuid4

from app.utils import allowed_image_type

def validate_values(
    attributes: dict,
    validator: BaseModel, 
    item_name: str, 
    model,
    find_model_by: str 
    ):

    for attribute, attribute_value in attributes.items():
        if not attribute_value:
            return jsonify({'status': 'error', 'message': f'{item_name} {attribute} parameter is required'}), 400
    try:
        validated = validator(**attributes)
    except Exception as e:
        return jsonify(
            {
                'status': 'error',
                'errors': { error['loc'][0]: error['msg'] for error in e.errors() }
            }
        ), 400

    return model.query.filter_by(
        **{ find_model_by: getattr(validated, find_model_by) }
    ).first()

def validate_image(
    image_attribute: str,
    save_folder: Path,
    form_data_dict: dict,
    save_image: bool = True
):
    if image_attribute not in request.files:
        return jsonify({'errors': [f'No {image_attribute} image file in request']}), 400
    
    file: FileStorage = request.files[image_attribute]

    if file.filename == '':
        return jsonify({'errors': [f'No {image_attribute} file selected']}), 400
        
    if file and allowed_image_type(file.filename) and save_image:
        filename: str = f'{uuid4().hex}-{secure_filename(file.filename)}'
        file.save(save_folder / filename)
    else:
        return jsonify({'errors': ['Invalid file type']}), 400

    form_data_dict[image_attribute] = file.filename
    return filename

def update_old_image(
    file: FileStorage,
    old_filename: str,
    upload_dir: Path,
    default_filename: str = ''
):
    
    if not file or file.filename == "":
        return old_filename
    
    filename = secure_filename(file.filename)
    unique_name = f"{uuid4().hex}_{filename}"
    file_path = upload_dir / unique_name
    file.save(file_path)

    old_path = upload_dir / old_filename
    if old_path.exists():
        old_path.unlink()

    return unique_name