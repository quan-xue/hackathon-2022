# hackathon-2022


## Create a .env file
Create a `.env` file with the respective telegram API tokens.

## Setup

To run the service locally, you are encouraged to run with the Docker Compose setup as the Postgres service and database are set up for you. Hot reload is supported.

```
# run locally
docker-compose up

# spin down the container
docker-compose down -v
```


To setup the PSA DB:

```bash
python ./scripts/psa_setup_db.py
```

The DB file will automatically be created in the data folder for usage by the container.
