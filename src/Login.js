console.log("API URL:", process.env.REACT_APP_API_URL);

import React, { useState } from 'react';
import api from './api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', res.data.token);
      setMessage('Login successful ✅');
    } catch (err) {
      setMessage(err.response?.data?.error || 'Login failed ❌');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: 'auto', marginTop: 100 }}>
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ display: 'block', marginBottom: 10, width: '100%' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ display: 'block', marginBottom: 10, width: '100%' }}
        />
        <button type="submit">Login</button>
      </form>
      <p>{message}</p>
    </div>
  );
}
