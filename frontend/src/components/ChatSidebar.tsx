'use client';

import { useState } from 'react';
import { 
  Box, 
  Button, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemText, 
  CircularProgress, 
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography
} from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';

interface Session {
  session_id: string;
  title: string;
  created_at: string;
}

interface ChatSidebarProps {
  sessions: Session[];
  isLoading: boolean;
  onSessionSelect: (sessionId: string | null) => void;
  currentSessionId: string | null;
  onNewChat: () => void;
  onRenameSession: (sessionId: string, newTitle: string) => Promise<void>;
  onDeleteSession: (sessionId: string) => Promise<void>;
  isOpen: boolean;
  onToggle: () => void;
}

export default function ChatSidebar({
  sessions,
  isLoading,
  onSessionSelect,
  currentSessionId,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  isOpen,
  onToggle,
}: ChatSidebarProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [isActionLoading, setIsActionLoading] = useState(false);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, sessionId: string) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedSessionId(sessionId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRename = () => {
    const session = sessions.find(s => s.session_id === selectedSessionId);
    if (session) {
      setRenameValue(session.title);
      setRenameDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleDelete = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleRenameConfirm = async () => {
    if (!selectedSessionId || !renameValue.trim()) {
      setRenameDialogOpen(false);
      setSelectedSessionId(null);
      return;
    }

    setIsActionLoading(true);
    try {
      await onRenameSession(selectedSessionId, renameValue.trim());
      setRenameDialogOpen(false);
      setRenameValue('');
      setSelectedSessionId(null);
    } catch (error) {
      console.error('Failed to rename session:', error);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedSessionId) {
      console.error('No selectedSessionId for delete');
      return;
    }

    console.log('🔍 Starting delete for session:', selectedSessionId);
    setIsActionLoading(true);
    try {
      await onDeleteSession(selectedSessionId);
      console.log('✅ Delete completed successfully');
      setDeleteDialogOpen(false);
      setSelectedSessionId(null);
      
      // If the deleted session was currently selected, clear selection
      if (selectedSessionId === currentSessionId) {
        onSessionSelect(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleDialogClose = (dialogType: 'rename' | 'delete') => {
    if (isActionLoading) return;
    
    if (dialogType === 'rename') {
      setRenameDialogOpen(false);
      setRenameValue('');
    } else {
      setDeleteDialogOpen(false);
    }
    setSelectedSessionId(null);
  };

  const selectedSession = sessions.find(s => s.session_id === selectedSessionId);
  
  console.log('🔍 Delete dialog state:', { 
    deleteDialogOpen, 
    selectedSessionId, 
    selectedSession: selectedSession?.title,
    sessionsCount: sessions.length 
  });

  return (
    <>
      {/* Sidebar */}
      <Box
        sx={{
          position: 'fixed',
          top: 80, // Further increased to ensure no overlap with navbar
          left: 0,
          width: 280,
          height: 'calc(100vh - 80px)', // Adjusted to match the new top position
          transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.3s ease',
          zIndex: 1200,
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ p: 2 }}>
          <Button variant="outlined" fullWidth onClick={onNewChat}>
            + New Chat
          </Button>
        </Box>
        <Divider />
        <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List>
              {sessions.map((session) => (
                <ListItem key={session.session_id} disablePadding>
                  <ListItemButton
                    selected={session.session_id === currentSessionId}
                    onClick={() => onSessionSelect(session.session_id)}
                    sx={{ pr: 1 }}
                  >
                    <ListItemText
                      primary={session.title}
                      secondary={new Date(session.created_at).toLocaleString()}
                      primaryTypographyProps={{
                        style: {
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        },
                      }}
                      sx={{ pr: 1 }}
                    />
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, session.session_id)}
                      sx={{ ml: 'auto' }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Box>

      {/* Backdrop for mobile */}
      {isOpen && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 1100,
            display: { md: 'none' },
          }}
          onClick={onToggle}
        />
      )}

      {/* Kebab Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleRename}>
          Rename
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          Delete
        </MenuItem>
      </Menu>

      {/* Rename Dialog */}
      <Dialog 
        open={renameDialogOpen} 
        onClose={() => handleDialogClose('rename')}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Rename Chat Session</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Session Title"
            fullWidth
            variant="outlined"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            disabled={isActionLoading}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && renameValue.trim()) {
                handleRenameConfirm();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => handleDialogClose('rename')}
            disabled={isActionLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleRenameConfirm}
            disabled={isActionLoading || !renameValue.trim()}
            variant="contained"
          >
            {isActionLoading ? <CircularProgress size={20} /> : 'Rename'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => handleDialogClose('delete')}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Chat Session</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedSession?.title || 'this session'}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => handleDialogClose('delete')}
            disabled={isActionLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm}
            disabled={isActionLoading}
            variant="contained"
            color="error"
          >
            {isActionLoading ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
} 