# Azure Cloud Booking Service

A pet grooming booking service built with FastAPI, SQLAlchemy, Azure SQL Database, and Azure Service Bus.

## Features

- 🚀 **FastAPI** - Modern, fast web framework with automatic API documentation
- 📨 **Azure Service Bus** - Event-driven messaging with queue-based communication
- 🗄️ **SQLAlchemy** - ORM for Azure SQL Database integration
- 📊 **Pydantic** - Data validation and settings management
- 🔄 **Async Background Tasks** - Continuous message processing from Service Bus Queue
- 📖 **API Versioning** - Structured v1 API endpoints for future extensibility
- 🏥 **Health Checks** - Built-in health monitoring endpoints

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Azure SQL Database instance
- Azure Service Bus Namespace with a Queue

### Installing ODBC Driver (Windows)

```powershell
winget install Microsoft.ODBCDriver18forSQLServer
```

Verify installation:

```powershell
Get-OdbcDriver | Where-Object {$_.Name -like "*ODBC Driver 18*"}
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/azure-cloud-booking-service.git
cd azure-cloud-booking-service
```

2. Install dependencies:

```bash
uv sync
```

3. Configure environment variables:

```bash
cp env_example .env
```

Edit `.env` with your Azure credentials:

```env
# Database Configuration
DB_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:your-server.database.windows.net,1433;Database=your-database;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;

# Service Bus Configuration
SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=your-key
SERVICE_BUS_QUEUE_NAME=your-queue-name
```

**Getting Azure Service Bus Connection String:**
1. Go to **Azure Portal → Service Bus Namespace**
2. Navigate to **Shared access policies → RootManageSharedAccessKey**
3. Copy the **Primary Connection String**

## Project Structure

```
azure-cloud-booking-service/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Pydantic settings
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py  # v1 API router
│   │       └── health.py    # Health check endpoint
│   └── services/
│       ├── database.py      # Database connection utilities
│       └── servicebus.py    # Service Bus receiver
├── models/
│   ├── base.py              # SQLAlchemy base class
│   ├── user.py              # User model
│   ├── pet.py               # Pet model
│   └── booking.py           # Booking model & status enum
├── examples/
│   └── sqlalchemy_demo.py   # Database demo script
├── pyproject.toml           # Project dependencies
└── .env                     # Environment configuration
```

## Models

### User

| Column         | Type         | Description              |
|----------------|--------------|--------------------------|
| user_id        | UUID (PK)    | Unique identifier        |
| first_name     | VARCHAR(100) | User's first name        |
| last_name      | VARCHAR(100) | User's last name         |
| email          | VARCHAR(255) | Email (unique, indexed)  |
| phone          | VARCHAR(20)  | Phone number (optional)  |
| bookings_taken | INTEGER      | Number of bookings       |

### Pet

| Column               | Type           | Description                |
|----------------------|----------------|----------------------------|
| pet_id               | UUID (PK)      | Unique identifier          |
| user_id              | UUID (FK)      | Owner's user ID            |
| name                 | VARCHAR(100)   | Pet's name                 |
| breed                | VARCHAR(100)   | Breed (optional)           |
| species              | VARCHAR(50)    | Species (Dog, Cat, etc.)   |
| age                  | INTEGER        | Age in years (optional)    |
| weight               | DECIMAL(10,2)  | Weight in kg (optional)    |
| special_instructions | TEXT           | Care notes (optional)      |

### Booking

| Column            | Type          | Description                    |
|-------------------|---------------|--------------------------------|
| booking_id        | UUID (PK)     | Unique identifier              |
| booking_date_time | DATETIME      | Appointment date/time          |
| booking_status    | VARCHAR(20)   | Status (see BookingStatus)     |
| groomer_id        | UUID          | Assigned groomer ID            |
| user_id           | UUID (FK)     | Customer's user ID             |
| pet_id            | UUID (FK)     | Pet being groomed              |
| rating            | DECIMAL(3,2)  | Customer rating (optional)     |

### BookingStatus Enum

- `pending` - Awaiting confirmation
- `confirmed` - Appointment confirmed
- `in_progress` - Service in progress
- `completed` - Service completed
- `cancelled` - Appointment cancelled
- `no_show` - Customer didn't show up

## Usage

### Running the FastAPI Application

Start the FastAPI server with hot-reload for development:

