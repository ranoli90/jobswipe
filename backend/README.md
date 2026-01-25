# Job Ingestion System

The job ingestion system is a component of the Sorce-like job search app that handles collecting job postings from various sources, normalizing the data, and storing it in the database.

## Features

### 1. Job Sources

The system supports the following job sources:

#### Greenhouse Public Boards API
- **Endpoint**: `/api/ingest/sources/greenhouse/sync`
- **Method**: POST
- **Parameters**: `board_token` (Greenhouse board token), `incremental` (whether to use incremental sync)
- **Example**: `POST /api/ingest/sources/greenhouse/sync?board_token=airbnb&incremental=true`

#### Lever Public Postings API
- **Endpoint**: `/api/ingest/sources/lever/sync`
- **Method**: POST
- **Parameters**: `org_slug` (Lever organization slug), `incremental` (whether to use incremental sync)
- **Example**: `POST /api/ingest/sources/lever/sync?org_slug=github&incremental=true`

#### RSS Feeds
- **Endpoint**: `/api/ingest/sources/rss/sync`
- **Method**: POST
- **Parameters**: `feed_url` (URL of the RSS feed)
- **Example**: `POST /api/ingest/sources/rss/sync?feed_url=https://example.com/jobs.rss`

### 2. Job Deduplication

The system uses fuzzy matching to identify and remove duplicate jobs.

#### Find Duplicates
- **Endpoint**: `/api/deduplicate/find`
- **Method**: GET
- **Response**: List of duplicate job groups

#### Remove Duplicates
- **Endpoint**: `/api/deduplicate/remove`
- **Method**: POST
- **Response**: Number of duplicates removed

#### Run Deduplication
- **Endpoint**: `/api/deduplicate/run`
- **Method**: POST
- **Response**: Deduplication results

### 3. Job Categorization

The system uses NLP to categorize jobs into predefined categories.

#### Categorize All Jobs
- **Endpoint**: `/api/categorize/all`
- **Method**: POST
- **Response**: Categorization results

#### Get Category Distribution
- **Endpoint**: `/api/categorize/distribution`
- **Method**: GET
- **Response**: Category distribution of jobs

#### Run Categorization
- **Endpoint**: `/api/categorize/run`
- **Method**: POST
- **Response**: Categorization results

## Configuration

### API Keys

The system uses API keys for authentication. The following API keys can be configured in the `.env` file:

```env
INGESTION_API_KEY=your-ingestion-api-key
DEDUPLICATION_API_KEY=your-deduplication-api-key
CATEGORIZATION_API_KEY=your-categorization-api-key
```

### Job Categories

Job categories are predefined in the `JOB_CATEGORIES` dictionary in `/backend/services/job_categorization.py`. You can customize the categories and keywords to match your needs.

## Installation

### Dependencies

The system requires the following Python packages:

```
fastapi
uvicorn
pydantic
psycopg2-binary
sqlalchemy
alembic
redis
celery
httpx
playwright
beautifulsoup4
lxml
numpy
scipy
scikit-learn
spaCy
pytest
pytest-asyncio
pytest-cov
python-jose[cryptography]
passlib[bcrypt]
python-magic
minio
openai
python-dotenv
hypothesis
kafka-python
pymupdf
python-docx
pandas
numpy
fuzzywuzzy
python-Levenshtein
feedparser
```

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

### Database

The system uses PostgreSQL for storage. Make sure you have PostgreSQL installed and running. You can create the database tables using the SQL migration scripts in `/backend/db/migrations/`.

### SpaCy Model

The categorization service uses the spaCy library. You need to download the English language model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

### Starting the Server

To start the server, run:

```bash
uvicorn backend.api.main:app --reload
```

The server will be available at `http://localhost:8000`.

### API Documentation

API documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Testing

To run the tests, run:

```bash
pytest backend/tests/test_job_ingestion.py -v
```

This will run the tests for the job ingestion service.

## Architecture

The job ingestion system is composed of the following components:

1. **API Routers**: Handle HTTP requests and responses
2. **Services**: Implement business logic (ingestion, deduplication, categorization)
3. **Workers**: Handle asynchronous job processing
4. **Database Models**: Define the data structure

## License

This project is licensed under the MIT License.