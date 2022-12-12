INSERT INTO store (store_id, address, phone_number, operation_hours) VALUES (1,"123 Rivian Road","IL", 1234567890, 8);
INSERT INTO store (store_id, address, phone_number, operation_hours) VALUES (2,"456 Bruh Road","IL", 0987654321, 8);
INSERT INTO product (product_id, product_name, source_nation, UPC_code, standard_price) VALUES (1,'Pepsi', 'United States', 111111,'5');
INSERT INTO product (product_id, product_name, source_nation, UPC_code, standard_price) VALUES (2,'coke', 'China', 999999,'3');
INSERT INTO product_package (packaging_number, size, product_id) VALUES (1, 'L', 1);
INSERT INTO product_package (packaging_number, size, product_id) VALUES (2, 'S', 2);
INSERT INTO brand (brand_id, brand_name) VALUES (1,'coca');
INSERT INTO brand (brand_id, brand_name) VALUES (2,'fake');
INSERT INTO vendor (vendor_id, vendor_name) VALUES (1,'Pepsi');
INSERT INTO vendor (vendor_id, vendor_name) VALUES (2,'Fake');
INSERT INTO price (vendor_id, brand_id,product_id,sell_price) VALUES (1,1,1,3);
INSERT INTO price (vendor_id, brand_id,product_id,sell_price) VALUES (2,2,2,2);
INSERT INTO inventory_space (store_id, product_id, maximum_space, current_stock) VALUES (1,1, 25, 5);
INSERT INTO inventory_space (store_id, product_id, maximum_space, current_stock) VALUES (2,2, 30, 10);
INSERT INTO product_type (product_id, product_type) VALUES (1,"type1");
INSERT INTO product_type (product_id, product_type) VALUES (2,"type2");
INSERT INTO customers (customers_id, address, phone_number) VALUES (1,"123 Grad Road", 1234567890);
INSERT INTO customers (customers_id, address, phone_number) VALUES (2,"345 Brian Road", 8765432190);