const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const axios = require('axios');
const db = require('../db/connection');
const { authLimiter } = require('../middleware/rateLimiter');
const { loginValidation, registerValidation } = require('../middleware/validators');
require('dotenv').config();

const router = express.Router();

// 🧩 REGISTER ENDPOINT (fully functional with validation)
router.post('/register', authLimiter, registerValidation, async (req, res) => {
  const { name, email, password, role } = req.body;

  try {
    // Check if user already exists
    db.query('SELECT * FROM users WHERE email = ?', [email], async (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }
      
      if (results.length > 0) {
        return res.status(400).json({ error: 'Email already registered. Please use a different email or try logging in.' });
      }

      // Hash password before saving
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash(password, salt);

      // Save user
      db.query(
        'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
        [name, email, hashedPassword, role || 'patient'],
        (err, result) => {
          if (err) {
            console.error('Database insert error:', err);
            return res.status(500).json({ error: 'Failed to create account. Please try again.' });
          }
          
          res.json({ 
            message: 'Account created successfully! You can now login.',
            userId: result.insertId,
            user: {
              name: name,
              email: email,
              role: role || 'patient'
            }
          });
        }
      );
    });
  } catch (err) {
    console.error('Registration error:', err);
    res.status(500).json({ error: 'Server error. Please try again.' });
  }
});

// 🧾 LOGIN ENDPOINT (Supports both hashed and plain-text passwords)
router.post('/login', authLimiter, loginValidation, (req, res) => {
  const { email, password } = req.body;

  db.query('SELECT * FROM users WHERE email = ?', [email], async (err, results) => {
    if (err) {
      console.error('Database error:', err);
      return res.status(500).json({ error: 'Database error' });
    }
    
    if (results.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const user = results[0];
    let isValidPassword = false;

    try {
      // Check if password is hashed (starts with $2b$)
      if (user.password_hash.startsWith('$2b$')) {
        // Compare hashed password
        isValidPassword = await bcrypt.compare(password, user.password_hash);
      } else {
        // Plain-text password (for existing users)
        isValidPassword = (password === user.password_hash);
      }

      if (!isValidPassword) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }

      // Generate JWT
      const token = jwt.sign(
        { id: user.id, role: user.role, name: user.name },
        process.env.JWT_SECRET,
        { expiresIn: '24h' } // Extended to 24 hours
      );

      res.json({ 
        message: 'Login successful ✅', 
        token,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role
        }
      });
    } catch (error) {
      console.error('Password comparison error:', error);
      res.status(500).json({ error: 'Authentication error' });
    }
  });
});

// 👤 GET CURRENT USER PROFILE
router.get('/me', (req, res) => {
  const authHeader = req.headers['authorization'];
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    db.query('SELECT id, name, email, role, created_at FROM users WHERE id = ?', [decoded.id], (err, results) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      if (results.length === 0) return res.status(404).json({ error: 'User not found' });
      
      res.json(results[0]);
    });
  } catch (err) {
    return res.status(403).json({ error: 'Invalid token' });
  }
});

// 🔑 FORGOT PASSWORD ENDPOINT
router.post('/forgot-password', async (req, res) => {
  const { email } = req.body;

  if (!email) return res.status(400).json({ error: 'Email is required' });

  try {
    // Check if user exists
    db.query('SELECT * FROM users WHERE email = ?', [email], async (err, results) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      
      if (results.length === 0) {
        // Don't reveal if email exists or not for security
        return res.json({ 
          message: 'If the email exists in our system, you will receive a password reset link.' 
        });
      }

      const user = results[0];
      
      // Generate a password reset token (expires in 1 hour)
      const resetToken = jwt.sign(
        { userId: user.id, email: user.email, type: 'password_reset' },
        process.env.JWT_SECRET,
        { expiresIn: '1h' }
      );

      try {
        // Call Python service to send password reset email
        const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';
        const emailResponse = await axios.post(`${pythonServiceUrl}/api/email/password-reset`, {
          email: user.email,
          user_name: user.name,
          reset_token: resetToken
        });

        if (emailResponse.data.message) {
          console.log('✅ Password reset email sent successfully');
          res.json({ 
            message: 'Password reset instructions have been sent to your email address.'
          });
        } else {
          console.log('❌ Failed to send password reset email:', emailResponse.data.error);
          res.json({ 
            message: 'Password reset instructions have been sent to your email address.',
            note: 'If you don\'t receive an email, please check your spam folder or contact support.'
          });
        }
      } catch (emailError) {
        console.error('❌ Error calling Python email service:', emailError.message);
        // Still return success message for security (don't reveal email service issues)
        res.json({ 
          message: 'Password reset instructions have been sent to your email address.',
          note: 'If you don\'t receive an email, please check your spam folder or contact support.'
        });
      }
    });
  } catch (error) {
    console.error('❌ Forgot password error:', error);
    res.status(500).json({ error: 'Server error. Please try again.' });
  }
});

// 💬 CHATBOT TOKEN ENDPOINT
router.get('/chatbot/token', (req, res) => {
  const { userId } = req.query;

  if (!userId) return res.status(400).json({ error: 'User ID required' });

  const shortLivedToken = jwt.sign({ userId }, process.env.JWT_SECRET, {
    expiresIn: '5m', // short-lived token for chatbot
  });

  res.json({ token: shortLivedToken });
});

module.exports = router;
