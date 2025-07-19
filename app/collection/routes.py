
from flask import abort, render_template, send_from_directory

from app.collection.models import NFTCollection
from app.collection import collection_bp
from config import settings

@collection_bp.route('/<int:collection_id>/get-image/featured', methods=['GET'])
def get_featured_image(collection_id):
    collection: NFTCollection = NFTCollection.query.filter_by(id=collection_id).first()
    if not collection:
        return abort(404)

    featured_image_file = collection.featured_file

    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'collection-featured',
        featured_image_file
    )

@collection_bp.route('/<int:collection_id>/get-image/baner', methods=['GET'])
def get_baner_image(collection_id):
    collection: NFTCollection = NFTCollection.query.filter_by(id=collection_id).first()
    if not collection:
        return abort(404)

    baner_image_file = collection.baner_file

    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'collection-baner',
        baner_image_file
    )


@collection_bp.route('/<int:collection_id>/get-image/logo', methods=['GET'])
def get_logo_image(collection_id):
    collection: NFTCollection = NFTCollection.query.filter_by(id=collection_id).first()
    if not collection:
        return abort(404)

    logo_image_file = collection.logo_file

    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'collection-logo',
        logo_image_file
    )

@collection_bp.route('/<int:collection_id>', methods=['GET'])
def collection_page(collection_id):
    collection: NFTCollection = NFTCollection.query.filter_by(id=collection_id).first()
    if not collection:
        return abort(404)
    
    return render_template('collection.html', collection=collection)