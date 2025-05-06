"""
Test script to verify that the Poetry setup is working correctly.
This script imports key modules from the project to ensure they can be found.
"""

import os
import sys

def test_imports():
    """Test importing key modules from the project."""
    try:
        from flask import Flask
        from app import create_app
        from models import User
        from extensions import db
        from config import config
        
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test creating a Flask application instance."""
    try:
        from app import create_app
        app = create_app()
        print("✅ App creation successful!")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Poetry setup...")
    imports_ok = test_imports()
    app_ok = test_app_creation() if imports_ok else False
    
    if imports_ok and app_ok:
        print("\n🎉 Poetry setup is working correctly! 🎉")
        sys.exit(0)
    else:
        print("\n❌ Poetry setup has issues that need to be resolved.")
        sys.exit(1)