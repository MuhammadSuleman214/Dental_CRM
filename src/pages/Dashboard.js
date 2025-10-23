import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  Paper,
  Avatar,
  CircularProgress,
} from '@mui/material';
import {
  Logout as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import api from '../api';
import Chatbot from '../components/Chatbot';
import AppointmentsList from '../components/AppointmentsList';

export default function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/');
        return;
      }

      try {
        const res = await api.get('/auth/me');
        setUserData(res.data);
      } catch (err) {
        console.error(err);
        localStorage.removeItem('token');
        navigate('/');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#e3f2fd' }}>
      {/* Header */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            🦷 Dental CRM
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              <PersonIcon />
            </Avatar>
            <Typography variant="body1">{userData?.name}</Typography>
            <Button
              color="inherit"
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {/* Welcome Section */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Welcome back, {userData?.name}! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Email: {userData?.email}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Role: {userData?.role}
          </Typography>
        </Paper>

        {/* Appointments Section */}
        <AppointmentsList />
      </Container>

      {/* Floating Chatbot */}
      {userData && (
        <Chatbot userId={userData.id} userName={userData.name} />
      )}
    </Box>
  );
}
