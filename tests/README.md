# Tests

This directory contains comprehensive unit tests for the Azure Cloud Booking Service.

## Test Structure

```
tests/
├── __init__.py              # Tests package initialization
├── conftest.py              # Shared pytest fixtures and configuration
├── test_config.py           # Tests for application configuration
├── test_health.py           # Tests for health check endpoints
├── test_main.py             # Tests for FastAPI application
└── test_servicebus.py       # Tests for Service Bus receiver service
```

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run tests with coverage report
```bash
uv run pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
uv run pytest tests/test_servicebus.py
```

### Run specific test class or function
```bash
uv run pytest tests/test_servicebus.py::TestServiceBusReceiverService::test_start_success
```

### Run with verbose output
```bash
uv run pytest -v
```

### Run with debug output
```bash
uv run pytest -vv -s
```

## Test Coverage

The tests provide comprehensive coverage of:

### Service Bus Receiver (`test_servicebus.py`)
- ✅ Service initialization
- ✅ Starting and stopping the service
- ✅ Receiving and processing messages
- ✅ Error handling and retries
- ✅ Task cancellation and timeout handling
- ✅ Multiple start/stop scenarios
- ✅ Integration tests

### FastAPI Application (`test_main.py`)
- ✅ Root endpoint redirection
- ✅ API documentation endpoints
- ✅ Health check endpoints
- ✅ Application lifecycle (startup/shutdown)
- ✅ Error handling during startup/shutdown
- ✅ Concurrent request handling
- ✅ API router integration

### Configuration (`test_config.py`)
- ✅ Default values
- ✅ Environment variable overrides
- ✅ Required field validation
- ✅ Boolean parsing
- ✅ Case-insensitive settings
- ✅ Immutability

### Health Checks (`test_health.py`)
- ✅ Basic health check
- ✅ Detailed health check
- ✅ Database health status
- ✅ Service Bus health status
- ✅ Error handling in health checks
- ✅ Proper HTTP status codes

## Mocking Strategy

The tests use comprehensive mocking to avoid dependencies on external services:

- **Azure Service Bus**: Mocked using `unittest.mock.AsyncMock` and `MagicMock`
- **Database connections**: Mocked to return predetermined health statuses
- **Environment variables**: Mocked using `patch.dict(os.environ, ...)`
- **Settings**: Mocked to provide consistent test configuration

## Fixtures

### Shared Fixtures (conftest.py)

- `mock_service_bus_client`: Provides a mocked ServiceBusClient
- `mock_service_bus_receiver`: Provides a mocked ServiceBusReceiver with async support
- `mock_service_bus_message`: Provides a mocked ServiceBusReceivedMessage
- `mock_messages`: Provides a list of mock messages for batch testing
- `event_loop_policy`: Configures async event loop for Windows compatibility

### Test-Specific Fixtures

Each test file includes fixtures specific to its domain (e.g., `service`, `client`, `mock_settings`)

## Test Patterns

### Async Testing
```python
async def test_async_operation(self, service):
    await service.start()
    assert service._running is True
```

### Mocking External Services
```python
with patch("app.services.servicebus.ServiceBusClient.from_connection_string") as mock:
    mock.return_value = mock_service_bus_client
    await service.start()
```

### Testing Error Handling
```python
mock_client.get_queue_receiver = MagicMock(side_effect=Exception("Connection failed"))
task = asyncio.create_task(service._receive_messages())
# Verify graceful error handling
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

- No external dependencies required
- Fast execution (all mocked)
- Comprehensive coverage reporting
- Clear pass/fail criteria

## Code Coverage Reports

After running tests with coverage, open the HTML report:

```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

The coverage report shows:
- Line coverage per file
- Branch coverage
- Missed lines highlighted
- Overall coverage percentage

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Deterministic**: Tests produce the same results every time
3. **Fast**: All external dependencies are mocked
4. **Readable**: Test names clearly describe what is being tested
5. **Comprehensive**: Edge cases and error conditions are tested

## Troubleshooting

### Tests hang or timeout
- Check for unhandled async operations
- Ensure all asyncio tasks are properly awaited or cancelled

### Mock not working as expected
- Verify the patch path is correct (use the import path, not the definition path)
- Check that async mocks use `AsyncMock` instead of `MagicMock`

### Windows-specific issues
- The `event_loop_policy` fixture handles Windows compatibility
- Ensure pytest-asyncio is installed: `uv add --dev pytest-asyncio`
