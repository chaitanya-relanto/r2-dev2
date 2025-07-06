'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Box, Container, Paper, TextField, IconButton, Typography, List, ListItem, CircularProgress, AppBar, Toolbar } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';
import { fetchSessions, fetchMessages, sendMessage, renameSession, deleteSession } from '@/utils/api';
import ChatSidebar from '@/components/ChatSidebar';

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

interface Session {
  session_id: string;
  title: string;
  created_at: string;
}

export default function ChatPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isSessionsLoading, setIsSessionsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const chatEndRef = useRef<null | HTMLDivElement>(null);

  const fetchSessionsCb = useCallback(async () => {
    if (!user) return;
    setIsSessionsLoading(true);
    try {
      const data = await fetchSessions(user.user_id);
      setSessions(data.sessions || []);
    } catch (error) {
      console.error(error);
      setSessions([]);
    } finally {
      setIsSessionsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchSessionsCb();
    }
  }, [user, fetchSessionsCb]);

  useEffect(() => {
    if (!user && localStorage.getItem('user') === null) {
      router.push('/login');
    }
  }, [user, router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const fetchMessagesCb = async () => {
      if (!currentSessionId) {
        setMessages([]);
        return;
      }

      setIsLoading(true);
      try {
        const data = await fetchMessages(currentSessionId);
        console.log('🔍 Raw API response for messages:', data);
        
        const messages = data.messages || data || [];
        console.log('🔍 Extracted messages array:', messages);
        
        const formattedMessages: Message[] = [];
        
        messages.forEach((item: any, index: number) => {
          console.log(`🔍 Processing message item ${index}:`, item);
          
          // Check different possible message structures
          if (item.role) {
            // OpenAI-style format with role
            const text = item.content || item.message || item.text;
            const sender = item.role === 'user' ? 'user' : 'bot';
            if (text) {
              formattedMessages.push({ text, sender });
              console.log(`✅ Added ${sender} message (role-based):`, text);
            }
          } else if (item.user_message && item.assistant_message) {
            // Paired format with both user and assistant messages
            formattedMessages.push({ text: item.user_message, sender: 'user' });
            formattedMessages.push({ text: item.assistant_message, sender: 'bot' });
            console.log('✅ Added paired messages:', { user: item.user_message, bot: item.assistant_message });
          } else if (item.query && item.response) {
            // Query/response format
            formattedMessages.push({ text: item.query, sender: 'user' });
            formattedMessages.push({ text: item.response, sender: 'bot' });
            console.log('✅ Added query/response messages:', { user: item.query, bot: item.response });
          } else if (item.type || item.sender) {
            // Message with explicit type/sender
            const text = item.content || item.message || item.text;
            const sender = (item.type === 'user' || item.sender === 'user') ? 'user' : 'bot';
            if (text) {
              formattedMessages.push({ text, sender });
              console.log(`✅ Added ${sender} message (type-based):`, text);
            }
          } else {
            // Fallback: try to extract any text content
            const possibleTexts = [
              item.user_message, item.query, item.user_query, item.message,
              item.assistant_message, item.response, item.assistant_response, item.bot_message,
              item.content, item.text
            ].filter(Boolean);
            
            if (possibleTexts.length > 0) {
              // If we have multiple texts, assume first is user, second is bot
              possibleTexts.forEach((text, i) => {
                const sender = i % 2 === 0 ? 'user' : 'bot';
                formattedMessages.push({ text, sender });
                console.log(`✅ Added ${sender} message (fallback):`, text);
              });
            }
          }
        });
        
        console.log('🔍 Final formatted messages:', formattedMessages);
        setMessages(formattedMessages);
      } catch (error) {
        console.error('❌ Error fetching messages:', error);
        setMessages([{ text: 'Failed to load chat history.', sender: 'bot' }]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMessagesCb();
  }, [currentSessionId]);

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
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }

      const data = await sendMessage(payload);

      const botMessage: Message = { text: data.response, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);

      if (data.session_id && !currentSessionId) {
        setCurrentSessionId(data.session_id);
        fetchSessionsCb(); // Re-fetch sessions to include the new one
      }
    } catch (error) {
      const errorMessage: Message = { text: 'Sorry, something went wrong.', sender: 'bot' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionSelect = (sessionId: string | null) => {
    setCurrentSessionId(sessionId);
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
  };

  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    await renameSession(sessionId, newTitle);
    await fetchSessionsCb(); // Refresh sessions list
  };

  const handleDeleteSession = async (sessionId: string) => {
    await deleteSession(sessionId);
    await fetchSessionsCb(); // Refresh sessions list
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)', position: 'relative' }}>
      <ChatSidebar 
        sessions={sessions}
        isLoading={isSessionsLoading}
        onSessionSelect={handleSessionSelect}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onRenameSession={handleRenameSession}
        onDeleteSession={handleDeleteSession}
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
      />
      <Box 
        sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          flexDirection: 'column',
          marginLeft: isSidebarOpen ? '280px' : '0',
          transition: 'margin-left 0.3s ease',
          width: isSidebarOpen ? 'calc(100% - 280px)' : '100%',
        }}
      >
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
            margin: 2,
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
                  <IconButton
                      onClick={toggleSidebar}
                      sx={{
                          mr: 2,
                          color: 'text.primary',
                      }}
                  >
                      <MenuIcon />
                  </IconButton>
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
            {messages.length === 0 && !isLoading ? (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <Image
                    src="/logo-background-removed.png"
                    alt="R2-Dev2 Logo"
                    width={600}
                    height={600}
                    className="opacity-[0.02] dark:opacity-[0.03]"
                    />
                </div>
            ) : (
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
            )}
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
                  },
              }}
            />
            <IconButton type="submit" color="primary" disabled={isLoading || !inputValue.trim()} sx={{ ml: 1 }}>
              <SendIcon />
            </IconButton>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
} 