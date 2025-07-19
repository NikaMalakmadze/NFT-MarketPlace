
import os
from flask.globals import request
from flask.json import jsonify

from app.api.collectionCategory.schemas import CollectionCategoryCreate, CollectionCategoryResponse, CollectionCategoryDelete
from app.api.collectionCategory import collection_category_api_bp
from app.jwt.decorators import jwt_required, admin_required
from app.collection.models import CollectionCategory
from app.api.utils import validate_values
from app.extensions import db
from config import settings

@collection_category_api_bp.route('/', methods=['GET'])
@jwt_required
@admin_required
def get_categories():
    collection_categories = CollectionCategory.query.all()
    if not collection_categories: 
        return jsonify({'status': 'Not Found', 'message': 'No Collection categories'}), 404
    return jsonify([
        CollectionCategoryResponse.model_validate(collection_category, from_attributes=True).model_dump() for collection_category in collection_categories
    ])

@collection_category_api_bp.route('/add', methods=['POST'])
@jwt_required
@admin_required
def add_collection_category():
    request_json: dict = request.json
    collection_category_name: str = request_json.get('name')
    collection_category_description: str = request_json.get('description')
    collection_category_logo = request_json.get('logo_file')
    validated_value = validate_values(
        {
            'name': collection_category_name.lower(),
            'description': collection_category_description,
            'logo_file': collection_category_logo
        },
        validator=CollectionCategoryCreate,
        item_name='CollectionCategory',
        model=CollectionCategory,
        find_model_by='name'
    )

    if isinstance(validated_value, tuple):
        return validated_value

    if validated_value:
        return jsonify({
            'status': 'exists',
            'message': f"Collection category '{validated_value.name}' already exists",
            'category_id': validated_value.id
        }), 200 
    
    new_collection_category = CollectionCategory(
        name=collection_category_name.lower(),
        description=collection_category_description,
        logo_file=collection_category_logo
    )
    db.session.add(new_collection_category)
    db.session.commit()

    return jsonify({
            'status': 'succsess', 
            'message': f'{collection_category_name} Collection category was added',
            'CollectionCategoryInformation': CollectionCategoryResponse.model_validate(new_collection_category, from_attributes=True).model_dump()
         }), 201

@collection_category_api_bp.route('/delete', methods=['DELETE'])
@jwt_required
@admin_required
def delete_allowed_wallet():
    request_json: dict = request.json
    validated_value = validate_values(
        {
            'id': request_json.get('id')
        },
        validator=CollectionCategoryDelete,
        model=CollectionCategory,
        item_name='CollectionCategory',
        find_model_by='id'
    )
    if not validated_value:
        return jsonify({'status': 'error', 'message': f'Collection Category with id: {request_json.get('id')} not found'}), 404
    
    if isinstance(validated_value, tuple): 
        return validated_value

    if os.path.isfile(settings.db.APP_FILES / 'collection-categories' / validated_value.logo_file):
        os.remove(settings.db.APP_FILES / 'collection-categories' /  validated_value.logo_file)

    db.session.delete(validated_value)
    db.session.commit()

    return jsonify({
        'status': 'succsess', 
        'message': f'{validated_value.name} is Forbidden from this moment',
        'CollectionCategoryInformation': CollectionCategoryResponse.model_validate(validated_value, from_attributes=True).model_dump()
    }), 200
