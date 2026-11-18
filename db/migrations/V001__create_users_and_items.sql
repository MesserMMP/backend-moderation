CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    is_verified boolean NOT NULL DEFAULT false,
    violations_qty integer NOT NULL DEFAULT 0 CHECK (violations_qty >= 0)
);

CREATE TABLE items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id bigint NOT NULL REFERENCES users(id),
    name text NOT NULL CHECK (btrim(name) <> ''),
    description text NOT NULL CHECK (btrim(description) <> ''),
    category integer NOT NULL CHECK (category > 0),
    images_qty integer NOT NULL CHECK (images_qty >= 0)
);
