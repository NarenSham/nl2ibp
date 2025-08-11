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

CREATE TABLE scenario (
    scenario_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scenario_overrides (
    override_id INTEGER PRIMARY KEY,
    scenario_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,  -- 'warehouses', 'retailers', 'routes'
    row_id INTEGER NOT NULL,   -- references primary key of baseline row
    column_name TEXT NOT NULL, -- e.g., 'demand', 'cost'
    override_value TEXT NOT NULL,
    FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id)
);

