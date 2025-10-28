#!/usr/bin/env python3
"""User management script for the PICO multi-user application."""

import sys
from pathlib import Path
from getpass import getpass
from flask import Flask

# Setup Flask app for database access
app = Flask(__name__)
app.config["SECRET_KEY"] = "management-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pico_experiments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from database import db, User

db.init_app(app)


def list_users():
    """List all users in the database."""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        
        print("\n=== All Users ===")
        print(f"{'ID':<5} {'Username':<20} {'Created At'}")
        print("-" * 60)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nTotal users: {len(users)}\n")


def add_user(username: str = None, password: str = None):
    """Add a new user to the database."""
    with app.app_context():
        # Get username
        if not username:
            username = input("Enter username: ").strip()
        
        if not username:
            print("Error: Username cannot be empty")
            return False
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Error: User '{username}' already exists")
            return False
        
        # Get password
        if not password:
            password = getpass("Enter password: ")
            password_confirm = getpass("Confirm password: ")
            
            if password != password_confirm:
                print("Error: Passwords do not match")
                return False
        
        if len(password) < 4:
            print("Error: Password must be at least 4 characters long")
            return False
        
        # Create user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        
        try:
            db.session.commit()
            print(f"✓ User '{username}' created successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            return False


def delete_user(username: str = None):
    """Delete a user from the database."""
    with app.app_context():
        # Get username
        if not username:
            username = input("Enter username to delete: ").strip()
        
        if not username:
            print("Error: Username cannot be empty")
            return False
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: User '{username}' not found")
            return False
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Deletion cancelled")
            return False
        
        # Delete user
        db.session.delete(user)
        
        try:
            db.session.commit()
            print(f"✓ User '{username}' deleted successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting user: {e}")
            return False


def change_password(username: str = None):
    """Change a user's password."""
    with app.app_context():
        # Get username
        if not username:
            username = input("Enter username: ").strip()
        
        if not username:
            print("Error: Username cannot be empty")
            return False
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: User '{username}' not found")
            return False
        
        # Get new password
        new_password = getpass("Enter new password: ")
        password_confirm = getpass("Confirm new password: ")
        
        if new_password != password_confirm:
            print("Error: Passwords do not match")
            return False
        
        if len(new_password) < 4:
            print("Error: Password must be at least 4 characters long")
            return False
        
        # Update password
        user.set_password(new_password)
        
        try:
            db.session.commit()
            print(f"✓ Password for user '{username}' changed successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error changing password: {e}")
            return False


def show_help():
    """Show usage information."""
    print("""
PICO User Management

Usage: python manage_users.py [command] [options]

Commands:
  list                  List all users
  add [username]        Add a new user (prompts for password)
  delete [username]     Delete a user
  password [username]   Change a user's password
  help                  Show this help message

Examples:
  python manage_users.py list
  python manage_users.py add
  python manage_users.py add admin
  python manage_users.py delete user1
  python manage_users.py password admin
""")


def main():
    """Main entry point for user management."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    
    elif command == "add":
        username = sys.argv[2] if len(sys.argv) > 2 else None
        add_user(username)
    
    elif command == "delete":
        username = sys.argv[2] if len(sys.argv) > 2 else None
        delete_user(username)
    
    elif command == "password":
        username = sys.argv[2] if len(sys.argv) > 2 else None
        change_password(username)
    
    elif command in ["help", "-h", "--help"]:
        show_help()
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python manage_users.py help' for usage information")


if __name__ == "__main__":
    main()
