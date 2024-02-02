# Create a Python virtual environment
venv:
	python3 -m venv venv
	
# Activate the virtual environment
activate:
	. ./venv/bin/activate

# Install dependencies
install:
	. ./venv/bin/activate && pip install -r requirements.txt

# Run the application
run:
	. ./venv/bin/activate && uvicorn main:app --reload --port 8001

# Install test requirements
install-test:
	pip install -r requirements-test.txt

# Test the application
test:
	. ./venv/bin/activate
	python -m pytest