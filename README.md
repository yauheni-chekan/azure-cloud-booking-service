# Azure Cloud Booking Service

A pet grooming booking service built with SQLAlchemy and Azure SQL Database.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Azure SQL Database instance

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

Edit `.env` with your Azure SQL connection string:

```
DB_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:your-server.database.windows.net,1433;Database=your-database;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

You can find this connection string in:
**Azure Portal → Your SQL Database → Settings → Connection strings → ODBC**

## Project Structure

```
azure-cloud-booking-service/
├── main.py              # Demo script
├── models/
│   ├── __init__.py      # Model exports
│   ├── base.py          # SQLAlchemy base class
│   ├── user.py          # User model
│   ├── pet.py           # Pet model
│   └── booking.py       # Booking model & status enum
├── service/
│   ├── __init__.py      # Service exports
│   └── database.py      # Database connection utilities
├── pyproject.toml       # Project dependencies
└── env_example          # Environment template
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

### Running the Demo

```bash
uv run python main.py
```

### Using in Your Code

```python
from models import User, Pet, Booking, BookingStatus
from service import DatabaseManager, create_engine_from_connection_string

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
from service import create_azure_sql_engine

engine = create_azure_sql_engine(
    server="your-server.database.windows.net",
    database="your-database",
    username="your-username",
    password="your-password",
)
```

## Azure SQL Setup

1. Create an Azure SQL Database in the Azure Portal
2. Configure firewall rules to allow your IP address:
   - Go to **SQL Server → Networking → Firewall rules**
   - Add your client IP
3. Copy the ODBC connection string from:
   - **SQL Database → Connection strings → ODBC**

## License

See [LICENSE](LICENSE) file.
