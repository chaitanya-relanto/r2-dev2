'use client';

import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useTheme } from 'next-themes';
import { useMemo, useEffect, useState } from 'react';

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const theme = useMemo(() => {
    // Always use light theme on server-side to prevent hydration mismatch
    const mode = mounted && resolvedTheme === 'dark' ? 'dark' : 'light';
    return createTheme({
      palette: {
        mode,
      },
      typography: {
        fontFamily: 'var(--font-inter)',
      },
    });
  }, [resolvedTheme, mounted]);

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
} 