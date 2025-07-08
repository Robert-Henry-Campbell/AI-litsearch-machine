# Contributing

Thank you for considering a contribution! This project uses **Black**, **Ruff** and **pytest** with coverage.

Before submitting a pull request:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```
2. Format and lint the code:
   ```bash
   black .
   ruff check .
   ```
3. Run the test suite with coverage (minimum 85% required):
   ```bash
   pytest --cov=. --cov-report=term --cov-fail-under=85
   ```

CI runs the same commands automatically.
