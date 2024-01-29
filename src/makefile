# Create a Python virtual environment
venv:
	python3 -m venv venv
	
# Activate the virtual environment
activate:
	. ./venv/bin/activate

# Install dependencies
install:
	pip install -r requirements.txt

# Run the application
run:
	. ./venv/bin/activate
	uvicorn main:app --reload

# Install test requirements
install-test:
	pip install -r requirements-test.txt

# Test the application
test:
	. ./venv/bin/activate
	python -m pytest