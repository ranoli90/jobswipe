# OpenAI Integration for Job Matching

## Overview
This document describes the OpenAI integration for the Sorce job matching system. The integration provides advanced semantic matching capabilities using OpenAI's GPT models.

## Features

### 1. Job Embedding Generation
- Generates vector embeddings for job descriptions using OpenAI's text-embedding-ada-002 model
- Enables semantic similarity calculations between jobs and candidate profiles

### 2. Profile Embedding Generation
- Converts candidate profiles to text format and generates embeddings
- Handles structured profile data including skills, experience, education, and preferences

### 3. Semantic Match Analysis
- Uses GPT-4 to analyze job-candidate matches
- Provides detailed analysis including:
  - Match score (0-1 scale)
  - Matched skills
  - Missing skills
  - Recommendations for improvement

### 4. Job Entity Extraction
- Extracts structured information from job descriptions
- Identifies:
  - Required skills
  - Technologies mentioned
  - Responsibilities
  - Minimum requirements (education, experience)

### 5. Fallback Mechanism
- Gracefully falls back to rule-based matching if OpenAI API is unavailable
- Provides consistent user experience even when AI services are down

## Configuration

### Environment Variables

```bash
# OpenAI API (required for advanced matching)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=2000
```

### Configuration File
Create a `.env` file in the project root with the required variables. See `.env.example` for a template.

## Usage

### Initialization
The OpenAI service is automatically initialized when the application starts.

### Job Feed with AI Matching
The job feed endpoint `/api/jobs/feed` now uses AI-powered matching:

```http
GET /api/jobs/feed?cursor=abc123&limit=20 HTTP/1.1
Authorization: Bearer {token}
```

### Match Analysis
To get detailed match analysis:

```python
from services.matching import calculate_job_score
from services.openai_service import OpenAIService

score = await calculate_job_score(job, profile)
```

## Performance Characteristics

### API Rate Limits
- OpenAI has rate limits based on your API key tier
- Service automatically handles rate limiting and retries

### Response Times
- Job embedding generation: ~0.5 seconds
- Profile embedding generation: ~0.3 seconds
- Match analysis: ~2-5 seconds
- Fallback rule-based matching: <0.1 seconds

### Cost Estimation
- Text embeddings: ~$0.0001 per job description
- Match analysis with GPT-4: ~$0.01 per match
- For 1000 daily job matches: ~$10.10 per day

## Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/test_openai_service.py -v
```

### Property-Based Tests
```bash
python -m pytest tests/test_matching_properties.py -v -xvs
```

### Quick Test
```bash
cd backend
python test_quick.py
```

## Security Considerations

### API Key Management
- Store API keys in secure environment variables
- Never hardcode API keys in source code
- Use environment-specific configurations

### Input Validation
- All inputs to OpenAI are sanitized and validated
- No raw user input is directly sent to OpenAI API

### Error Handling
- Comprehensive error handling for API failures
- Fallback mechanism to ensure system availability
- Detailed logging of errors

## Monitoring

### Metrics
- API call success/failure rates
- Response times
- Token usage tracking
- Cost tracking

### Logging
- Detailed logs of all OpenAI interactions
- Error logging with context information
- Performance monitoring

## Future Improvements

### 1. Caching
- Cache embeddings for repeated job descriptions
- Implement TTL for cached matches

### 2. Batch Processing
- Batch job embedding generation
- Parallel processing for large datasets

### 3. Model Optimization
- Experiment with different embedding models
- Fine-tune GPT model for specific job domains

### 4. Cost Optimization
- Implement dynamic temperature adjustment
- Intelligent batching strategies

### 5. Security Hardening
- Add API key rotation support
- Implement request signing
- Add rate limiting per user

## Contributing

### Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Create `.env` file from `.env.example`
3. Run tests: `python -m pytest tests/test_openai_service.py -v`

### Code Structure
- `services/openai_service.py`: Core integration
- `services/matching.py`: Matching algorithm
- `api/routers/jobs.py`: API endpoints
- `tests/test_openai_service.py`: Unit tests

## License
Internal use only. Do not use to violate any site's Terms of Service.
