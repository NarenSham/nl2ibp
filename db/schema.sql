DROP TABLE IF EXISTS warehouses;
DROP TABLE IF EXISTS retailers;
DROP TABLE IF EXISTS routes;

CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);

CREATE TABLE retailers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    demand INTEGER,
    latitude REAL,
    longitude REAL
);

CREATE TABLE routes (
    id INTEGER PRIMARY KEY,
    warehouse_id INTEGER,
    retailer_id INTEGER,
    cost REAL,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (retailer_id) REFERENCES retailers(id)
);
