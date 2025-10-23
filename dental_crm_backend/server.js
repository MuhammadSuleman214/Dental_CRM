require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const db = require('./db/connection');

// Import middleware
const { apiLimiter } = require('./middleware/rateLimiter');

// ✅ Debug message for startup
console.log("🟢 Starting Dental CRM Backend...");

// Import routes
const authRoutes = require('./routes/authRoutes');
const appointmentRoutes = require('./routes/appointmentRoutes');

const app = express();

// ✅ Security middleware
app.use(helmet()); // Adds various HTTP headers for security
app.use(cors()); // Enable CORS
app.use(express.json()); // Parse JSON bodies
app.use(morgan('dev')); // HTTP request logging

// ✅ Apply rate limiting to all routes
app.use('/api/', apiLimiter);

// ✅ Debug message to verify routes are registered
console.log("🔹 Registering routes...");

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/appointments', appointmentRoutes);

// ✅ Simple test route
app.get('/', (req, res) => {
  res.send('Dental CRM Backend Running ✅');
});

// ✅ DB test API
app.get('/api/users', (req, res) => {
  db.query('SELECT * FROM users', (err, results) => {
    if (err) {
      console.error("❌ Database error:", err);
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

// ✅ Debug middleware for all incoming requests (optional, helps with login issues)
app.use((req, res, next) => {
  console.log(`📌 Incoming Request: ${req.method} ${req.originalUrl}`);
  next();
});

// ✅ Catch-all route for undefined endpoints
app.use((req, res) => {
  res.status(404).json({ error: `Route not found: ${req.originalUrl}` });
});

// ✅ Ensure PORT has a default
const PORT = process.env.PORT || 5000;

// ✅ Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
