'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Box, Container, Paper, TextField, IconButton, Typography, List, ListItem, CircularProgress, AppBar, Toolbar } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

export default function ChatPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    if (!user && localStorage.getItem('user') === null) {
      router.push('/login');
    }
  }, [user, router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !user) return;

    const userMessage: Message = { text: inputValue, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const payload: { user_id: string; query: string; session_id?: string } = {
        user_id: user.user_id,
        query: inputValue,
      };
      if (sessionId) {
        payload.session_id = sessionId;
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      
      const res = await fetch(`${API_BASE_URL}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error('Failed to get a response from the agent.');
      }

      const data = await res.json();

      const botMessage: Message = { text: data.response, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);

      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (error) {
      const errorMessage: Message = { text: 'Sorry, something went wrong.', sender: 'bot' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Container maxWidth="lg" className="h-[calc(100vh-64px)] flex flex-col py-4">
      <Paper
        elevation={3}
        sx={{
          flex: '1 1 auto',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: '#f1f5f9', // More noticeable light gray background
          border: '1px solid #e2e8f0',
          '.dark &': {
            bgcolor: '#1e293b', // A dark slate color
            border: '1px solid #475569',
          },
        }}
      >
        <AppBar 
            position="static" 
            color="transparent" 
            elevation={2}
            sx={{
                bgcolor: '#ffffff',
                borderBottom: '2px solid #cbd5e1',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                '.dark &': {
                    bgcolor: '#334155',
                    borderBottom: '2px solid #475569',
                },
            }}
        >
            <Toolbar>
                <Typography 
                    variant="h6" 
                    className="flex-grow"
                    sx={{
                        color: 'text.primary',
                        fontWeight: 'bold'
                    }}
                >
                    AI Assistant
                </Typography>
            </Toolbar>
        </AppBar>
        <Box className="flex-grow p-4 overflow-y-auto relative">
          {/* Background Logo */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <Image
              src="/logo-background-removed.png"
              alt="R2-Dev2 Logo"
              width={600}
              height={600}
              className="opacity-[0.02] dark:opacity-[0.03]"
            />
          </div>
          
          <List className="relative z-10">
            {messages.map((msg, index) => (
              <ListItem
                key={index}
                disableGutters
                sx={{
                  display: 'flex',
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  my: 1,
                }}
              >
                <Paper
                  elevation={2}
                  className="fade-in"
                  sx={{
                    p: '12px 16px',
                    maxWidth: '75%',
                    borderRadius: '20px',
                    bgcolor: msg.sender === 'user' ? 'primary.main' : 'grey.100',
                    color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                    '.dark &': {
                        bgcolor: msg.sender === 'user' ? 'primary.main' : 'grey.800',
                    },
                    '& p': { margin: 0 },
                    '& strong': { fontWeight: 'bold' },
                    '& ul, & ol': { 
                        textAlign: 'left', 
                        paddingLeft: '20px',
                    },
                  }}
                >
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  ) : (
                    <Typography variant="body1">{msg.text}</Typography>
                  )}
                </Paper>
              </ListItem>
            ))}
            {isLoading && (
              <ListItem
                disableGutters
                sx={{
                  display: 'flex',
                  justifyContent: 'flex-start',
                  my: 1,
                }}
              >
                <Paper
                  elevation={2}
                  className="fade-in"
                  sx={{
                    p: '12px 16px',
                    maxWidth: '75%',
                    borderRadius: '20px',
                    bgcolor: 'grey.100',
                    '.dark &': {
                        bgcolor: 'grey.800',
                    },
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </Paper>
              </ListItem>
            )}
            <div ref={chatEndRef} />
          </List>
        </Box>
        <Box 
            component="form" 
            onSubmit={handleSendMessage} 
            className="p-4 flex items-center"
            sx={{
                bgcolor: '#ffffff',
                borderTop: '2px solid #cbd5e1',
                boxShadow: '0 -1px 3px rgba(0, 0, 0, 0.1)',
                '.dark &': {
                    bgcolor: '#334155',
                    borderTop: '2px solid #475569',
                },
            }}
        >
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            sx={{
                '& .MuiOutlinedInput-root': {
                    borderRadius: '20px',
                    bgcolor: '#e2e8f0',
                    border: '1px solid #cbd5e1',
                    '.dark &': {
                        bgcolor: '#1e293b',
                        border: '1px solid #475569',
                    },
                    '&.Mui-focused fieldset': {
                        borderColor: '#3b82f6',
                        borderWidth: '2px',
                    },
                    '&:hover fieldset': {
                        borderColor: '#64748b',
                    },
                },
            }}
          />
          <IconButton color="primary" type="submit" className="ml-2" disabled={isLoading}>
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>
    </Container>
  );
} 