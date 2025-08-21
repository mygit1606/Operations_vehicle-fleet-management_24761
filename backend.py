import psycopg2
import pandas as pd
from psycopg2 import sql

# --- Database Configuration ---
# Replace with your PostgreSQL credentials
DB_HOST = "localhost"
DB_NAME = "vehicle_fleet"
DB_USER = "postgres"
DB_PASSWORD = "Admin@0416"
DB_PORT = 5432

class Database:
    """
    This class handles all database operations for the Vehicle Fleet Management app.
    It connects to a PostgreSQL database and provides methods for CRUD operations.
    """
    def __init__(self):
        """
        Initializes the Database object and establishes a connection
        using the credentials defined at the top of the script.
        """
        self.conn = None
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
        except psycopg2.OperationalError as e:
            print(f"Error connecting to the database: {e}")
            self.conn = None

    # --- CREATE Operation ---
    def create_vehicle(self, vehicle_id, make, model, status, mileage, service_date):
        """Adds a new vehicle to the database."""
        if not self.conn: return False, "No database connection."
        try:
            with self.conn.cursor() as cur:
                query = sql.SQL("INSERT INTO vehicles (vehicle_id, make, model, status, current_mileage, last_service_date) VALUES (%s, %s, %s, %s, %s, %s)")
                cur.execute(query, (vehicle_id, make, model, status, mileage, service_date))
                self.conn.commit()
            return True, "Vehicle added successfully."
        except (Exception, psycopg2.Error) as error:
            self.conn.rollback()
            return False, f"Error creating vehicle: {error}"

    # --- READ Operations ---
    def get_vehicles(self, filter_by=None, filter_value=None, sort_by=None, sort_order='ASC'):
        """Retrieves a list of vehicles from the database."""
        if not self.conn: return pd.DataFrame()
        base_query = "SELECT vehicle_id, make, model, status, current_mileage, last_service_date FROM vehicles"
        query_parts = [sql.SQL(base_query)]
        params = []
        if filter_by and filter_value and filter_value != 'All':
            query_parts.append(sql.SQL("WHERE {field} = %s").format(field=sql.Identifier(filter_by)))
            params.append(filter_value)
        if sort_by:
            if sort_order.upper() not in ['ASC', 'DESC']: sort_order = 'ASC'
            query_parts.append(sql.SQL("ORDER BY {sort_field} {sort_order}").format(sort_field=sql.Identifier(sort_by), sort_order=sql.SQL(sort_order)))
        final_query = sql.SQL(' ').join(query_parts)
        try:
            df = pd.read_sql_query(final_query.as_string(self.conn), self.conn, params=params)
            return df
        except (Exception, psycopg2.Error) as error:
            print(f"Error fetching vehicles: {error}")
            return pd.DataFrame()
            
    def get_vehicle_by_id(self, vehicle_id):
        """Retrieves a single vehicle by its ID."""
        if not self.conn: return None
        try:
            query = "SELECT * FROM vehicles WHERE vehicle_id = %s"
            df = pd.read_sql_query(query, self.conn, params=(vehicle_id,))
            if not df.empty: return df.iloc[0]
            return None
        except (Exception, psycopg2.Error) as error:
            print(f"Error fetching vehicle by ID: {error}")
            return None

    def get_aggregation(self, agg_function, filter_by=None, filter_value=None):
        """Performs an aggregation (COUNT, AVG) on the vehicles table, with optional filtering."""
        if not self.conn: return 0
        if agg_function.upper() not in ['COUNT', 'AVG']: raise ValueError("Unsupported aggregation function")
        
        column = 'vehicle_id' if agg_function.upper() == 'COUNT' else 'current_mileage'
        base_query = "SELECT {agg}({col}) FROM vehicles"
        
        query_parts = [sql.SQL(base_query).format(agg=sql.SQL(agg_function), col=sql.Identifier(column))]
        params = []

        if filter_by and filter_value and filter_value != 'All':
            query_parts.append(sql.SQL("WHERE {field} = %s").format(field=sql.Identifier(filter_by)))
            params.append(filter_value)
            
        final_query = sql.SQL(' ').join(query_parts)

        try:
            with self.conn.cursor() as cur:
                cur.execute(final_query, params)
                result = cur.fetchone()[0]
                return result if result is not None else 0
        except (Exception, psycopg2.Error) as error:
            print(f"Error during aggregation {agg_function}: {error}")
            return 0
            
    def get_extreme_mileage_vehicle(self, extreme_type='MAX', filter_by=None, filter_value=None):
        """Finds the vehicle with the highest or lowest mileage, with optional filtering."""
        if not self.conn: return None
        order = 'DESC' if extreme_type.upper() == 'MAX' else 'ASC'
        
        base_query = "SELECT * FROM vehicles"
        query_parts = [sql.SQL(base_query)]
        params = []

        if filter_by and filter_value and filter_value != 'All':
            query_parts.append(sql.SQL("WHERE {field} = %s").format(field=sql.Identifier(filter_by)))
            params.append(filter_value)
            
        query_parts.append(sql.SQL("ORDER BY current_mileage {sort_order} LIMIT 1").format(sort_order=sql.SQL(order)))
        final_query = sql.SQL(' ').join(query_parts)

        try:
            df = pd.read_sql_query(final_query.as_string(self.conn), self.conn, params=params)
            if not df.empty: return df.iloc[0]
            return None
        except (Exception, psycopg2.Error) as error:
            print(f"Error fetching extreme mileage vehicle: {error}")
            return None

    # --- UPDATE Operation ---
    def update_vehicle(self, original_vehicle_id, make, model, status, mileage, service_date):
        """Updates an existing vehicle's details."""
        if not self.conn: return False, "No database connection."
        try:
            with self.conn.cursor() as cur:
                query = sql.SQL("UPDATE vehicles SET make = %s, model = %s, status = %s, current_mileage = %s, last_service_date = %s WHERE vehicle_id = %s")
                cur.execute(query, (make, model, status, mileage, service_date, original_vehicle_id))
                self.conn.commit()
            return True, "Vehicle updated successfully."
        except (Exception, psycopg2.Error) as error:
            self.conn.rollback()
            return False, f"Error updating vehicle: {error}"

    # --- DELETE Operation ---
    def delete_vehicle(self, vehicle_id):
        """Deletes a vehicle from the database."""
        if not self.conn: return False, "No database connection."
        try:
            with self.conn.cursor() as cur:
                query = sql.SQL("DELETE FROM vehicles WHERE vehicle_id = %s")
                cur.execute(query, (vehicle_id,))
                self.conn.commit()
            return True, "Vehicle deleted successfully."
        except (Exception, psycopg2.Error) as error:
            self.conn.rollback()
            return False, f"Error deleting vehicle: {error}"

    def __del__(self):
        """Destructor to close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
