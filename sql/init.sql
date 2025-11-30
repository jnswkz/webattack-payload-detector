
Create table USERS(
	userID char(5) primary key,
	userName varchar(50),
	fullName varchar(100),
	email varchar(100),
	password varchar(100),
	balance money
);

Create table PRODUCTS (
	productID char(5) primary key,
	productName varchar(50),
	productType varchar(50),
	price money,
	descriptions varchar(200),
	stock int
);

create table users_information (
	userID char(5) primary key,
	fullName varchar(50),
	address varchar(100),
	dateofbirth date,
	gender varchar(10),
	phone char(10)
);

create table credit_card (
	cardID varchar(10) primary key,
	userID char(5),
	cardNumber char(20),
	csc char(3)
);
create table user_promos (
	promoID char(10) primary key,
	userID char(5) primary key,
	promoCode varchar(20),
	producttype varchar(50),
	discount int,
	quantity int
);
INSERT INTO USERS (userID, userName, email, password, balance) VALUES
('00001', 'admin', 'admin@example.com', 'admin123', 10000),
('00002', 'john_doe', 'john@example.com', 'johnpass', 3000),
('00003', 'emma_w', 'emma@example.com', 'emmapass', 2500),
('00004', 'michael_s', 'michael@example.com', 'mikepass', 1800),
('00005', 'sarah_k', 'sarah@example.com', 'sarahpass', 1200),
('00006', 'david_p', 'david@example.com', 'davidpass', 900),
('00007', 'linda_m', 'linda@example.com', 'lindapass', 1500),
('00008', 'robert_b', 'robert@example.com', 'robpass', 2200),
('00009', 'julia_r', 'julia@example.com', 'juliapass', 800),
('00010', 'kevin_l', 'kevin@example.com', 'kevpass', 1600);
INSERT INTO PRODUCTS (productID, productName, price, producttype, descriptions, stock) VALUES
('P001', 'Acer Laptop', 15000, 'Electronics', 'Acer Aspire 5 laptop', 20),
('P002', 'iPhone 14', 25000, 'Electronics', 'Apple iPhone 14 smartphone', 15),
('P003', 'Mechanical Keyboard', 1200, 'Accessories', 'RGB backlit mechanical keyboard', 50),
('P004', 'Logitech Mouse', 800, 'Accessories', 'Gaming wireless mouse', 40),
('P005', 'Sony Headphones', 1500, 'Audio', 'Noise-cancelling headphones', 30),
('P006', 'Samsung Monitor', 3000, 'Electronics', '27-inch 144Hz monitor', 25),
('P007', 'JBL Speaker', 2000, 'Audio', 'Portable Bluetooth speaker', 35),
('P008', 'USB 64GB', 300, 'Accessories', 'High-speed USB 3.0 drive', 100),
('P009', 'Laptop Backpack', 500, 'Bag', 'Waterproof laptop backpack', 60),
('P010', 'Power Bank', 700, 'Accessories', '20,000mAh fast-charging power bank', 80);
INSERT INTO users_information (userID, fullName, address, dateofbirth, gender, phone) VALUES
('00001', 'Admin User', 'New York, USA', '1990-01-01', 'Male', '1111111111'),
('00002', 'John Doe', 'Los Angeles, USA', '1998-04-12', 'Male', '2222222222'),
('00003', 'Emma Watson', 'Chicago, USA', '1999-06-20', 'Female', '3333333333'),
('00004', 'Michael Scott', 'Scranton, USA', '1985-03-15', 'Male', '4444444444'),
('00005', 'Sarah Klein', 'Houston, USA', '2000-09-09', 'Female', '5555555555'),
('00006', 'David Park', 'Seattle, USA', '1997-02-18', 'Male', '6666666666'),
('00007', 'Linda Moore', 'Miami, USA', '1996-07-23', 'Female', '7777777777'),
('00008', 'Robert Brown', 'Dallas, USA', '1995-11-30', 'Male', '8888888888'),
('00009', 'Julia Rose', 'Boston, USA', '2001-12-03', 'Female', '9999999999'),
('00010', 'Kevin Lee', 'San Diego, USA', '1998-08-14', 'Male', '1010101010');
INSERT INTO credit_card (cardID, userID, cardNumber, csc) VALUES
('CARD001', '00001', '1111222233334444', '123'),
('CARD002', '00002', '2222333344445555', '234'),
('CARD003', '00003', '3333444455556666', '345'),
('CARD004', '00004', '4444555566667777', '456'),
('CARD005', '00005', '5555666677778888', '567'),
('CARD006', '00006', '6666777788889999', '678'),
('CARD007', '00007', '7777888899990000', '789'),
('CARD008', '00008', '8888999900001111', '890'),
('CARD009', '00009', '9999000011112222', '901'),
('CARD010', '00010', '0000111122223333', '012');

INSERT INTO user_promos (promoID, userID, promoCode, producttype, discount, quantity) VALUES
('PRM001', '00001', 'ADMIN10', 'Electronics', 10, 5),
('PRM002', '00002', 'SAVE5', 'Accessories', 5, 3),
('PRM003', '00003', 'AUDIO7', 'Audio', 7, 2),
('PRM004', '00004', 'ELEC8', 'Electronics', 8, 1),
('PRM005', '00005', 'BAG6', 'Bag', 6, 4),
('PRM006', '00006', 'ACC5', 'Accessories', 5, 2),
('PRM007', '00007', 'AUDIO10', 'Audio', 10, 3),
('PRM008', '00008', 'ELEC12', 'Electronics', 12, 1),
('PRM009', '00009', 'ACC4', 'Accessories', 4, 5),
('PRM010', '00010', 'AUDIO15', 'Audio', 15, 2);
INSERT INTO transactions (transactionID, userID, productID, quantity, totalprice) VALUES
('TRX0000001', '00001', 'P001', 1, 15000),
('TRX0000002', '00002', 'P003', 2, 2400),
('TRX0000003', '00003', 'P002', 1, 25000),
('TRX0000004', '00004', 'P004', 1, 800),
('TRX0000005', '00005', 'P005', 1, 1500),
('TRX0000006', '00006', 'P008', 3, 900),
('TRX0000007', '00007', 'P007', 1, 2000),
('TRX0000008', '00008', 'P010', 2, 1400),
('TRX0000009', '00009', 'P009', 1, 500),
('TRX0000010', '00010', 'P006', 1, 3000);

select * from users