import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Link,
  Divider,
} from '@mui/material';
import {
  Login as LoginIcon,
  PersonAdd as RegisterIcon,
  LockReset as ResetIcon,
} from '@mui/icons-material';
import api from '../api';

export default function Login() {
  const [tabValue, setTabValue] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('patient');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError(false);

    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', res.data.token);
      setMessage('Login successful! Redirecting...');
      setError(false);

      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      console.error(err.response || err);
      setMessage(err.response?.data?.error || 'Login failed. Please try again.');
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError(false);

    // Validation
    if (password !== confirmPassword) {
      setMessage('Passwords do not match!');
      setError(true);
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setMessage('Password must be at least 6 characters!');
      setError(true);
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/auth/register', { 
        name, 
        email, 
        password, 
        role 
      });
      setMessage('Registration successful! You can now login.');
      setError(false);
      
      // Clear form
      setName('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      
      // Switch to login tab
      setTimeout(() => {
        setTabValue(0);
        setMessage('');
      }, 2000);
    } catch (err) {
      console.error(err.response || err);
      setMessage(err.response?.data?.error || 'Registration failed. Please try again.');
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError(false);

    if (!email) {
      setMessage('Please enter your email address first!');
      setError(true);
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/auth/forgot-password', { email });
      setMessage(res.data.message);
      setError(false);
      
      // Clear email after successful request
      if (res.data.message.includes('sent')) {
        setEmail('');
      }
    } catch (err) {
      console.error(err.response || err);
      setMessage(err.response?.data?.error || 'Error sending reset email. Please try again.');
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setMessage('');
    setError(false);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundImage: 'url(/dental_bg.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <Container maxWidth="sm">
        <Paper elevation={10} sx={{ p: 4, borderRadius: 2,backgroundColor: '#e3f2fd' }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
              🦷 Dental CRM
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {tabValue === 0 ? 'Book your appointment now! Please login to continue' : 
               tabValue === 1 ? 'Create your account' : 'Reset your password'}
            </Typography>
          </Box>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} centered>
              <Tab label="Login" icon={<LoginIcon />} />
              <Tab label="Register" icon={<RegisterIcon />} />
              <Tab label="Forgot Password" icon={<ResetIcon />} />
            </Tabs>
          </Box>

          {message && (
            <Alert severity={error ? 'error' : 'success'} sx={{ mb: 2 }}>
              {message}
            </Alert>
          )}

          {/* Login Tab */}
          {tabValue === 0 && (
            <form onSubmit={handleLogin}>
              <TextField
                fullWidth
                type="email"
                label="Email Address"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                sx={{ mb: 2 }}
                autoComplete="off"
              />

              <TextField
                fullWidth
                type="password"
                label="Password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                sx={{ mb: 3 }}
                autoComplete="current-password"
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <LoginIcon />}
                sx={{ py: 1.5 }}
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          )}

          {/* Register Tab */}
          {tabValue === 1 && (
            <form onSubmit={handleRegister}>
              <TextField
                fullWidth
                label="Full Name"
                variant="outlined"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                sx={{ mb: 2 }}
                autoComplete="name"
              />

              <TextField
                fullWidth
                type="email"
                label="Email Address"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                sx={{ mb: 2 }}
                autoComplete="email"
              />

              <TextField
                fullWidth
                select
                label="Role"
                variant="outlined"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                sx={{ mb: 2 }}
                SelectProps={{ native: true }}
              >
                <option value="patient">Patient</option>
                <option value="dentist">Dentist</option>
                <option value="admin">Admin</option>
              </TextField>

              <TextField
                fullWidth
                type="password"
                label="Password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                sx={{ mb: 2 }}
                autoComplete="new-password"
              />

              <TextField
                fullWidth
                type="password"
                label="Confirm Password"
                variant="outlined"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                sx={{ mb: 3 }}
                autoComplete="new-password"
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <RegisterIcon />}
                sx={{ py: 1.5 }}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </form>
          )}

          {/* Forgot Password Tab */}
          {tabValue === 2 && (
            <form onSubmit={handleForgotPassword}>
              <TextField
                fullWidth
                type="email"
                label="Email Address"
                variant="outlined"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                sx={{ mb: 3 }}
                autoComplete="email"
                placeholder="Enter your registered email"
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <ResetIcon />}
                sx={{ py: 1.5 }}
              >
                {loading ? 'Sending Reset Email...' : 'Send Reset Email'}
              </Button>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                We'll send you a password reset link if the email exists in our system.
              </Typography>
            </form>
          )}

          {/* Footer Links */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              {tabValue === 0 && (
                <>
                  Don't have an account?{' '}
                  <Link 
                    component="button" 
                    variant="body2" 
                    onClick={() => setTabValue(1)}
                    sx={{ textDecoration: 'underline' }}
                  >
                    Register here
                  </Link>
                  {' • '}
                  <Link 
                    component="button" 
                    variant="body2" 
                    onClick={() => setTabValue(2)}
                    sx={{ textDecoration: 'underline' }}
                  >
                    Forgot password?
                  </Link>
                </>
              )}
              {tabValue === 1 && (
                <>
                  Already have an account?{' '}
                  <Link 
                    component="button" 
                    variant="body2" 
                    onClick={() => setTabValue(0)}
                    sx={{ textDecoration: 'underline' }}
                  >
                    Login here
                  </Link>
                </>
              )}
              {tabValue === 2 && (
                <>
                  Remember your password?{' '}
                  <Link 
                    component="button" 
                    variant="body2" 
                    onClick={() => setTabValue(0)}
                    sx={{ textDecoration: 'underline' }}
                  >
                    Login here
                  </Link>
                </>
              )}
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}
