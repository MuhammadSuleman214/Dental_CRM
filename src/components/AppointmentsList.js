import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Grid,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import api from '../api';
import { format } from 'date-fns';

export default function AppointmentsList() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [formData, setFormData] = useState({
    appointment_date: '',
    notes: '',
    status: 'scheduled',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/appointments');
      setAppointments(response.data);
    } catch (err) {
      console.error('Error fetching appointments:', err);
      setError('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (appointment = null) => {
    if (appointment) {
      setEditingAppointment(appointment);
      setFormData({
        appointment_date: appointment.appointment_date,
        notes: appointment.notes || '',
        status: appointment.status || 'scheduled',
      });
    } else {
      setEditingAppointment(null);
      setFormData({
        appointment_date: '',
        notes: '',
        status: 'scheduled',
      });
    }
    setOpenDialog(true);
    setError('');
    setSuccess('');
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingAppointment(null);
    setFormData({ appointment_date: '', notes: '', status: 'scheduled' });
  };

  const handleSubmit = async () => {
    try {
      if (!formData.appointment_date) {
        setError('Please select a date and time');
        return;
      }

      if (editingAppointment) {
        // Update existing appointment
        await api.put(`/appointments/${editingAppointment.id}`, formData);
        setSuccess('Appointment updated successfully!');
      } else {
        // Create new appointment
        await api.post('/appointments', formData);
        setSuccess('Appointment created successfully!');
      }

      setTimeout(() => {
        handleCloseDialog();
        fetchAppointments();
        setSuccess('');
      }, 1500);
    } catch (err) {
      console.error('Error saving appointment:', err);
      setError(err.response?.data?.error || 'Failed to save appointment');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this appointment?')) {
      return;
    }

    try {
      await api.delete(`/appointments/${id}`);
      setSuccess('Appointment deleted successfully!');
      fetchAppointments();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Error deleting appointment:', err);
      setError('Failed to delete appointment');
      setTimeout(() => setError(''), 3000);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled':
        return 'primary';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'PPp');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center' }}>
          <CalendarIcon sx={{ mr: 1 }} />
          My Appointments
        </Typography>
        {/*<Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Book Appointment
        </Button>*/}
      </Box>

      {/* Success/Error Messages */}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Appointments List */}
      {appointments.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              No appointments scheduled. Book your first appointment!
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {appointments.map((appointment) => (
            <Grid item xs={12} md={6} key={appointment.id}>
              <Card elevation={2}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" color="primary">
                      📅 {formatDate(appointment.appointment_date)}
                    </Typography>
                    <Chip
                      label={appointment.status}
                      color={getStatusColor(appointment.status)}
                      size="small"
                    />
                  </Box>

                  {appointment.notes && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {appointment.notes}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleOpenDialog(appointment)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(appointment.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingAppointment ? 'Edit Appointment' : 'Book New Appointment'}
        </DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

          <TextField
            fullWidth
            label="Date & Time"
            type="datetime-local"
            value={formData.appointment_date}
            onChange={(e) => setFormData({ ...formData, appointment_date: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            fullWidth
            label="Notes / Reason for Visit"
            multiline
            rows={3}
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            sx={{ mb: 2 }}
            placeholder="e.g., Regular checkup, tooth pain, cleaning"
          />

          {editingAppointment && (
            <TextField
              fullWidth
              select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              SelectProps={{ native: true }}
            >
              <option value="scheduled">Scheduled</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </TextField>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingAppointment ? 'Update' : 'Book Appointment'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}




