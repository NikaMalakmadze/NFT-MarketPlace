from datetime import datetime, timezone
from flask_login.utils import login_user, login_required, logout_user
from flask.templating import render_template
from flask.helpers import redirect, url_for
from pydantic import ValidationError
from flask.globals import request
from flask.json import jsonify

from app.nft.utils import get_nft_image, get_category_image
from app.api.allowedwallets.models import AllowedWallet
from app.user.schemas import UserRegister, UserLogin
from app.collection.models import NFTCollection
from app.main.decorators import admin_required
from app.main.utils import validate_wallet_id
from app.jwt.utils import generate_tokens
from app.extensions import login_manager
from app.nft.models import NFT, Category, Offer
from config import ALLOWED_EXTENSIONS
from app.user.models import User
from app.extensions import db
from app.main import main_bp
from config import settings

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@main_bp.route("/", methods=['GET'])
def index_page():

    trusted_by = AllowedWallet.query.all()
    nfts: list[NFT] = (
        NFT.query.filter_by(is_listed=True).order_by(NFT.created_at.desc()).limit(10).all()
    )

    categories: list[Category] = Category.query.all()

    return render_template(
        "main/index.html",
        trusted_by=[*trusted_by, {"name": "TBCBank", "logo": "images/logos/tbc.svg"}],
        nfts=nfts,
        categories=categories
    )


@main_bp.route("/connect")
def connect():
    wallets = AllowedWallet.query.all()
    return render_template("main/connect.html", wallets=wallets)


@main_bp.route("/connect/create-account", methods=["POST"])
# @limiter.limit('5 per minute')
def create_acount():
    try:
        data: UserRegister = UserRegister(**request.json)
    except ValidationError as e:
        return jsonify({"message": "Invalid input", "errors": e.errors()}), 400

    if User.query.filter_by(email=data.email).first():
        return jsonify({"message": "Email already registered"}), 400

    if User.query.filter_by(username=data.username).first():
        return jsonify({"message": "Username already taken"}), 400

    new_user: User = User(
        username=data.username.lower(),
        display_name=data.displayName,
        wallet=data.wallet_id,
        email=data.email,
    )
    new_user.hash_password(data.password)

    db.session.add(new_user)
    db.session.commit()

    access_token, refresh_token = generate_tokens(new_user.id)

    response = jsonify(
        {
            "message": "User registered successfully",
            "access_token": access_token,
        }
    )

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=settings.jwt.JWT_REFRESH_TOKEN_EXPIRES * 60,
    )

    login_user(new_user)

    return response, 201


@main_bp.route("/connect/create-account", methods=["GET"])
# @limiter.limit('5 per minute')
def register_page():
    try:
        validate_wallet_id(request.args.get("card-id"))
    except ValueError as e:
        return render_template("main/register.html", error=e)
    return render_template("main/register.html")


@main_bp.route("/connect/login", methods=["POST"])
def login():
    try:
        data: UserLogin = UserLogin(**request.json)
    except ValidationError as e:
        return jsonify({"message": "Invalid input", "errors": e.errors()}), 400

    user: User = User.query.filter_by(email=data.email).first()
    if not user:
        return jsonify({"message": "User with that email Doesn't exists"}), 400

    if not User.query.filter_by(username=data.username):
        return jsonify({"message": "Username Doesn't exists"}), 400

    if not user.validate_password(data.password):
        return jsonify({"message": "Invalid Password"}), 400

    access_token, refresh_token = generate_tokens(user.id, user.role)

    response = jsonify({"access_token": access_token})

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=settings.jwt.JWT_REFRESH_TOKEN_EXPIRES * 60,
    )

    login_user(user)

    return response, 200


@main_bp.route("/connect/login", methods=["GET"])
def login_page():
    return render_template("main/login.html")


@main_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    response = redirect(url_for("main.index_page"))

    response.set_cookie(
        "refresh_token", "", max_age=0, httponly=True, samesite="Strict", secure=True
    )

    logout_user()

    return response

@main_bp.route("/drops", methods=['GET'])
def drops_page():
    nft_categories: list[Category] = Category.query.all()

    return render_template('main/drops.html', categories=nft_categories, file_types=ALLOWED_EXTENSIONS)

@main_bp.route('/admin', methods=['GET'])
@admin_required
def admin_page():
    user_count: int = User.query.count()
    nft_count: int = NFT.query.count()
    collection_count: int = NFTCollection.query.count()
    active_offers: int = Offer.query.filter(
        Offer.is_accepted == False,
        Offer.is_cancelled == False,
        Offer.expires_at > datetime.now(timezone.utc)
    ).count()

    return render_template(
        'main/admin.html',
        total_users=user_count,
        total_nfts=nft_count,
        total_collections=collection_count,
        active_offers=active_offers
    )