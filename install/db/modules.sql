DROP DATABASE IF EXISTS exam_papers;
CREATE DATABASE exam_papers;
\c exam_papers

CREATE TABLE module_category(
    id      SERIAL PRIMARY KEY,
    name    TEXT,
    code    VARCHAR(5)
);

CREATE TABLE module(
    id          SERIAL PRIMARY KEY,
    name        TEXT,
    code        VARCHAR(10),
    category    INT REFERENCES module_category(id)
);

CREATE TABLE paper(
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10),
    module      INT REFERENCES module(id),
    name        TEXT,
    paper       TEXT,
    period      VARCHAR(30),
    sitting     TEXT,
    year_start  INT,
    year_stop   INT,
    link        TEXT
);