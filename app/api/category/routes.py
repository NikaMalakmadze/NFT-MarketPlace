
from flask.globals import request
from flask.json import jsonify

from app.api.category.schemas import CategoryResponse, CategoryCreate
from app.jwt.decorators import admin_required, jwt_required
from app.api.category import category_api_bp
from app.api.utils import validate_values
from app.nft.models import Category
from app.extensions import db

@category_api_bp.route('/', methods=['GET'])
@jwt_required
@admin_required
def get_categories():
    categories = Category.query.all()
    if not categories: 
        return jsonify({'status': 'Not Found', 'message': 'No categories'}), 404
    
    categories_dicts: list[dict] = [
        CategoryResponse.model_validate(category, from_attributes=True).model_dump() for category in categories
    ]

    return jsonify({'status': 'success', 'categories': categories_dicts}), 200

@category_api_bp.route('/add', methods=['POST'])
@jwt_required
@admin_required
def add_category():
    request_json: dict = request.json
    category_name = request_json.get('name')
    category_logo = request_json.get('logo')
    validated_value = validate_values(
        {
        'name': category_name.lower(),
        'logo': category_logo
        },
        category_logo,
        CategoryCreate,
        item_name='category',
        model=Category,
        find_model_by='name'
    )
    if validated_value is tuple:
        return validated_value

    if validated_value:
        return jsonify({
            'status': 'exists',
            'message': f"category '{validated_value.name}' already exists",
            'category_id': validated_value.id
        }), 200 
    
    new_category = Category(name=category_name, logo=category_logo)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({
            'status': 'succsess', 
            'message': f'{category_name} category was added',
            'categoryInformation': CategoryResponse.model_validate(new_category, from_attributes=True).model_dump()
         }), 201

@category_api_bp.route('/update/<int:category_id>', methods=['PATCH'])
@jwt_required
@admin_required
def update_category(category_id):
    category: Category = db.get_or_404(Category, category_id)

    request_json: dict = request.json
    category_name = request_json.get('name', category.name)
    category_logo = request_json.get('logo', category.logo)

    validated_value = validate_values(
        {
            'name': category_name.lower(),
            'logo': category_logo
        },
        category_logo,
        CategoryCreate,
        item_name='category',
        model=Category,
        find_model_by='name',
    )

    if validated_value is tuple:
        return validated_value

    category.name = category_name
    category.logo = category_logo
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Category {category.id} was updated',
        'categoryInformation': CategoryResponse.model_validate(category, from_attributes=True).model_dump()
    }), 200
