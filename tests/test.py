from dotenv import load_dotenv
import os
load_dotenv()
DB_URL = os.getenv('DB_URL')
db_url = DB_URL.replace("postgresql://", "postgresql+asyncpg://") if DB_URL.startswith("postgresql://") else DB_URL
print(db_url)