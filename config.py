class Config:
    SECRET_KEY = 'password'  # Replace with your actual secret key
    MYSQL_HOST = 'bloodbank-db.clacek8ey7ty.us-east-1.rds.amazonaws.com'
    MYSQL_USER = 'admin'  # Your MySQL username
    MYSQL_PASSWORD = 'bloodbank12345'  # Your MySQL password
    MYSQL_DB = 'bloodbank-db'  # Your MySQL database name

    # Add a DB_CONFIG attribute to hold database connection parameters
    DB_CONFIG = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': MYSQL_DB
    }
