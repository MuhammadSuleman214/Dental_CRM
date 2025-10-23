import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  CircularProgress,
  Fab,
  Drawer,
  AppBar,
  Toolbar,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Chat as ChatIcon,
  Close as CloseIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import axios from 'axios';

const CHATBOT_API_URL = process.env.REACT_APP_CHATBOT_URL || 'http://localhost:8000';

export default function Chatbot({ userId, userName }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize chat with welcome message
  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([
        {
          sender: 'bot',
          message: `Hello ${userName}! 👋 I'm your dental assistant. How can I help you today? I can help you schedule appointments, answer questions about our services, or provide general information.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }, [open, userName, messages.length]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      sender: 'user',
      message: inputMessage,
      timestamp: new Date().toISOString(),
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      console.log('Sending message to:', `${CHATBOT_API_URL}/api/chat`);
      console.log('Message data:', { message: inputMessage, user_id: userId, session_id: sessionId });
      
      // Send message to Python chatbot service
      const response = await axios.post(`${CHATBOT_API_URL}/api/chat`, {
        message: inputMessage,
        user_id: userId,
        session_id: sessionId,
      });

      console.log('Response received:', response.data);

      // Update session ID if new
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Add bot response to chat
      const botMessage = {
        sender: 'bot',
        message: response.data.response,
        timestamp: response.data.timestamp,
        appointmentData: response.data.appointment_data,
      };

      setMessages((prev) => [...prev, botMessage]);

      // Show notification if appointment was created
      if (response.data.appointment_data?.appointment_id) {
        console.log('Appointment created:', response.data.appointment_data);
        // You can add a toast notification here
      }
    } catch (error) {
      console.error('Detailed error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Error message:', error.message);
      
      const errorMessage = {
        sender: 'bot',
        message: `Debug: ${error.response?.data?.detail || error.message || "Connection error"}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!open && (
        <Fab
          color="primary"
          aria-label="chat"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            zIndex: 1000,
          }}
          onClick={() => setOpen(true)}
        >
          <ChatIcon />
        </Fab>
      )}

      {/* Chat Drawer */}
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{
          sx: {
            width: { xs: '100%', sm: 400 },
            maxWidth: '100%',
          },
        }}
      >
        {/* Chat Header */}
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <BotIcon sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Dental Assistant
            </Typography>
            <IconButton color="inherit" onClick={() => setOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Chat Messages */}
        <Box
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            p: 2,
            backgroundColor: '#f5f5f5',
            height: 'calc(100vh - 128px)',
          }}
        >
          {messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              {msg.sender === 'bot' && (
                <Avatar sx={{ bgcolor: 'primary.main', mr: 1 }}>
                  <BotIcon />
                </Avatar>
              )}

              <Paper
                elevation={1}
                sx={{
                  p: 1.5,
                  maxWidth: '75%',
                  backgroundColor: msg.sender === 'user' ? 'primary.main' : 'white',
                  color: msg.sender === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.message}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    mt: 0.5,
                    opacity: 0.7,
                    textAlign: 'right',
                  }}
                >
                  {formatTime(msg.timestamp)}
                </Typography>

                {/* Show appointment confirmation badge */}
                {msg.appointmentData?.appointment_id && (
                  <Box
                    sx={{
                      mt: 1,
                      p: 1,
                      backgroundColor: 'success.light',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                      ✓ Appointment Confirmed
                    </Typography>
                  </Box>
                )}
              </Paper>

              {msg.sender === 'user' && (
                <Avatar sx={{ bgcolor: 'secondary.main', ml: 1 }}>
                  <PersonIcon />
                </Avatar>
              )}
            </Box>
          ))}

          {/* Loading indicator */}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 1 }}>
                <BotIcon />
              </Avatar>
              <Paper elevation={1} sx={{ p: 1.5 }}>
                <CircularProgress size={20} />
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        {/* Message Input */}
        <Box
          sx={{
            p: 2,
            backgroundColor: 'white',
            borderTop: '1px solid #e0e0e0',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              size="small"
              multiline
              maxRows={3}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || loading}
              sx={{ ml: 1 }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Drawer>
    </>
  );
}

