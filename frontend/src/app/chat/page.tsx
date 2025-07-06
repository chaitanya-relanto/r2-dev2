'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Box, Container, Paper, TextField, IconButton, Typography, List, ListItem, CircularProgress, AppBar, Toolbar } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';
import { fetchSessions, fetchMessages, sendMessage, renameSession, deleteSession, getRecommendations } from '@/utils/api';
import ChatSidebar from '@/components/ChatSidebar';
import { Suspense } from 'react';

interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface Session {
  session_id: string;
  title: string;
  created_at: string;
}

interface Recommendation {
  suggestions: string[];
  session_id: string;
  status: string;
  duration_seconds: number;
}

function ChatPageContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isSessionsLoading, setIsSessionsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [isRecommendationsLoading, setIsRecommendationsLoading] = useState(false);
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

  // Handle session query parameter from URL
  useEffect(() => {
    const sessionParam = searchParams.get('session');
    if (sessionParam && user) {
      console.log('🔍 Loading session from URL parameter:', sessionParam);
      setCurrentSessionId(sessionParam);
    }
  }, [searchParams, user]);

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
              formattedMessages.push({ 
                text, 
                sender,
                timestamp: item.timestamp ? new Date(item.timestamp) : new Date()
              });
              console.log(`✅ Added ${sender} message (role-based):`, text);
            }
          } else if (item.user_message && item.assistant_message) {
            // Paired format with both user and assistant messages
            formattedMessages.push({ 
              text: item.user_message, 
              sender: 'user',
              timestamp: item.created_at ? new Date(item.created_at) : new Date()
            });
            formattedMessages.push({ 
              text: item.assistant_message, 
              sender: 'bot',
              timestamp: item.created_at ? new Date(item.created_at) : new Date()
            });
            console.log('✅ Added paired messages:', { user: item.user_message, bot: item.assistant_message });
          } else if (item.query && item.response) {
            // Query/response format
            formattedMessages.push({ 
              text: item.query, 
              sender: 'user',
              timestamp: item.created_at ? new Date(item.created_at) : new Date()
            });
            formattedMessages.push({ 
              text: item.response, 
              sender: 'bot',
              timestamp: item.created_at ? new Date(item.created_at) : new Date()
            });
            console.log('✅ Added query/response messages:', { user: item.query, bot: item.response });
          } else if (item.type || item.sender) {
            // Message with explicit type/sender
            const text = item.content || item.message || item.text;
            const sender = (item.type === 'user' || item.sender === 'user') ? 'user' : 'bot';
            if (text) {
              formattedMessages.push({ 
                text, 
                sender,
                timestamp: item.timestamp ? new Date(item.timestamp) : new Date()
              });
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
                formattedMessages.push({ 
                  text, 
                  sender,
                  timestamp: item.created_at ? new Date(item.created_at) : new Date()
                });
                console.log(`✅ Added ${sender} message (fallback):`, text);
              });
            }
          }
        });
        
        console.log('🔍 Final formatted messages:', formattedMessages);
        setMessages(formattedMessages);
      } catch (error) {
        console.error('❌ Error fetching messages:', error);
        setMessages([{ text: 'Failed to load chat history.', sender: 'bot', timestamp: new Date() }]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMessagesCb();
  }, [currentSessionId]);

  // Fetch recommendations when session changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!currentSessionId) {
        setRecommendations([]);
        return;
      }

      setIsRecommendationsLoading(true);
      try {
        const data = await getRecommendations(currentSessionId, 5);
        setRecommendations(data.suggestions || []);
        console.log('✅ Recommendations loaded:', data.suggestions);
      } catch (error) {
        console.error('❌ Error fetching recommendations:', error);
        setRecommendations([]);
      } finally {
        setIsRecommendationsLoading(false);
      }
    };

    fetchRecommendations();
  }, [currentSessionId]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !user) return;

    const userMessage: Message = { 
      text: inputValue, 
      sender: 'user',
      timestamp: new Date()
    };
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

      const botMessage: Message = { 
        text: data.response, 
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, botMessage]);

      if (data.session_id && !currentSessionId) {
        setCurrentSessionId(data.session_id);
        fetchSessionsCb(); // Re-fetch sessions to include the new one
      }
    } catch (error) {
      const errorMessage: Message = { 
        text: 'Sorry, something went wrong.', 
        sender: 'bot',
        timestamp: new Date()
      };
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

  const handleRecommendationClick = (suggestion: string) => {
    setInputValue(suggestion);
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
                        flexDirection: 'column',
                        alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
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
                        
                        {/* Timestamp */}
                        <Typography
                            variant="caption"
                            sx={{
                                mt: 0.5,
                                color: 'text.secondary',
                                fontSize: '0.75rem',
                                opacity: 0.7,
                            }}
                        >
                            {msg.timestamp.toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            })}
                        </Typography>
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
          
          {/* Recommended Actions */}
          {recommendations.length > 0 && (
            <Box className="px-4 py-2 border-t" sx={{
              bgcolor: '#f8fafc',
              borderTop: '1px solid #e2e8f0',
              '.dark &': {
                bgcolor: '#1e293b',
                borderTop: '1px solid #475569',
              },
            }}>
              <Typography variant="caption" sx={{ 
                color: 'text.secondary', 
                fontSize: '0.75rem',
                fontWeight: 'medium',
                mb: 1,
                display: 'block'
              }}>
                💡 Recommended Actions
              </Typography>
              <Box className="flex gap-2 overflow-x-auto pb-1" sx={{
                '&::-webkit-scrollbar': {
                  height: '4px',
                },
                '&::-webkit-scrollbar-track': {
                  background: 'transparent',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: '#cbd5e1',
                  borderRadius: '2px',
                  '.dark &': {
                    background: '#475569',
                  },
                },
              }}>
                {recommendations.map((suggestion, index) => (
                  <Box
                    key={index}
                    onClick={() => handleRecommendationClick(suggestion)}
                    className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-sm rounded-full px-4 py-2 cursor-pointer transition-colors whitespace-nowrap select-none"
                    sx={{
                      color: 'text.primary',
                      fontSize: '0.875rem',
                      fontWeight: 'medium',
                      '&:hover': {
                        transform: 'translateY(-1px)',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      },
                    }}
                  >
                    {suggestion}
                  </Box>
                ))}
              </Box>
            </Box>
          )}
          
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

export default function ChatPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ChatPageContent />
    </Suspense>
  );
} 