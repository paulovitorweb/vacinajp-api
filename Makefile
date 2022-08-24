#
# Run api for development
dev:
	make config-local-mongodb
	uvicorn src.vacinajp.api.main:app --reload

#
# Run tests
test:
	ENVIRONMENT=test pytest --cov=src --cov-report=html

#
# Run lint
lint:
	flake8
	@echo "No lint problems found"

#
# Run lint and tests
check:
	make lint
	make test

#
# Config local mongodb for transactions
config-local-mongodb:
	# REPLICASET
	echo "rs.initiate({ _id: 'rs0', members: [{ _id: 0, host: 'local-mongo:27017' }] })" > local-replicaset.js
	docker cp local-replicaset.js mongodb:/replicaset.js
	docker exec mongodb bash -c 'mongo < /replicaset.js'
	rm local-replicaset.js