const jwt = require('jsonwebtoken');
require('dotenv').config();

function verifyToken(req, res, next) {
  try {
    // Extract Authorization header (should be "Bearer <token>")
    const authHeader = req.headers['authorization'];

    if (!authHeader) {
      return res.status(401).json({ error: 'Access denied. No Authorization header provided.' });
    }

    // Ensure the header starts with "Bearer"
    if (!authHeader.startsWith('Bearer ')) {
      return res.status(400).json({ error: 'Malformed token. Expected format: Bearer <token>' });
    }

    // Extract token from header
    const token = authHeader.split(' ')[1];

    // Verify JWT token
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
      if (err) {
        console.error('❌ JWT verification failed:', err.message);
        return res.status(403).json({ error: 'Invalid or expired token' });
      }

      // Attach decoded user info to request
      req.user = user;
      next();
    });

  } catch (err) {
    console.error('🔥 Token verification error:', err);
    res.status(500).json({ error: 'Internal server error during authentication.' });
  }
}

module.exports = verifyToken;
