DROP TABLE IF EXISTS shipment_group;
DROP TABLE IF EXISTS shipment;
DROP TABLE IF EXISTS order_request;
DROP TABLE IF EXISTS inventory_space;
DROP TABLE IF EXISTS store_price;
DROP TABLE IF EXISTS store;
DROP TABLE IF EXISTS price;
DROP TABLE IF EXISTS product_type;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS customer_order;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS vendor;
DROP TABLE IF EXISTS brand;
DROP TABLE IF EXISTS product;

CREATE TABLE store (
	store_id INT PRIMARY KEY,
    address VARCHAR(30),
    phone_number INT,
    operation_hours INT
);

CREATE TABLE store_price (
	store_id INT,
    product_id INT,
    override_price INT,
    CONSTRAINT FOREIGN KEY (store_id) REFERENCES store(store_id),
    PRIMARY KEY (store_id, product_id)
);

CREATE TABLE product (
	product_id INT PRIMARY KEY,
    source_nation VARCHAR(30),
    UPC_code INT,
    standard_price INT,
    size VARCHAR(5),
    packaging_number INT
);

CREATE TABLE brand (
	brand_id INT PRIMARY KEY,
    product_id INT,
    CONSTRAINT FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE vendor (
	vendor_id INT PRIMARY KEY,
    vendor_name VARCHAR(50)
);

CREATE TABLE price (
	vendor_id INT,
    brand_id INT,
    product_id INT,
    sell_price INT,
	FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id),
	FOREIGN KEY (brand_id) REFERENCES brand(brand_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id),
    PRIMARY KEY (vendor_id, brand_id, product_id)
);

CREATE TABLE product_type (
	product_id INT PRIMARY KEY,
    product_type VARCHAR(30),
    CONSTRAINT FOREIGN KEY (product_id) REFERENCES product(product_id)
    
);

CREATE TABLE customers (
	customers_id INT PRIMARY KEY,
    address VARCHAR(45),
    phone_number INT
);

CREATE TABLE customer_order (
	order_id INT PRIMARY KEY,
    customers_id INT,
    order_type VARCHAR(45),
    store_id INT,
    whether_successful BOOL,
    FOREIGN KEY (customers_id) REFERENCES customers(customers_id)
);

CREATE TABLE items (
	item_id INT PRIMARY KEY,
    order_id INT,
    cost INT,
    FOREIGN KEY (order_id) REFERENCES customer_order(order_id)
);

CREATE TABLE inventory_space (
    product_id INT,
    store_id INT,
    maximum_space INT,
    current_stock INT,
    PRIMARY KEY (product_id, store_id),
    FOREIGN KEY (store_id) REFERENCES store(store_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE order_request (
	request_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT,
    vendor_id INT,
    order_time TIME,
    amount_requested INT,
    seen_or_not INT,
    total_cost INT,
    order_status INT,
    FOREIGN KEY (store_id) REFERENCES store(store_id),
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

CREATE TABLE shipment (
	expected_delivery_time TIME,
    delivery_time TIME,
    shipment_id INT,
    request_id INT,
    vendor_id INT,
    PRIMARY KEY (shipment_id),
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

CREATE TABLE shipment_group (
	shipment_id INT,
    request_id INT,
    FOREIGN KEY (shipment_id) REFERENCES shipment(shipment_id),
    FOREIGN KEY (request_id) REFERENCES order_request(request_id),
    PRIMARY KEY (shipment_id, request_id)
);



