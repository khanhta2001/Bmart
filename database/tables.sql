DROP TABLE IF EXISTS store_price;
DROP TABLE IF EXISTS store;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS brand;
DROP TABLE IF EXISTS product_type;


CREATE TABLE store (
	store_id INT PRIMARY KEY,
    address VARCHAR(30),
    phone_number INT,
    operation_hours VARCHAR(30),
    inventory_space VARCHAR(30)
);

CREATE TABLE store_price (
	store_id INT,
    product_id INT,
    override_price INT,
    FOREIGN KEY (store_id) REFERENCES store(store_id)
);

CREATE TABLE product (
	product_id INT,
    source_nation VARCHAR(30),
    UPC_code INT,
    price INT,
    brand_id INT,
    size INT,
    package_color INT
);

CREATE TABLE brand (
	brand_id INT,
    product_id INT
);

CREATE TABLE product_type (
	product_id INT,
    type VARCHAR(30)
    
);

