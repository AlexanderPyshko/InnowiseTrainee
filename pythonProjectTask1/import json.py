import json
import xml.etree.ElementTree as ET
import psycopg2
import argparse
from datetime import datetime, date
from psycopg2 import OperationalError, sql

# SQL schema and table creation
SQL_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS schematask1;

CREATE TABLE IF NOT EXISTS schematask1.rooms (
    id INT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS schematask1.students (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    birthday DATE,
    sex CHAR(1),
    room_id INT,
    FOREIGN KEY (room_id) REFERENCES schematask1.rooms(id)
);
"""

class Config:
    @staticmethod
    def load_config(config_file='config.json'):
        with open(config_file, 'r') as file:
            return json.load(file)

class Database:
    def __init__(self, host='localhost', database='postgres', user=None, password=None):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def create_connection(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("Connected to database successfully")
            return conn
        except OperationalError as e:
            print(f'Failed to connect to the database: {e}')
            return None

    def execute_query(self, query, params=()):
        conn = self.create_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
        except Exception as e:
            print(f'Query failed: {e}')
        finally:
            cursor.close()
            conn.close()

    def create_schema_and_tables(self):
        conn = self.create_connection()
        if conn is None:
            return

        cursor = conn.cursor()
        try:
            cursor.execute(SQL_SCHEMA)
            conn.commit()
            print("Schema and tables created successfully")
        except Exception as e:
            print(f'Failed to create schema and tables: {e}')
        finally:
            cursor.close()
            conn.close()

class FileLoader:
    @staticmethod
    def load_json(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

class DataFormatter:
    @staticmethod
    def format_as_json(data):
        def default(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')

        return json.dumps(data, default=default, indent=4)

    @staticmethod
    def format_as_xml(data):
        root = ET.Element("data")
        for key, value_list in data.items():
            category_elem = ET.SubElement(root, key)
            for item in value_list:
                item_elem = ET.SubElement(category_elem, "item")
                for k, v in item.items():
                    child = ET.SubElement(item_elem, k)
                    child.text = str(v)
        return ET.tostring(root, encoding='unicode')

class CommandLineInterface:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Process student and room data.')
        self.parser.add_argument('--config', type=str, required=True, help='Path to configuration file')
        self.parser.add_argument('--format', type=str, choices=['json', 'xml'], required=True, help='Output format')

    def run(self):
        args = self.parser.parse_args()
        config = Config.load_config(args.config)
        students_file = config['paths']['students']
        rooms_file = config['paths']['rooms']
        
        db = Database(
            host=config['database']['host'],
            database=config['database']['dbname'],
            user=config['database']['user'],
            password=config['database']['password']
        )
        
        db.create_schema_and_tables()
        self.load_data(db, students_file, rooms_file)
        self.retrieve_and_format_data(db, args.format)

    def load_data(self, db, students_file, rooms_file):
        conn = db.create_connection()
        if conn is None:
            print("Failed to connect to the database")
            return

        cursor = conn.cursor()
        try:
            # Load rooms
            rooms = FileLoader.load_json(rooms_file)
            for room in rooms:
                cursor.execute(
                    "INSERT INTO schematask1.rooms (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                    (room['id'], room['name'])
                )

            # Load students
            students = FileLoader.load_json(students_file)
            for student in students:
                cursor.execute(
                    """
                    INSERT INTO schematask1.students (id, name, birthday, sex, room_id) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        student['id'],
                        student['name'],
                        datetime.strptime(student['birthday'][:10], '%Y-%m-%d'),
                        student['sex'],
                        student['room']
                    )
                )

            conn.commit()
            print("Loaded data successfully")
        except Exception as e:
            print(f'Failed to load data: {e}')
        finally:
            cursor.close()
            conn.close()

    def retrieve_and_format_data(self, db, output_format):
        conn = db.create_connection()
        if conn is None:
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM schematask1.rooms")
            rooms = cursor.fetchall()

            cursor.execute("SELECT * FROM schematask1.students")
            students = cursor.fetchall()

            room_columns = [desc[0] for desc in cursor.description]
            room_data = [dict(zip(room_columns, row)) for row in rooms]

            student_columns = [desc[0] for desc in cursor.description]
            student_data = [dict(zip(student_columns, row)) for row in students]

            data = {
                'rooms': room_data,
                'students': student_data
            }

            if output_format == 'json':
                print(DataFormatter.format_as_json(data))
            elif output_format == 'xml':
                print(DataFormatter.format_as_xml(data))
        except Exception as e:
            print(f'Failed to retrieve data: {e}')
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    cli = CommandLineInterface()
    cli.run()