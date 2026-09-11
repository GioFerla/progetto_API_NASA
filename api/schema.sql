CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT NULL,
    link VARCHAR(1000) NULL,
    closed_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_events_closed_at (closed_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    link VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NULL,
    source_url VARCHAR(1000) NULL,
    link VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_categories (
    event_id VARCHAR(100) NOT NULL,
    category_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (event_id, category_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS event_sources (
    event_id VARCHAR(100) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    reference_url VARCHAR(1500) NULL,
    PRIMARY KEY (event_id, source_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS geometries (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL,
    observed_at DATETIME NOT NULL,
    geometry_type VARCHAR(30) NOT NULL,
    coordinates LONGTEXT NOT NULL CHECK (JSON_VALID(coordinates)),
    longitude DECIMAL(10, 7) NULL,
    latitude DECIMAL(10, 7) NULL,
    bbox_min_longitude DECIMAL(10, 7) NULL,
    bbox_min_latitude DECIMAL(10, 7) NULL,
    bbox_max_longitude DECIMAL(10, 7) NULL,
    bbox_max_latitude DECIMAL(10, 7) NULL,
    magnitude_value DECIMAL(15, 5) NULL,
    magnitude_unit VARCHAR(100) NULL,
    magnitude_description VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_geometries_event (event_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    status VARCHAR(20) NOT NULL,
    records_received INT NOT NULL DEFAULT 0,
    records_created INT NOT NULL DEFAULT 0,
    records_updated INT NOT NULL DEFAULT 0,
    error_message TEXT NULL
);
