
from flask import render_template, send_from_directory, abort
from flask_login import current_user

from app.nft.models import NFT, Category, NFTView
from app.extensions import db
from config import settings
from app.nft import nft_bp

@nft_bp.route('/<token_id>', methods=['GET'])
def nft_item_info(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return abort(404)

    if nft.is_blocked:
        return abort(403)

    if not current_user.is_anonymous:

        is_viewed: NFTView = NFTView.query.filter_by(
            user_id=current_user.id,
            token_id=nft.token_id
        ).first()

        if not is_viewed:
            view: NFTView = NFTView(
                user_id=current_user.id,
                nft_id=nft.id,
                token_id=nft.token_id
            )

            db.session.add(view)
            db.session.commit()

    return render_template("nft/nft-item.html", nft=nft)

@nft_bp.route('/<token_id>/get-image', methods=['GET'])
def get_nft_image(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return abort(404)
    
    if nft.is_blocked:
        return abort(403)

    nft_image_file = nft.image_file

    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'nft-images',
        nft_image_file
    )

@nft_bp.route('/category/<category_id>', methods=['GET'])
def get_category_image(category_id):
    category: Category = Category.query.filter_by(id=category_id).first()
    if not category:
        return abort(404)

    category_image_file = category.logo

    return send_from_directory(
        settings.db.APP_FILES / 'category-icons',
        category_image_file
    )