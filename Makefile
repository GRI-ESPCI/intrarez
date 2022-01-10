
SHELL := /bin/bash

help:
	@echo "IntraRez Makefile - v0.1.0"
	@echo "The following directives are available:"
	@echo "		install 	Install IntraRez (development mode)"
	@echo "					Run all steps described in README §Installation"
	@echo "		deploy 		Make IntraRez ready for production"
	@echo "					Run all steps described in README §Passage en prod"
	@echo "		update 		Install IntraRez (development mode)"
	@echo "					Run all steps described in README Mise à jour"
	@echo "		help 		Show this message and exit"

install:
	@echo "Installing IntraRez (development mode)..."
	# Check packages
	EXECUTABLES = python3 mysql postfix git npm
	K := $(foreach exec,$(EXECUTABLES),\
	    $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))
	# Install dependecies
	python3 -m venv env
	env/bin/pip install -r requirements.txt
	env/bin/pip install pymysql cryptography
	npm install
	# Configure .env
	cp .conf_models/.model.env .env
	SECRET_KEY=$(shell python3 -c "import uuid; print(uuid.uuid4().hex)")
	sed -e "s/some-random-key/$(SECRET_KEY)" .env
	edit .env
	# Create database
	SQL_PASS=$(shell bash -c 'read -s -p "SQL user password: " pwd; echo $$pwd')
	SQL_PASS_SEDESC=$(printf '%s\n' "$SQL_PASS" | sed -e 's/[]\/$*.^[]/\\&/g');
	sed -e "s/<mdp-db>/$(SQL_PASS_SEDESC)" .env
	@echo "We need privileges to create MySQL base and user:"
	sudo su postgres -c "psql \
		-c \"CREATE ROLE intrarez WITH LOGIN PASSWORD '$(SQL_PASS)'\" \
		-c \"CREATE DATABASE intrarez OWNER intrarez ENCODING 'UTF8'\""
	# Other steps
	echo "export FLASK_APP=intrarez.py" >> ~/.profile
	bower install
	env/bin/flask translate compile
	env/bin/flask sass compile
	@echo "All set, try source 'env/bin/activate' then 'flask run'!"

deploy:
	@echo "Installing production mode..."
	# Check packages
	EXECUTABLES = supervisor nginx
	K := $(foreach exec,$(EXECUTABLES),\
	    $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))
	# Update environment
	cp .conf_models/prod.flaskenv .flaskenv
	env/bin/pip install gunicorn
	# Configure Supervisor
	cp .conf_models/supervisor.conf /etc/supervisor/conf.d/intrarez.conf
	supervisorctl reload
	# Configure Nginx
	cp .conf_models/nginx.conf /etc/nginx/sites-enabled/intrarez
	service nginx reload

update:
	@echo "Updating IntraRez..."
	# Get last version
	git pull
	# Update dependencies
	env/bin/pip install -r requirements.txt
	npm install
	bower install
	# Upgrade application
	@echo "Stopping application before critical updates..."
	sudo supervisorctl stop intrarez
	env/bin/flask db upgrade
	env/bin/flask translate compile
	env/bin/flask sass compile
	@echo "Compressing static files..."
	find app/static -name "*.gz" -type f -delete
	gzip -krf app/static
	@echo "Starting application..."
	sudo supervisorctl start intrarez
	@echo "Update live!"
