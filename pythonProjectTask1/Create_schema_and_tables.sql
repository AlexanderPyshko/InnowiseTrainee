CREATE SCHEMA IF NOT EXISTS schematask1;

-- USE schematask1;

DROP TABLE IF EXISTS students;

DROP TABLE IF EXISTS rooms CASCADE;

CREATE TABLE rooms (
    id INT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    birthday DATE,
    sex CHAR(1),
    room_id INT,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);