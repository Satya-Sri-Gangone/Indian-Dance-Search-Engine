-- Run this in MySQL Workbench (or `mysql -u root -p < schema.sql`)

CREATE DATABASE IF NOT EXISTS dance_search_db;
USE dance_search_db;

CREATE TABLE IF NOT EXISTS search_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    query_searched  VARCHAR(255) NOT NULL,
    result          TEXT,              -- stores the JSON result returned to the user
    date            DATE NOT NULL,
    timestamp       TIME NOT NULL
);