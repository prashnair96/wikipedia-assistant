# Makefile

# Install Python dependencies
requirements:
	pip install -r requirements.txt

# Run your full setup pipeline via the shell script
run-etl:
	bash setup.sh

# Run the FastAPI application
run-api:
	uvicorn app.api.main:app --reload

# Clean pycache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +

# Show help
help:
	@echo "Available commands:"
	@echo "  make requirements   - Install dependencies"
	@echo "  make run-etl        - Run full ETL pipeline via setup.sh"
	@echo "  make run-api        - Start FastAPI app"
	@echo "  make clean          - Remove temporary files"