```bash
# run from root directory
uv run -m app.main
# or
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check Endpoint**: http://localhost:8000/api/v1/health

### Service Bus Message Processing

The application automatically starts a background task that:
1. Connects to your Azure Service Bus Queue
2. Continuously polls for new messages
3. Prints received messages to the console
4. Completes messages (removes them from the queue) after processing

**To test message reception:**
1. Send messages to your Azure Service Bus Queue using Azure Portal or Azure CLI
2. Watch the console output for received messages:
   ```
   📨 Service Bus Event Received: <message content>
   ```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "azure-cloud-booking-service",
  "version": "0.1.0",
  "timestamp": "2025-12-13T10:30:00.000000Z"
}
```

### Running the SQLAlchemy Demo

To test database operations with the example script:

```bash
uv run python examples/sqlalchemy_demo.py
```

This demo will:
- Create database tables
- Insert sample users, pets, and bookings
- Query and display the data
- Clean up (delete data and drop tables)

### Using Database Services in Your Code

```python
from models import User, Pet, Booking, BookingStatus
from app.services import DatabaseManager, create_engine_from_connection_string

# Create engine from connection string
engine = create_engine_from_connection_string(connection_string)

# Initialize database manager
db = DatabaseManager(engine)

# Create tables
db.create_tables()

# Use session scope for transactions
with db.session_scope() as session:
    # Create a user
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1-555-123-4567"
    )
    session.add(user)
    session.flush()  # Get the user_id

    # Create a pet
    pet = Pet(
        user_id=user.user_id,
        name="Buddy",
        species="Dog",
        breed="Golden Retriever"
    )
    session.add(pet)
    session.flush()

    # Create a booking
    from datetime import datetime
    import uuid

    booking = Booking(
        booking_date_time=datetime(2025, 12, 15, 10, 0),
        booking_status=BookingStatus.CONFIRMED,
        groomer_id=uuid.uuid4(),
        user_id=user.user_id,
        pet_id=pet.pet_id
    )
    session.add(booking)
    # Commits automatically when exiting the context

# Query data
with db.session_scope() as session:
    users = session.query(User).all()
    bookings = session.query(Booking).filter_by(
        booking_status=BookingStatus.CONFIRMED.value
    ).all()
```

### Using create_azure_sql_engine (Alternative)

```python
from app.services import create_azure_sql_engine

engine = create_azure_sql_engine(
    server="your-server.database.windows.net",
    database="your-database",
    username="your-username",
    password="your-password",
)
```

## Azure Setup

### Azure SQL Database

1. Create an Azure SQL Database in the Azure Portal
2. Configure firewall rules to allow your IP address:
   - Go to **SQL Server → Networking → Firewall rules**
   - Add your client IP
3. Copy the ODBC connection string from:
   - **SQL Database → Connection strings → ODBC**

### Azure Service Bus

1. Create a Service Bus Namespace in the Azure Portal
2. Create a Queue in the namespace:
   - Go to **Service Bus Namespace → Entities → Queues**
   - Click **+ Queue**
   - Enter a queue name (e.g., `booking-events`)
   - Use default settings or customize as needed
3. Get the connection string:
   - Go to **Service Bus Namespace → Shared access policies**
   - Select **RootManageSharedAccessKey**
   - Copy the **Primary Connection String**

## Development

### Project Organization

- **`app/`** - Main application code
  - **`api/v1/`** - Version 1 API endpoints (use v2 for breaking changes)
  - **`services/`** - Business logic and external service integrations
  - **`config.py`** - Configuration management with Pydantic
  - **`main.py`** - FastAPI application entry point

- **`models/`** - SQLAlchemy database models
- **`examples/`** - Example scripts and demos

### Adding New API Endpoints

1. Create a new file in `app/api/v1/` (e.g., `bookings.py`)
2. Define your Pydantic models and routes
3. Include the router in `app/api/v1/__init__.py`
4. The endpoint will be available at `/api/v1/<your-endpoint>`

### Environment Variables

All configuration is managed through Pydantic Settings in `app/config.py`:

- **Required:**
  - `SERVICE_BUS_CONNECTION_STRING` - Azure Service Bus connection string
  - `SERVICE_BUS_QUEUE_NAME` - Queue name to receive messages from

- **Optional:**
  - `DB_CONNECTION_STRING` - Database connection (for future features)
  - `APP_NAME` - Application name (default: "azure-cloud-booking-service")
  - `APP_VERSION` - Application version (default: "0.1.0")
  - `DEBUG` - Enable debug mode (default: false)

## Next Steps

- [ ] Implement booking creation from Service Bus events
- [ ] Add more RESTful endpoints for users, pets, and bookings
- [ ] Implement authentication and authorization
- [ ] Add structured logging and monitoring
- [ ] Set up dead-letter queue handling
- [ ] Deploy to Azure Container Apps or App Service

## License

See [LICENSE](LICENSE) file.
