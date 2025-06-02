-- Create database
CREATE DATABASE IF NOT EXISTS pizzadb;
USE pizzadb;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(300) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Pizzas table (with image path and type)
CREATE TABLE IF NOT EXISTS pizzas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(6,2) NOT NULL,
    image_path VARCHAR(255),
    image_type ENUM('url', 'local') DEFAULT 'local'
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pizza_id INT NOT NULL,
    quantity INT DEFAULT 1,
    total_price DECIMAL(8,2),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pizza_id) REFERENCES pizzas(id) ON DELETE CASCADE
);

-- Insert default pizzas if none exist
INSERT INTO pizzas (name, description, price, image_path, image_type)
SELECT * FROM (
    SELECT 'Margherita', 'Classic tomato and cheese', 899, 'pizza_images/margherita.jpg', 'local' UNION ALL
    SELECT 'Pepperoni', 'Pepperoni and cheese', 1009, 'https://cdn.example.com/images/pepperoni.jpg', 'url' UNION ALL
    SELECT 'Veggie Delight', 'Onions, peppers, mushrooms', 999, 'pizza_images/veggie.jpg', 'local' UNION ALL
    SELECT 'BBQ Chicken', 'BBQ chicken, onions, cheese', 1149, 'pizza_images/BBQ Chicken Pizza.jpg', 'url'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM pizzas);
