import click
from flask.cli import with_appcontext
from app.models.user import User
from app.extensions import db

@click.command('create-admin')
@with_appcontext
@click.option('--email', prompt='Admin email', help='Email address for admin user')
@click.option('--username', prompt='Admin username', help='Username for admin user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for admin user')
def create_admin(email, username, password):
    """Create an admin user."""
    try:
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            click.echo('Error: Email already registered')
            return
        if User.query.filter_by(username=username).first():
            click.echo('Error: Username already taken')
            return

        # Create admin user
        admin = User(
            username=username,
            email=email,
            is_admin=True
        )
        admin.set_password(password)
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        click.echo(f'Successfully created admin user: {username}')
    
    except Exception as e:
        click.echo(f'Error creating admin user: {str(e)}')
        db.session.rollback() 