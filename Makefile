IMAGE_NAME := csv_bot
COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env


CERT_DIR=certs
CERT_KEY=$(CERT_DIR)/server.key
CERT_CSR=$(CERT_DIR)/server.csr
CERT_CERT=$(CERT_DIR)/server.pem
CERT_DAYS=365
CERT_SUBJ="/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

.PHONY: clean_certs create_certs up

all: clean_certs create_certs up

create_certs: $(CERT_CERT)


$(CERT_DIR):
	mkdir -p $(CERT_DIR)

$(CERT_KEY): | $(CERT_DIR)
	openssl genrsa -out $(CERT_KEY) 2048


$(CERT_CERT):
	openssl req -newkey rsa:2048 -sha256 -nodes -x509 -days 365 -keyout $(CERT_KEY) -out $(CERT_CERT) -subj $(CERT_SUBJ)

clean_certs:
	rm -rf $(CERT_DIR)

build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up
stop:
	docker-compose -f $(COMPOSE_FILE) stop

down:
	docker-compose -f $(COMPOSE_FILE) down

clean:
	docker-compose -f $(COMPOSE_FILE) down --rmi all --volumes



ngrok: env
	ngrok http ${WEBHOOK_PORT}

rerun: down clean
	   echo "Rerunning..."
	   up


