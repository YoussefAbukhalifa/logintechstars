from sqlalchemy import create_engine, text
from app import Base

# Use the same DATABASE_URL as in your app.py
DATABASE_URL = 'sqlite:///./techstars.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Create users table
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            national_id VARCHAR(20) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            reset_token VARCHAR(6),
            reset_token_expiry DATETIME
        )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_name ON users (name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_national_id ON users (national_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

if __name__ == "__main__":
    init_db()