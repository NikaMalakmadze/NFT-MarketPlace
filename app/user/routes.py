
from flask import abort, redirect, send_from_directory, url_for
from flask.templating import render_template
from flask_login.utils import current_user
from flask_login import login_required
from pathlib import Path

from app.collection.models import CollectionCategory, NFTCollection
from app.user.models import Follower, User
from config import ALLOWED_EXTENSIONS
from config import settings, BASE_DIR
from app.nft.models import Category
from app.extensions import db
from app.user import user_bp

@user_bp.route('/create', methods=['GET'])
@login_required
def create_nft_page():
    categories: list[Category] = Category.query.all()
    supporteds: list[str] = ALLOWED_EXTENSIONS
    user_collections: list[NFTCollection] = NFTCollection.query.filter_by(user_id=current_user.id)
    collection_categories: list[CollectionCategory] = CollectionCategory.query.all()
    return render_template(
        'user/createNft.html', 
        categories=categories,
        supporteds=supporteds,
        collections=user_collections,
        collection_categories=collection_categories
        )

@user_bp.route('/<int:user_id>/get-image/logo', methods=['GET'])
def get_logo_image(user_id):
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    user_logo_file = user.profile_avatar

    static_path: Path = BASE_DIR / 'app' / 'static' / 'images'
    if user_logo_file == 'defaultAvatar.png':
        return send_from_directory(static_path, 'defaultAvatar.png')
    
    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'user-logo',
        user_logo_file
    )

@user_bp.route('/<int:user_id>/get-image/bg', methods=['GET'])
def get_bg_image(user_id):
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    user_bg_file = user.profile_background

    static_path: Path = BASE_DIR / 'app' / 'static' / 'images'
    if user_bg_file == 'defaultBg.png':
        return send_from_directory(static_path, 'defaultBg.png')
    
    return send_from_directory(
        settings.db.UPLOAD_FOLDER / 'user-bg',
        user_bg_file
    )

@user_bp.route('/profile/<int:user_id>')
def profile_page(user_id):
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)
    
    if user.is_blocked:
        return abort(403)

    is_current = False

    if not current_user.is_anonymous:
        if current_user.id == user_id:
            is_current = True

    return render_template('user/profile.html', user=user, is_current=is_current)

@user_bp.route('/profile/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    if current_user.id == user_id:
        return abort(400)

    user: User = User.query.get_or_404(user_id)

    if user.is_blocked:
        return abort(403)

    follow: Follower = Follower(
        follower_id=current_user.id,
        followed_id=user.id
    )

    db.session.add(follow)
    db.session.commit()

    return redirect(url_for("user.profile_page", user_id=user.id))

@user_bp.route('/profile/<int:user_id>/unfollow', methods=['POST'])
@login_required
def unfollow_user(user_id):
    if current_user.id == user_id:
        return abort(400)

    user: User = User.query.get_or_404(user_id)

    if user.is_blocked:
        return abort(403)

    follow = Follower.query.filter_by(
        follower_id=current_user.id,
        followed_id=user.id
    ).first()

    if follow:
        db.session.delete(follow)
        db.session.commit()

    return redirect(url_for("user.profile_page", user_id=user.id))

@user_bp.route('/profile/<int:user_id>/update-page')
@login_required
def update_profile_page(user_id):
    if current_user.id != user_id:
        return abort(401)
    
    user: User = User.query.get_or_404(user_id)

    if user.is_blocked:
        return abort(403)

    return render_template('user/updateProfile.html', user=user)
