#!/usr/bin/env python3
"""
Initialize the PICO Platform database and create user accounts.
"""
from app import app, db, User
from werkzeug.security import generate_password_hash
import sys

def create_user(username, password):
    """Create a new user account."""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists!")
            return False
        
        # Create new user
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        print(f"User '{username}' created successfully!")
        return True

def init_database():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

def list_users():
    """List all users."""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found.")
        else:
            print("\nExisting users:")
            for user in users:
                print(f"  - {user.username} (ID: {user.id})")

def delete_user(username):
    """Delete a user account."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found!")
            return False
        
        db.session.delete(user)
        db.session.commit()
        print(f"User '{username}' deleted successfully!")
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python init_db.py init                    - Initialize database")
        print("  python init_db.py create <user> <pass>    - Create user account")
        print("  python init_db.py list                    - List all users")
        print("  python init_db.py delete <user>           - Delete user account")
        return
    
    command = sys.argv[1]
    
    if command == 'init':
        init_database()
        
    elif command == 'create':
        if len(sys.argv) < 4:
            print("Usage: python init_db.py create <username> <password>")
            return
        username = sys.argv[2]
        password = sys.argv[3]
        create_user(username, password)
        
    elif command == 'list':
        list_users()
        
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Usage: python init_db.py delete <username>")
            return
        username = sys.argv[2]
        delete_user(username)
        
    else:
        print(f"Unknown command: {command}")

if __name__ == '__main__':
    main()
