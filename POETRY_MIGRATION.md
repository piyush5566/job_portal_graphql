# Migration from pip to Poetry

This document outlines the changes made to migrate the project from pip to Poetry for dependency management.

## Changes Made

1. Created a `pyproject.toml` file with:
   - Project metadata
   - All dependencies from `requirements.txt`
   - Development dependencies (pytest, black, flake8, etc.)
   - Tool configurations (black, isort, pytest)

2. Updated `.gitignore` to include Poetry-specific files:
   - `poetry.lock`
   - `.pytest_cache/`
   - `dist/`

3. Updated `README.md` to reflect the change to Poetry:
   - Updated Prerequisites section
   - Updated Installation instructions
   - Updated Running the Application section
   - Updated Testing section
   - Updated Database Migrations section
   - Updated Project Structure section

4. Created a test script (`test_poetry_setup.py`) to verify the Poetry setup

## How to Test the Migration

1. Install Poetry if you haven't already:
   ```bash
   # Windows PowerShell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

   # Linux/macOS
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the Poetry virtual environment:
   ```bash
   poetry shell
   ```

4. Run the test script to verify the Poetry setup:
   ```bash
   python test_poetry_setup.py
   ```

5. Run the application to ensure it works with Poetry:
   ```bash
   python run.py
   ```

## Reverting to pip (if needed)

If you need to revert to pip for any reason, you can:

1. Create a new virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

2. Install dependencies from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

## Notes

- The original `requirements.txt` file has been kept for reference
- Poetry will automatically create and manage a virtual environment for the project
- Poetry will generate a `poetry.lock` file to lock dependencies to specific versions
- You can add new dependencies using `poetry add package-name`
- You can add development dependencies using `poetry add --group dev package-name`