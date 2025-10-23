-- Additional tables for chatbot functionality
-- Run these SQL commands in your XAMPP phpMyAdmin or MySQL console

-- Chat Sessions Table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    started_at DATETIME NOT NULL,
    ended_at DATETIME,
    status ENUM('active', 'ended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_sessions (user_id, started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    sender ENUM('user', 'bot') NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_messages (session_id, timestamp),
    INDEX idx_sender (sender)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes to existing tables for better performance (if not already present)
ALTER TABLE users ADD INDEX IF NOT EXISTS idx_email (email);
ALTER TABLE users ADD INDEX IF NOT EXISTS idx_role (role);

ALTER TABLE appointments ADD INDEX IF NOT EXISTS idx_user_date (user_id, appointment_date);
ALTER TABLE appointments ADD INDEX IF NOT EXISTS idx_status (status);
ALTER TABLE appointments ADD INDEX IF NOT EXISTS idx_appointment_date (appointment_date);

-- Sample data for testing (optional)
-- Note: Make sure you have users table with at least one user before inserting test data

-- Insert a test chat session (replace user_id with actual user ID)
-- INSERT INTO chat_sessions (user_id, started_at, status) 
-- VALUES (1, NOW(), 'active');

-- Insert sample messages (replace session_id with actual session ID)
-- INSERT INTO chat_messages (session_id, sender, message, timestamp)
-- VALUES 
-- (1, 'user', 'Hello, I need to book an appointment', NOW()),
-- (1, 'bot', 'Hello! I would be happy to help you schedule an appointment. When would you like to come in?', NOW());

-- View to check recent chat activity
CREATE OR REPLACE VIEW recent_chat_activity AS
SELECT 
    cs.id as session_id,
    u.name as user_name,
    u.email as user_email,
    cs.started_at,
    cs.status,
    COUNT(cm.id) as message_count,
    MAX(cm.timestamp) as last_message_at
FROM chat_sessions cs
JOIN users u ON cs.user_id = u.id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY cs.id, u.name, u.email, cs.started_at, cs.status
ORDER BY cs.started_at DESC;

-- Query to check chatbot analytics
-- SELECT * FROM recent_chat_activity;




