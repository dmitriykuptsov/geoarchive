CREATE TABLE users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,

    password_hash VARCHAR(255) NOT NULL,

    first_name VARCHAR(100),
    last_name VARCHAR(100),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
);

CREATE TABLE roles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(100) NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_roles_name (name)
);

CREATE TABLE deposits (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    country VARCHAR(100),
    region VARCHAR(255),

    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    status ENUM(
        'active',
        'inactive',
        'archived'
    ) NOT NULL DEFAULT 'active',

    visibility ENUM(
        'private',
        'group',
        'public'
    ) NOT NULL DEFAULT 'private',

    created_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (created_by)
        REFERENCES users(id),

    FULLTEXT INDEX ft_deposit_search (
        name,
        description
    )
);

CREATE TABLE attribute_definitions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(255) NOT NULL,

    data_type ENUM(
        'text',
        'integer',
        'decimal',
        'boolean',
        'date'
    ) NOT NULL,

    unit VARCHAR(100),

    PRIMARY KEY (id),

    UNIQUE KEY uq_attribute_name (name)
);

CREATE TABLE documents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    deposit_id BIGINT UNSIGNED NOT NULL,

    name VARCHAR(500) NOT NULL,

    original_filename VARCHAR(500),

    storage_path VARCHAR(1000) NOT NULL,

    mime_type VARCHAR(100),

    file_size BIGINT UNSIGNED,

    sha256 CHAR(64),

    uploaded_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (deposit_id)
        REFERENCES deposits(id),

    INDEX idx_documents_deposit (deposit_id)
);


CREATE TABLE document_text (
    document_id BIGINT UNSIGNED NOT NULL,

    extracted_text LONGTEXT,

    extraction_method ENUM(
        'text',
        'ocr',
        'mixed'
    ),

    extraction_status ENUM(
        'pending',
        'processing',
        'completed',
        'failed'
    ),

    extracted_at DATETIME,

    PRIMARY KEY (document_id),

    FOREIGN KEY (document_id)
        REFERENCES documents(id)
);


CREATE TABLE maps (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    deposit_id BIGINT UNSIGNED NOT NULL,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    image_path VARCHAR(1000) NOT NULL,

    mime_type VARCHAR(100),

    width INT UNSIGNED,
    height INT UNSIGNED,

    min_zoom TINYINT,
    max_zoom TINYINT,

    created_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (deposit_id)
        REFERENCES deposits(id)
        ON DELETE CASCADE,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
);

CREATE TABLE layers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    deposit_id BIGINT UNSIGNED NOT NULL,

    name VARCHAR(255) NOT NULL,

    layer_type ENUM(
        'vector',
        'raster',
        'tile'
    ) NOT NULL,

    feature_type ENUM(
        'borehole',
        'fault',
        'contour',
        'boundary',
        'polygon',
        'line',
        'point',
        'other'
    ),

    is_visible BOOLEAN NOT NULL DEFAULT TRUE,

    display_order INT NOT NULL DEFAULT 0,

    created_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (deposit_id)
        REFERENCES deposits(id)
        ON DELETE CASCADE
);


CREATE TABLE geometries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    layer_id BIGINT UNSIGNED NOT NULL,

    name VARCHAR(255),

    geometry GEOMETRY NOT NULL SRID 4326,

    properties JSON,

    created_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (layer_id)
        REFERENCES layers(id)
        ON DELETE CASCADE,

    SPATIAL INDEX idx_geometry (geometry)
);


CREATE TABLE access_groups (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    created_by BIGINT UNSIGNED NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    FOREIGN KEY (created_by)
        REFERENCES users(id)
);


CREATE TABLE group_members (
    group_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (group_id, user_id),

    FOREIGN KEY (group_id)
        REFERENCES access_groups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE TABLE deposit_access (
    deposit_id BIGINT UNSIGNED NOT NULL,

    group_id BIGINT UNSIGNED NOT NULL,

    permission ENUM(
        'read',
        'write',
        'admin'
    ) NOT NULL DEFAULT 'read',

    PRIMARY KEY (deposit_id, group_id),

    FOREIGN KEY (deposit_id)
        REFERENCES deposits(id)
        ON DELETE CASCADE,

    FOREIGN KEY (group_id)
        REFERENCES access_groups(id)
        ON DELETE CASCADE
);