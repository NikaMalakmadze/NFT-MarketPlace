
from flask.globals import current_app
import click

from app.api.allowedwallets.models import AllowedWallet
from app.user.models import User
from app.nft.models import NFT
from app.extensions import db

@click.command('add-admin')
@click.argument('username')
@click.argument('password')
@click.argument('email')
@click.argument('display_name')
@click.argument('wallet_id')
def create_admin(
    username: str,
    password: str,
    email: str,
    display_name: str,
    wallet_id: str
    ) -> None:    
    with current_app.app_context():
        if User.query.filter((User.username==username) | (User.email==email)).first():
            click.echo("User with this username or email already exists.")
            return
        
        try:
            wallet_id = int(wallet_id)
        except (TypeError, ValueError):
            click.echo("Wallet id must be number")
            return
    
        if not AllowedWallet.query.filter_by(id=wallet_id).first():
            click.echo("Invalid Wallet Id")
            return

        admin = User(
            username=username.lower(),
            email=email,
            display_name=display_name,
            wallet=wallet_id,
            role='admin'
        )
        admin.hash_password(password)
        db.session.add(admin)
        db.session.commit()

        click.echo(f"Admin user '{username}' created.")

@click.command('show-admins')
def show_admins():
    admins: list[User] = User.query.filter_by(role='admin').all()
    if not admins:
        print('No admins')

    for index, admin in enumerate(admins, 1):
        print()
        print(f'--------- Admin N:{index} ---------')
        print(f'Username: {admin.username}')
        print(f'Email: {admin.email}')
        print(f'Admin From Date: {admin.created_at}')
        print(f'Is Blocked?: {admin.is_blocked}')
        print(f'Is Active?: {admin.is_active}')

@click.command('delete-all-nft')
def delete_all_nft():
    from flask import current_app
    import os

    from app.nft.models import NFT
    from app.utils import delete_table
    from config import settings

    for file in os.listdir(settings.db.UPLOAD_FOLDER / 'nft-images'):
        os.remove(settings.db.UPLOAD_FOLDER / 'nft-images' / file)

    with current_app.app_context():
        delete_table(NFT, db)
        db.create_all()

@click.command('delete-all-collections')
def delete_all_collections():
    from flask import current_app
    import os

    from app.collection.models import NFTCollection
    from app.utils import delete_table
    from config import settings

    for file in os.listdir(settings.db.UPLOAD_FOLDER / 'collection-featured'):
        os.remove(settings.db.UPLOAD_FOLDER / 'collection-featured' / file)

    for file in os.listdir(settings.db.UPLOAD_FOLDER / 'collection-logo'):
        os.remove(settings.db.UPLOAD_FOLDER / 'collection-logo' / file)

    for file in os.listdir(settings.db.UPLOAD_FOLDER / 'collection-baner'):
        os.remove(settings.db.UPLOAD_FOLDER / 'collection-baner' / file)

    with current_app.app_context():
        db.session.query(NFT).filter(NFT.collection_id.isnot(None)).update(
            {NFT.collection_id: None}, synchronize_session=False
        )
        db.session.commit()
        db.session.close()
        db.engine.dispose()
        delete_table(NFTCollection, db)
        db.create_all()

def register_commands(app) -> None:
    app.cli.add_command(create_admin)
    app.cli.add_command(show_admins)
    app.cli.add_command(delete_all_nft)
    app.cli.add_command(delete_all_collections)