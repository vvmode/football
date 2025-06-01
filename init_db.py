import psycopg2

conn = psycopg2.connect(
    dbname="mydb",
    user="admin",
    password="mypassword",
    host="dpg-xxxx.render.com",
    port="5432",
    sslmode="require"
)

cursor = conn.cursor()

# Create admin_users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    full_name TEXT,
    username TEXT
)
""")

conn.commit()
cursor.close()
conn.close()

print("✅ Table admin_users created successfully.")
