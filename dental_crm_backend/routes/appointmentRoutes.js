const express = require('express');
const db = require('../db/connection');
const verifyToken = require('../middleware/authMiddleware');
const { appointmentValidation } = require('../middleware/validators');

const router = express.Router();

/**
 * 🩺 GET: All appointments for the logged-in user
 */
router.get('/', verifyToken, (req, res) => {
  const userId = req.user.id;

  db.query('SELECT * FROM appointments WHERE user_id = ?', [userId], (err, results) => {
    if (err) {
      console.error('Database error:', err);
      return res.status(500).json({ error: 'Database error' });
    }

    res.json(results);
  });
});

/**
 * 🆕 POST: Create a new appointment
 */
router.post('/', verifyToken, appointmentValidation, (req, res) => {
  const userId = req.user.id;
  const { appointment_date, notes } = req.body;

  if (!appointment_date) {
    return res.status(400).json({ error: 'Appointment date is required.' });
  }

  db.query(
    'INSERT INTO appointments (user_id, appointment_date, notes, status) VALUES (?, ?, ?, ?)',
    [userId, appointment_date, notes || '', 'scheduled'],
    (err, result) => {
      if (err) {
        console.error('Database insert error:', err);
        return res.status(500).json({ error: 'Database insert error' });
      }

      res.status(201).json({
        message: 'Appointment created successfully ✅',
        appointmentId: result.insertId,
      });
    }
  );
});

/**
 * ✏️ PUT: Update an existing appointment
 */
router.put('/:id', verifyToken, (req, res) => {
  const userId = req.user.id;
  const { id } = req.params;
  const { appointment_date, status, notes } = req.body;

  // Validate input
  if (!appointment_date && !status && !notes) {
    return res.status(400).json({ error: 'No update fields provided.' });
  }

  db.query(
    'UPDATE appointments SET appointment_date = ?, status = ?, notes = ? WHERE id = ? AND user_id = ?',
    [appointment_date, status, notes, id, userId],
    (err, result) => {
      if (err) {
        console.error('Database update error:', err);
        return res.status(500).json({ error: 'Database update error' });
      }

      if (result.affectedRows === 0) {
        return res.status(404).json({ error: 'Appointment not found or unauthorized' });
      }

      res.json({ message: 'Appointment updated successfully ✅' });
    }
  );
});

/**
 * 🗑️ DELETE: Cancel or delete an appointment
 */
router.delete('/:id', verifyToken, (req, res) => {
  const userId = req.user.id;
  const { id } = req.params;

  db.query('DELETE FROM appointments WHERE id = ? AND user_id = ?', [id, userId], (err, result) => {
    if (err) {
      console.error('Database delete error:', err);
      return res.status(500).json({ error: 'Database delete error' });
    }

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Appointment not found or unauthorized' });
    }

    res.json({ message: 'Appointment deleted successfully 🗑️' });
  });
});

module.exports = router;
