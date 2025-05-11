import pyodbc
from datetime import datetime
from dotenv import load_dotenv
import os
import hashlib
import time
import re

load_dotenv()

class Database:
    def __init__(self):
        self.server = os.getenv('SQL_SERVER')
        self.database = os.getenv('SQL_DATABASE')
        self.driver = os.getenv('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.auth_type = os.getenv('SQL_AUTH', 'Windows')
        self.username = os.getenv('SQL_USERNAME')
        self.password = os.getenv('SQL_PASSWORD')
        
        self.conn = None
        self.connect_with_retry()
        self.create_tables()
        self.create_default_admin()
        self.max_document_size = 5 * 1024 * 1024  # 5MB limit

    def get_connection_string(self):
        if self.auth_type.lower() == 'windows':
            return f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'
        else:
            return f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};'

    def connect_with_retry(self, max_retries=3, retry_delay=5):
        for attempt in range(max_retries):
            try:
                self.conn = pyodbc.connect(self.get_connection_string())
                return True
            except pyodbc.Error as e:
                if attempt < max_retries - 1:
                    print(f"Connection failed (attempt {attempt + 1}), retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect after {max_retries} attempts")
                    raise e
        return False

    def check_connection(self):
        try:
            if self.conn is None:
                return False
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except pyodbc.Error:
            return False

    def reconnect(self):
        try:
            self.close()
            return self.connect_with_retry()
        except pyodbc.Error as e:
            print(f"Reconnection failed: {e}")
            return False

    def execute_with_reconnect(self, query, params=None, max_retries=2):
        for attempt in range(max_retries):
            try:
                if not self.check_connection():
                    self.reconnect()
                
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor
            except pyodbc.Error as e:
                if attempt < max_retries - 1:
                    print(f"Query failed (attempt {attempt + 1}), reconnecting...")
                    self.reconnect()
                else:
                    raise e
        return None

    def create_tables(self):
        try:
            cursor = self.execute_with_reconnect("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transactions' AND xtype='U')
            BEGIN
                CREATE TABLE transactions (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    registration_date DATETIME NOT NULL,
                    created_on DATETIME NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    description NVARCHAR(255) NOT NULL,
                    amount DECIMAL(18, 2) NOT NULL,
                    transaction_type VARCHAR(10) NOT NULL,
                    deleted BIT DEFAULT 0,
                    deleted_date DATETIME NULL,
                    created_by INT NULL,
                    deleted_by INT NULL,
                    document VARBINARY(MAX) NULL,
                    document_name NVARCHAR(255) NULL,
                    document_size INT NULL,
                    document_hash NVARCHAR(64) NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (deleted_by) REFERENCES users(id)
                )
            END
            """)
            self.conn.commit()
            
            cursor = self.execute_with_reconnect("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
            BEGIN
                CREATE TABLE users (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(50) NOT NULL UNIQUE,
                    password NVARCHAR(255) NOT NULL,
                    role NVARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
                    created_on DATETIME NOT NULL DEFAULT GETDATE(),
                    can_upload_documents BIT DEFAULT 0
                )
            END
            """)
            self.conn.commit()
        except pyodbc.Error as e:
            print(f"Error creating tables: {e}")

    def create_default_admin(self):
        try:
            cursor = self.execute_with_reconnect("SELECT 1 FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                cursor = self.execute_with_reconnect("""
                INSERT INTO users (username, password, role, can_upload_documents)
                VALUES (?, ?, ?, 1)
                """, ('admin', self.hash_password('admin123'), 'admin'))
                self.conn.commit()
        except Exception as e:
            print(f"Error creating default admin: {e}")

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def hash_document(document_data):
        return hashlib.sha256(document_data).hexdigest()

    @staticmethod
    def sanitize_filename(filename):
        if not filename:
            return filename
        filename = os.path.basename(filename)
        return re.sub(r'[^\w\-_.]', '', filename)

    def authenticate_user(self, username, password):
        try:
            cursor = self.execute_with_reconnect("""
            SELECT id, username, role, can_upload_documents FROM users 
            WHERE username = ? AND password = ?
            """, (username, self.hash_password(password)))
            return cursor.fetchone()
        except pyodbc.Error as e:
            print(f"Authentication error: {e}")
            return None

    def get_user_role(self, user_id):
        try:
            cursor = self.execute_with_reconnect("SELECT role FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except pyodbc.Error as e:
            print(f"Error getting user role: {e}")
            return None

    def can_user_upload_documents(self, user_id):
        try:
            cursor = self.execute_with_reconnect("SELECT can_upload_documents FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else False
        except pyodbc.Error as e:
            print(f"Error checking upload permissions: {e}")
            return False

    def add_transaction(self, date_str, currency, description, amount, transaction_type, user_id=None, document_data=None, document_name=None):
        try:
            if document_data and len(document_data) > self.max_document_size:
                raise ValueError(f"Document exceeds maximum size of {self.max_document_size} bytes")

            if document_name:
                document_name = self.sanitize_filename(document_name)

            registration_date = datetime.strptime(date_str, "%d-%m-%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        document_size = len(document_data) if document_data else None
        document_hash = self.hash_document(document_data) if document_data else None
    
        try:
            cursor = self.execute_with_reconnect("""
            INSERT INTO transactions 
            (registration_date, created_on, currency, description, amount, transaction_type, 
             created_by, document, document_name, document_size, document_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                registration_date, created_on, currency, description, amount, transaction_type,
                user_id, document_data, document_name, document_size, document_hash
            ))
        
            self.conn.commit()
            return True
        
        except pyodbc.Error as e:
            print(f"Database error adding transaction: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error adding transaction: {e}")
            self.conn.rollback()
            return False

    def get_transactions(self, include_deleted=False):
        try:
            if include_deleted:
                cursor = self.execute_with_reconnect("""
                SELECT id, registration_date, currency, description, amount, transaction_type,
                       document_name, document_size
                FROM transactions
                """)
            else:
                cursor = self.execute_with_reconnect("""
                SELECT id, registration_date, currency, description, amount, transaction_type,
                       document_name, document_size
                FROM transactions 
                WHERE deleted = 0
                """)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Error getting transactions: {e}")
            return []

    def get_document(self, transaction_id):
        try:
            cursor = self.execute_with_reconnect("""
            SELECT document, document_name, document_hash 
            FROM transactions 
            WHERE id = ? AND deleted = 0
            """, (transaction_id,))
            result = cursor.fetchone()
            if result:
                calculated_hash = self.hash_document(result[0])
                if calculated_hash == result[2]:
                    return result[0], result[1]
                else:
                    print("Document hash verification failed")
                    return None, None
            return None, None
        except pyodbc.Error as e:
            print(f"Error getting document: {e}")
            return None, None

    def soft_delete_transaction(self, transaction_id, user_id=None):
        try:
            cursor = self.execute_with_reconnect("""
            UPDATE transactions 
            SET deleted = 1, deleted_date = ?, deleted_by=?
            WHERE id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, transaction_id))
            self.conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error soft deleting transaction: {e}")
            return False

    def get_balances(self):
        try:
            cursor = self.execute_with_reconnect("""
            SELECT currency, 
                   CAST(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) AS FLOAT) as income,
                   CAST(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) AS FLOAT) as expense
            FROM transactions
            WHERE deleted = 0
            GROUP BY currency
            """)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Error getting balances: {e}")
            return []

    def get_filtered_transactions(self, from_date, to_date, desc_filter=None, currency_filter=None, type_filter=None):
        try:
            query = """
            SELECT t.id, t.registration_date, t.currency, t.description, 
               CAST(t.amount AS FLOAT) as amount, 
               t.transaction_type,
               u.username as created_by,
               u2.username as deleted_by,
               t.document_name,
               t.document_size
            FROM transactions t
            LEFT JOIN users u ON t.created_by = u.id
            LEFT JOIN users u2 ON t.deleted_by = u2.id
            WHERE t.deleted = 0
            AND t.registration_date BETWEEN ? AND ?
            """
            params = [from_date, to_date]
            
            if desc_filter:
                query += " AND LOWER(description) LIKE ?"
                params.append(f"%{desc_filter.lower()}%")
                
            if currency_filter and currency_filter != 'All':
                query += " AND currency = ?"
                params.append(currency_filter)
                
            if type_filter and type_filter != 'All':
                query += " AND transaction_type = ?"
                params.append(type_filter.lower())
                
            cursor = self.execute_with_reconnect(query, params)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Error getting filtered transactions: {e}")
            return []

    def create_user(self, username, password, role, can_upload=False):
        try:
            cursor = self.execute_with_reconnect("""
            INSERT INTO users (username, password, role, can_upload_documents)
            VALUES (?, ?, ?, ?)
            """, (username, self.hash_password(password), role, 1 if can_upload else 0))
            self.conn.commit()
            return True
        except pyodbc.IntegrityError:
            return False
        except pyodbc.Error as e:
            print(f"Error creating user: {e}")
            return False

    def change_password(self, user_id, new_password):
        try:
            cursor = self.execute_with_reconnect("""
            UPDATE users SET password = ? 
            WHERE id = ?
            """, (self.hash_password(new_password), user_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Error changing password: {e}")
            return False

    def change_upload_permission(self, user_id, can_upload):
        try:
            cursor = self.execute_with_reconnect("""
            UPDATE users SET can_upload_documents = ? 
            WHERE id = ?
            """, (1 if can_upload else 0, user_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Error changing upload permissions: {e}")
            return False

    def get_all_users(self):
        try:
            cursor = self.execute_with_reconnect("""
            SELECT id, username, role, can_upload_documents 
            FROM users 
            ORDER BY username
            """)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Error getting all users: {e}")
            return []

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except pyodbc.Error as e:
            print(f"Error closing connection: {e}")