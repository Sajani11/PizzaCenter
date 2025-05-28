-- Create database
CREATE DATABASE IF NOT EXISTS pizzadb;
USE pizzadb;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Pizzas table
CREATE TABLE IF NOT EXISTS pizzas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(6,2) NOT NULL
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pizza_id INT NOT NULL,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pizza_id) REFERENCES pizzas(id) ON DELETE CASCADE
);

 Insert default pizzas only if table is empty
INSERT INTO pizzas (name, description, price)
SELECT * FROM (
    SELECT 'Margherita', 'Classic tomato and cheese', 8.99 UNION ALL
    SELECT 'Pepperoni', 'Pepperoni and cheese', 10.49 UNION ALL
    SELECT 'Veggie Delight', 'Onions, peppers, mushrooms', 9.99
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM pizzas);
