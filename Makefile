IMAGE_NAME := csv_bot
COMPOSE_FILE := docker-compose.yml
DEV_COMPOSE_FILE := docker-compose.dev.yaml
ENV_FILE := .env
DEV_ENV_FILE := .env.dev

CERT_DIR = certs
CERT_KEY = $(CERT_DIR)/server_pkey.pem
CERT_CERT = $(CERT_DIR)/server_cert.pem
CERT_DAYS = 365
CERT_SUBJ = "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=${host}"

.PHONY: all clean_certs create_certs build up stop down clean ngrok rerun

all: clean_certs create_certs build up

create_certs: $(CERT_CERT)

$(CERT_DIR):
	mkdir -p $(CERT_DIR)

$(CERT_KEY): | $(CERT_DIR)
	openssl genrsa -out $(CERT_KEY) 2048

$(CERT_CERT): | $(CERT_DIR)
	openssl req -newkey rsa:2048 -sha256 -nodes -x509 -days $(CERT_DAYS) -keyout $(CERT_KEY) -out $(CERT_CERT) -subj $(CERT_SUBJ)

clean_certs:
	rm -rf $(CERT_DIR)

build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up

stop:
	docker-compose -f $(COMPOSE_FILE) stop

down:
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down

clean:
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --rmi all --volumes

ngrok: env
	ngrok http $(WEBHOOK_PORT)

rerun: down clean
	@echo "Rerunning..."
	$(MAKE) up

dev:
	docker-compose -f $(DEV_COMPOSE_FILE) --env-file $(DEV_ENV_FILE) up

