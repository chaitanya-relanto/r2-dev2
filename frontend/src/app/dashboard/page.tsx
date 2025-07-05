'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getApiBaseUrl } from '@/utils/api';

interface TicketSummary {
  open: number;
  inProgress: number;
  closed: number;
}

interface PullRequest {
  id: string;
  title: string;
  ticketId: string;
  summary: string;
}

interface Doc {
  id: string;
  title: string;
  description: string;
}

interface Learning {
  id: string;
  title: string;
  description: string;
  tags: string[];
}

interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: string;
  // Add other fields as needed based on the API response
}

interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  project_id: string;
  project_name: string;
  assigned_to: string;
}

interface PRDetails {
  id: string;
  title: string;
  description: string;
  summary: string;
  ticketId: string;
  status: string;
  created_at: string;
  updated_at: string;
  author: string;
  // Add other fields as needed based on the API response
}

interface DocDetails {
  id: string;
  title: string;
  description: string;
  content: string;
  created_at: string;
  updated_at: string;
  // Add other fields as needed based on the API response
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { theme, resolvedTheme } = useTheme();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [ticketSummary, setTicketSummary] = useState<TicketSummary>({ open: 0, inProgress: 0, closed: 0 });
  const [recentPRs, setRecentPRs] = useState<PullRequest[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [learnings, setLearnings] = useState<Learning[]>([]);
  const [activeTab, setActiveTab] = useState<'docs' | 'learnings'>('docs');
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [selectedTicketType, setSelectedTicketType] = useState<'open' | 'inProgress' | 'closed' | null>(null);
  const [modalTickets, setModalTickets] = useState<Ticket[]>([]);
  const [showPRModal, setShowPRModal] = useState(false);
  const [selectedPR, setSelectedPR] = useState<PRDetails | null>(null);
  const [showDocModal, setShowDocModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocDetails | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Debug theme changes
  useEffect(() => {
    console.log('Dashboard theme changed:', { theme, resolvedTheme });
  }, [theme, resolvedTheme]);

  useEffect(() => {
    if (!user && localStorage.getItem('user') === null) {
      router.push('/login');
    }
  }, [user, router]);

  useEffect(() => {
    if (user && mounted) {
      fetchDashboardData();
    }
  }, [user, mounted]);

  const fetchDashboardData = async () => {
    if (!user) return;

    try {
      const API_BASE_URL = getApiBaseUrl();
      
      // Debug: Log the user object and API URL
      console.log('🔍 Current user object:', user);
      console.log('🔍 API URL:', `${API_BASE_URL}/data/users/${user.user_id}/info`);
      
      // Fetch user info from the API
      const userResponse = await fetch(`${API_BASE_URL}/data/users/${user.user_id}/info`);
      
      // Debug: Log response status
      console.log('🔍 API Response status:', userResponse.status);
      console.log('🔍 API Response ok:', userResponse.ok);
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        console.log('✅ API Response data:', userData);
        setUserInfo(userData);
      } else {
        const errorText = await userResponse.text();
        console.error('❌ Failed to fetch user info. Status:', userResponse.status);
        console.error('❌ Error response:', errorText);
        
        // Fallback to current user data if API fails
        setUserInfo({
          id: user.user_id,
          name: user.email, // Fallback to email if name not available
          email: user.email,
          role: user.role
        });
      }

      // Fetch ticket data from actual APIs
      console.log('🔍 Fetching ticket data...');
      
      // Fetch tickets in parallel
      const [openTicketsResponse, inProgressTicketsResponse, closedTicketsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/data/users/${user.user_id}/tickets/open`),
        fetch(`${API_BASE_URL}/data/users/${user.user_id}/tickets/in-progress`),
        fetch(`${API_BASE_URL}/data/users/${user.user_id}/tickets/closed`)
      ]);

      // Process ticket responses
      let openCount = 0, inProgressCount = 0, closedCount = 0;

      if (openTicketsResponse.ok) {
        const openTickets = await openTicketsResponse.json();
        console.log('🔍 Open tickets response:', openTickets);
        openCount = Array.isArray(openTickets) ? openTickets.length : 0;
        console.log('✅ Open tickets count:', openCount);
      } else {
        const errorText = await openTicketsResponse.text();
        console.error('❌ Failed to fetch open tickets:', openTicketsResponse.status, errorText);
      }

      if (inProgressTicketsResponse.ok) {
        const inProgressTickets = await inProgressTicketsResponse.json();
        console.log('🔍 In-progress tickets response:', inProgressTickets);
        inProgressCount = Array.isArray(inProgressTickets) ? inProgressTickets.length : 0;
        console.log('✅ In-progress tickets count:', inProgressCount);
      } else {
        const errorText = await inProgressTicketsResponse.text();
        console.error('❌ Failed to fetch in-progress tickets:', inProgressTicketsResponse.status, errorText);
      }

      if (closedTicketsResponse.ok) {
        const closedTickets = await closedTicketsResponse.json();
        console.log('🔍 Closed tickets response:', closedTickets);
        closedCount = Array.isArray(closedTickets) ? closedTickets.length : 0;
        console.log('✅ Closed tickets count:', closedCount);
      } else {
        const errorText = await closedTicketsResponse.text();
        console.error('❌ Failed to fetch closed tickets:', closedTicketsResponse.status, errorText);
      }

      // Set ticket summary with real data
      setTicketSummary({
        open: openCount,
        inProgress: inProgressCount,
        closed: closedCount
      });

      // Fetch recent PRs from tickets (get all tickets first, then get PRs for recent ones)
      console.log('🔍 Fetching recent PRs...');
      try {
        const allTicketsResponse = await fetch(`${API_BASE_URL}/data/users/${user.user_id}/tickets`);
        if (allTicketsResponse.ok) {
          const allTickets = await allTicketsResponse.json();
          console.log('🔍 All tickets response:', allTickets);
          const recentTickets = Array.isArray(allTickets) ? allTickets.slice(0, 3) : [];
          
          // Fetch PRs for recent tickets
          const prPromises = recentTickets.map(async (ticket: any) => {
            try {
              const prResponse = await fetch(`${API_BASE_URL}/data/tickets/${ticket.id}/pull-requests`);
              if (prResponse.ok) {
                const prs = await prResponse.json();
                console.log(`🔍 PRs for ticket ${ticket.id}:`, prs);
                return Array.isArray(prs) ? prs.map((pr: any) => ({
                  id: pr.id,
                  title: pr.title || `PR for ${ticket.title}`,
                  ticketId: ticket.id,
                  summary: pr.summary || pr.description || 'No summary available'
                })) : [];
              }
            } catch (error) {
              console.error(`Error fetching PRs for ticket ${ticket.id}:`, error);
            }
            return [];
          });
          
          const prResults = await Promise.all(prPromises);
          const flatPRs = prResults.flat().slice(0, 3); // Get first 3 PRs
          setRecentPRs(flatPRs);
          console.log('✅ Recent PRs:', flatPRs.length);
        } else {
          const errorText = await allTicketsResponse.text();
          console.error('❌ Failed to fetch tickets for PRs:', allTicketsResponse.status, errorText);
          setRecentPRs([]); // Set empty array if API fails
        }
      } catch (error) {
        console.error('❌ Error fetching recent PRs:', error);
        setRecentPRs([]); // Set empty array if error occurs
      }

      // Fetch docs from API
      console.log('🔍 Fetching documentation...');
      try {
        const docsResponse = await fetch(`${API_BASE_URL}/data/docs`);
        if (docsResponse.ok) {
          const docsData = await docsResponse.json();
          console.log('🔍 Docs response:', docsData);
          const formattedDocs = Array.isArray(docsData) ? docsData.map((doc: any) => ({
            id: doc.id,
            title: doc.title || 'Untitled Document',
            description: doc.description || doc.summary || 'No description available'
          })) : [];
          setDocs(formattedDocs);
          console.log('✅ Documentation loaded:', formattedDocs.length);
        } else {
          const errorText = await docsResponse.text();
          console.error('❌ Failed to fetch docs:', docsResponse.status, errorText);
          setDocs([]); // Set empty array if API fails
        }
      } catch (error) {
        console.error('❌ Error fetching docs:', error);
        setDocs([]); // Set empty array if error occurs
      }

      // Fetch learning resources from API
      console.log('🔍 Fetching learning resources...');
      try {
        const learningResponse = await fetch(`${API_BASE_URL}/data/learning`);
        if (learningResponse.ok) {
          const learningData = await learningResponse.json();
          console.log('🔍 Learning response:', learningData);
          const formattedLearning = Array.isArray(learningData) ? learningData.map((learning: any) => ({
            id: learning.id,
            title: learning.title || 'Untitled Resource',
            description: learning.description || learning.summary || 'No description available',
            tags: Array.isArray(learning.tags) ? learning.tags : (learning.tag ? [learning.tag] : [])
          })) : [];
          setLearnings(formattedLearning);
          console.log('✅ Learning resources loaded:', formattedLearning.length);
        } else {
          const errorText = await learningResponse.text();
          console.error('❌ Failed to fetch learning resources:', learningResponse.status, errorText);
          setLearnings([]); // Set empty array if API fails
        }
      } catch (error) {
        console.error('❌ Error fetching learning resources:', error);
        setLearnings([]); // Set empty array if error occurs
      }

    } catch (error) {
      console.error('💥 Error fetching dashboard data:', error);
      console.error('💥 Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace'
      });
      
      // Set fallback user info if everything fails
      if (!userInfo) {
        console.log('🔄 Setting fallback user info');
        setUserInfo({
          id: user.user_id,
          name: user.email || 'User',
          email: user.email || '',
          role: user.role || 'User'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewTickets = async (ticketType: 'open' | 'inProgress' | 'closed') => {
    if (!user) return;
    
    setSelectedTicketType(ticketType);
    setShowTicketModal(true);
    
    try {
      const API_BASE_URL = getApiBaseUrl();
      let endpoint = '';
      
      switch (ticketType) {
        case 'open':
          endpoint = `/data/users/${user.user_id}/tickets/open`;
          break;
        case 'inProgress':
          endpoint = `/data/users/${user.user_id}/tickets/in-progress`;
          break;
        case 'closed':
          endpoint = `/data/users/${user.user_id}/tickets/closed`;
          break;
      }
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      if (response.ok) {
        const tickets = await response.json();
        setModalTickets(Array.isArray(tickets) ? tickets : []);
      } else {
        console.error('Failed to fetch tickets for modal:', response.status);
        setModalTickets([]);
      }
    } catch (error) {
      console.error('Error fetching tickets for modal:', error);
      setModalTickets([]);
    }
  };

  const handleViewAllTickets = async () => {
    if (!user) return;
    
    setSelectedTicketType(null); // Set to null to indicate "all tickets"
    setShowTicketModal(true);
    
    try {
      const API_BASE_URL = getApiBaseUrl();
      
      // Fetch all tickets
      const response = await fetch(`${API_BASE_URL}/data/users/${user.user_id}/tickets`);
      if (response.ok) {
        const tickets = await response.json();
        setModalTickets(Array.isArray(tickets) ? tickets : []);
      } else {
        console.error('Failed to fetch all tickets:', response.status);
        setModalTickets([]);
      }
    } catch (error) {
      console.error('Error fetching all tickets:', error);
      setModalTickets([]);
    }
  };

  const handleViewPR = async (prId: string, ticketId: string) => {
    try {
      const API_BASE_URL = getApiBaseUrl();
      
      // Try to get PR details with diff/summary
      const prResponse = await fetch(`${API_BASE_URL}/data/pull-requests/${prId}/diff`);
      
      if (prResponse.ok) {
        const prDetails = await prResponse.json();
        console.log('🔍 PR Details:', prDetails);
        
        // Find the original PR data from recentPRs
        const originalPR = recentPRs.find(pr => pr.id === prId);
        
        setSelectedPR({
          id: prId,
          title: originalPR?.title || prDetails.title || 'Unknown PR',
          description: prDetails.description || originalPR?.summary || 'No description available',
          summary: prDetails.summary || prDetails.ai_summary || originalPR?.summary || 'No summary available',
          ticketId: ticketId,
          status: prDetails.status || 'Unknown',
          created_at: prDetails.created_at || '',
          updated_at: prDetails.updated_at || '',
          author: prDetails.author || prDetails.created_by || 'Unknown'
        });
        
        setShowPRModal(true);
      } else {
        console.error('Failed to fetch PR details:', prResponse.status);
        // Fallback: show basic info from recentPRs
        const originalPR = recentPRs.find(pr => pr.id === prId);
        if (originalPR) {
          setSelectedPR({
            id: prId,
            title: originalPR.title,
            description: originalPR.summary,
            summary: originalPR.summary,
            ticketId: ticketId,
            status: 'Unknown',
            created_at: '',
            updated_at: '',
            author: 'Unknown'
          });
          setShowPRModal(true);
        }
      }
    } catch (error) {
      console.error('Error fetching PR details:', error);
      // Fallback: show basic info from recentPRs
      const originalPR = recentPRs.find(pr => pr.id === prId);
      if (originalPR) {
        setSelectedPR({
          id: prId,
          title: originalPR.title,
          description: originalPR.summary,
          summary: originalPR.summary,
          ticketId: ticketId,
          status: 'Unknown',
          created_at: '',
          updated_at: '',
          author: 'Unknown'
        });
        setShowPRModal(true);
      }
    }
  };

  const handleViewDoc = async (docId: string) => {
    try {
      const API_BASE_URL = getApiBaseUrl();
      
      // Fetch document details
      const docResponse = await fetch(`${API_BASE_URL}/data/docs/${docId}`);
      
      if (docResponse.ok) {
        const docDetails = await docResponse.json();
        console.log('🔍 Doc Details:', docDetails);
        
        setSelectedDoc({
          id: docId,
          title: docDetails.title || 'Unknown Document',
          description: docDetails.description || docDetails.summary || 'No description available',
          content: docDetails.content || docDetails.body || 'No content available',
          created_at: docDetails.created_at || '',
          updated_at: docDetails.updated_at || ''
        });
        
        setShowDocModal(true);
      } else {
        console.error('Failed to fetch document details:', docResponse.status);
        // Fallback: show basic info from docs list
        const originalDoc = docs.find(doc => doc.id === docId);
        if (originalDoc) {
          setSelectedDoc({
            id: docId,
            title: originalDoc.title,
            description: originalDoc.description,
            content: 'Content not available',
            created_at: '',
            updated_at: ''
          });
          setShowDocModal(true);
        }
      }
    } catch (error) {
      console.error('Error fetching document details:', error);
      // Fallback: show basic info from docs list
      const originalDoc = docs.find(doc => doc.id === docId);
      if (originalDoc) {
        setSelectedDoc({
          id: docId,
          title: originalDoc.title,
          description: originalDoc.description,
          content: 'Content not available',
          created_at: '',
          updated_at: ''
        });
        setShowDocModal(true);
      }
    }
  };

  // Show loading while mounting or user is not available
  if (!mounted || !user) {
    return (
      <div className={`flex items-center justify-center min-h-screen ${
        resolvedTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      }`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center min-h-screen ${
        resolvedTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      }`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div 
      className={`min-h-screen py-8 transition-colors duration-200 ${
        resolvedTheme === 'dark' 
          ? 'bg-gray-900' 
          : 'bg-gray-50'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <div className={`rounded-lg shadow-sm p-6 border transition-colors duration-200 ${
            resolvedTheme === 'dark'
              ? 'bg-gray-800 border-gray-700'
              : 'bg-white border-gray-200'
          }`}>
            <h1 className={`text-3xl font-bold mb-2 ${
              resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              👋 Welcome, {userInfo?.name || user.email || 'User'}
            </h1>
            <p className={`text-lg mb-1 ${
              resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className={`font-semibold ${
                resolvedTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'
              }`}>
                {(userInfo?.role || user.role || '').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </p>
            {userInfo?.email && userInfo.email !== userInfo.name && (
              <p className={`text-sm ${
                resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {userInfo.email}
              </p>
            )}
          </div>
        </div>

        {/* Ticket Summary Cards */}
        <div className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${
            resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>Ticket Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Open Tickets */}
            <div className={`rounded-lg shadow-sm p-6 border hover:shadow-md transition-all duration-200 ${
              resolvedTheme === 'dark'
                ? 'bg-gray-800 border-gray-700'
                : 'bg-white border-gray-200'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`text-lg font-semibold ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>Open Tickets</h3>
                  <p className={`text-3xl font-bold mt-2 ${
                    resolvedTheme === 'dark' ? 'text-red-400' : 'text-red-600'
                  }`}>{ticketSummary.open}</p>
                </div>
                <div className={`p-3 rounded-full ${
                  resolvedTheme === 'dark' ? 'bg-red-900' : 'bg-red-100'
                }`}>
                  <svg className={`w-6 h-6 ${
                    resolvedTheme === 'dark' ? 'text-red-400' : 'text-red-600'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
              </div>
              <button 
                onClick={() => handleViewTickets('open')}
                className={`mt-4 font-medium ${
                  resolvedTheme === 'dark' 
                    ? 'text-red-400 hover:text-red-300' 
                    : 'text-red-600 hover:text-red-800'
                }`}
              >
                View Details →
              </button>
            </div>

            {/* In Progress Tickets */}
            <div className={`rounded-lg shadow-sm p-6 border hover:shadow-md transition-all duration-200 ${
              resolvedTheme === 'dark'
                ? 'bg-gray-800 border-gray-700'
                : 'bg-white border-gray-200'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`text-lg font-semibold ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>In Progress</h3>
                  <p className={`text-3xl font-bold mt-2 ${
                    resolvedTheme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'
                  }`}>{ticketSummary.inProgress}</p>
                </div>
                <div className={`p-3 rounded-full ${
                  resolvedTheme === 'dark' ? 'bg-yellow-900' : 'bg-yellow-100'
                }`}>
                  <svg className={`w-6 h-6 ${
                    resolvedTheme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <button 
                onClick={() => handleViewTickets('inProgress')}
                className={`mt-4 font-medium ${
                  resolvedTheme === 'dark' 
                    ? 'text-yellow-400 hover:text-yellow-300' 
                    : 'text-yellow-600 hover:text-yellow-800'
                }`}
              >
                View Details →
              </button>
            </div>

            {/* Closed Tickets */}
            <div className={`rounded-lg shadow-sm p-6 border hover:shadow-md transition-all duration-200 ${
              resolvedTheme === 'dark'
                ? 'bg-gray-800 border-gray-700'
                : 'bg-white border-gray-200'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`text-lg font-semibold ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>Closed Tickets</h3>
                  <p className={`text-3xl font-bold mt-2 ${
                    resolvedTheme === 'dark' ? 'text-green-400' : 'text-green-600'
                  }`}>{ticketSummary.closed}</p>
                </div>
                <div className={`p-3 rounded-full ${
                  resolvedTheme === 'dark' ? 'bg-green-900' : 'bg-green-100'
                }`}>
                  <svg className={`w-6 h-6 ${
                    resolvedTheme === 'dark' ? 'text-green-400' : 'text-green-600'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <button 
                onClick={() => handleViewTickets('closed')}
                className={`mt-4 font-medium ${
                  resolvedTheme === 'dark' 
                    ? 'text-green-400 hover:text-green-300' 
                    : 'text-green-600 hover:text-green-800'
                }`}
              >
                View Details →
              </button>
            </div>
          </div>
        </div>

        {/* Recent PR Summaries */}
        <div className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${
            resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>Recent Pull Requests</h2>
          <div className="space-y-4">
            {recentPRs.length > 0 ? (
              recentPRs.map((pr) => (
                <div key={pr.id} className={`rounded-lg shadow-sm p-6 border hover:shadow-md transition-all duration-200 ${
                  resolvedTheme === 'dark'
                    ? 'bg-gray-800 border-gray-700'
                    : 'bg-white border-gray-200'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className={`text-lg font-semibold mb-2 ${
                        resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>{pr.title}</h3>
                      <p className={`text-sm mb-2 ${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      }`}>Ticket: {pr.ticketId}</p>
                      <p className={`line-clamp-2 ${
                        resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>{pr.summary}</p>
                    </div>
                    <button 
                      onClick={() => handleViewPR(pr.id, pr.ticketId)}
                      className={`ml-4 font-medium ${
                        resolvedTheme === 'dark' 
                          ? 'text-blue-400 hover:text-blue-300' 
                          : 'text-blue-600 hover:text-blue-800'
                      }`}
                    >
                      View PR →
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className={`rounded-lg shadow-sm p-6 border text-center transition-all duration-200 ${
                resolvedTheme === 'dark'
                  ? 'bg-gray-800 border-gray-700'
                  : 'bg-white border-gray-200'
              }`}>
                <p className={`${
                  resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>No recent pull requests found.</p>
              </div>
            )}
          </div>
        </div>

        {/* Docs & Learnings */}
        <div className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${
            resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>Resources</h2>
          <div className={`rounded-lg shadow-sm border h-96 transition-colors duration-200 ${
            resolvedTheme === 'dark'
              ? 'bg-gray-800 border-gray-700'
              : 'bg-white border-gray-200'
          }`}>
            {/* Tab Navigation */}
            <div className={`border-b transition-colors duration-200 ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <nav className="flex">
                <button
                  onClick={() => setActiveTab('docs')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200 ${
                    activeTab === 'docs'
                      ? `border-blue-500 ${resolvedTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`
                      : `border-transparent ${
                          resolvedTheme === 'dark' 
                            ? 'text-gray-400 hover:text-gray-300' 
                            : 'text-gray-500 hover:text-gray-700'
                        }`
                  }`}
                >
                  📚 Documentation
                </button>
                <button
                  onClick={() => setActiveTab('learnings')}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200 ${
                    activeTab === 'learnings'
                      ? `border-blue-500 ${resolvedTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`
                      : `border-transparent ${
                          resolvedTheme === 'dark' 
                            ? 'text-gray-400 hover:text-gray-300' 
                            : 'text-gray-500 hover:text-gray-700'
                        }`
                  }`}
                >
                  📒 Learning Resources
                </button>
              </nav>
            </div>

            {/* Tab Content - Scrollable */}
            <div className="p-6 h-80 overflow-y-auto">
              {activeTab === 'docs' && (
                <div className="space-y-4">
                  {docs.length > 0 ? (
                    docs.map((doc) => (
                      <div 
                        key={doc.id} 
                        onClick={() => handleViewDoc(doc.id)}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors duration-200 ${
                          resolvedTheme === 'dark'
                            ? 'border-gray-600 hover:bg-gray-700'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <h3 className={`font-semibold mb-2 ${
                          resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>{doc.title}</h3>
                        <p className={`text-sm ${
                          resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                        }`}>{doc.description}</p>
                        <p className={`text-xs mt-2 ${
                          resolvedTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                        }`}>Click to view content →</p>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <p className={`${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      }`}>No documentation found.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'learnings' && (
                <div className="space-y-4">
                  {learnings.length > 0 ? (
                    learnings.map((learning) => (
                      <div key={learning.id} className={`p-4 border rounded-lg transition-colors duration-200 ${
                        resolvedTheme === 'dark'
                          ? 'border-gray-600 hover:bg-gray-700'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}>
                        <h3 className={`font-semibold mb-2 ${
                          resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>{learning.title}</h3>
                        <p className={`text-sm mb-3 ${
                          resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                        }`}>{learning.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {learning.tags.map((tag) => (
                            <span
                              key={tag}
                              className={`px-2 py-1 text-xs rounded-full ${
                                resolvedTheme === 'dark'
                                  ? 'bg-blue-900 text-blue-200'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <p className={`${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      }`}>No learning resources found.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${
            resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link
              href="/chat"
              className={`rounded-lg p-6 text-center transition-colors shadow-sm ${
                resolvedTheme === 'dark'
                  ? 'bg-blue-700 hover:bg-blue-800 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              <div className="text-2xl mb-2">💬</div>
              <h3 className="font-semibold">Ask the Agent</h3>
              <p className="text-sm opacity-90 mt-1">Get help with your tasks</p>
            </Link>

            <button 
              onClick={handleViewAllTickets}
              className={`rounded-lg p-6 text-center transition-colors shadow-sm border ${
                resolvedTheme === 'dark'
                  ? 'bg-gray-800 hover:bg-gray-700 text-white border-gray-700'
                  : 'bg-white hover:bg-gray-50 text-gray-900 border-gray-200'
              }`}
            >
              <div className="text-2xl mb-2">🗃️</div>
              <h3 className="font-semibold">View My Tickets</h3>
              <p className={`text-sm mt-1 ${
                resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>Manage your tasks</p>
            </button>

            <button className={`rounded-lg p-6 text-center transition-colors shadow-sm border ${
              resolvedTheme === 'dark'
                ? 'bg-gray-800 hover:bg-gray-700 text-white border-gray-700'
                : 'bg-white hover:bg-gray-50 text-gray-900 border-gray-200'
            }`}>
              <div className="text-2xl mb-2">⚙️</div>
              <h3 className="font-semibold">Settings</h3>
              <p className={`text-sm mt-1 ${
                resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>Configure your account</p>
            </button>
          </div>
        </div>
      </div>

      {/* Ticket Details Modal */}
      {showTicketModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden ${
            resolvedTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            {/* Modal Header */}
            <div className={`flex items-center justify-between p-6 border-b ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <h2 className={`text-2xl font-bold ${
                resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {selectedTicketType === 'open' && 'Open Tickets'}
                {selectedTicketType === 'inProgress' && 'In Progress Tickets'}
                {selectedTicketType === 'closed' && 'Closed Tickets'}
                {selectedTicketType === null && 'All My Tickets'}
                <span className={`ml-2 text-sm font-normal ${
                  resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  ({modalTickets.length} ticket{modalTickets.length !== 1 ? 's' : ''})
                </span>
              </h2>
              <button
                onClick={() => setShowTicketModal(false)}
                className={`text-gray-400 ${
                  resolvedTheme === 'dark' ? 'hover:text-gray-300' : 'hover:text-gray-600'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {modalTickets.length > 0 ? (
                <div className="space-y-4">
                  {modalTickets.map((ticket) => (
                    <div key={ticket.id} className={`border rounded-lg p-4 transition-colors ${
                      resolvedTheme === 'dark'
                        ? 'border-gray-600 hover:bg-gray-700'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}>
                      <div className="flex items-start justify-between mb-3">
                        <h3 className={`text-lg font-semibold ${
                          resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>
                          {ticket.title}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.status === 'Open' 
                            ? (resolvedTheme === 'dark' ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800')
                            : ticket.status === 'In Progress'
                            ? (resolvedTheme === 'dark' ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800')
                            : (resolvedTheme === 'dark' ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800')
                        }`}>
                          {ticket.status}
                        </span>
                      </div>
                      <p className={`mb-3 ${
                        resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>
                        {ticket.description}
                      </p>
                      <div className={`flex items-center justify-between text-sm ${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        <span>Project: <span className="font-medium">{ticket.project_name}</span></span>
                        <span>ID: {ticket.id.slice(0, 8)}...</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className={`${
                    resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`}>No tickets found.</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className={`flex justify-end p-6 border-t ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <button
                onClick={() => setShowTicketModal(false)}
                className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PR Details Modal */}
      {showPRModal && selectedPR && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden ${
            resolvedTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            {/* Modal Header */}
            <div className={`flex items-center justify-between p-6 border-b ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <div>
                <h2 className={`text-2xl font-bold ${
                  resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  Pull Request Details
                </h2>
                <p className={`text-sm mt-1 ${
                  resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  Ticket: {selectedPR.ticketId}
                </p>
              </div>
              <button
                onClick={() => setShowPRModal(false)}
                className={`text-gray-400 ${
                  resolvedTheme === 'dark' ? 'hover:text-gray-300' : 'hover:text-gray-600'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="space-y-6">
                {/* PR Title */}
                <div>
                  <h3 className={`text-xl font-semibold mb-2 ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>
                    {selectedPR.title}
                  </h3>
                  <div className={`flex items-center gap-4 text-sm ${
                    resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    <span>ID: {selectedPR.id.slice(0, 8)}...</span>
                    {selectedPR.status && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        resolvedTheme === 'dark' ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {selectedPR.status}
                      </span>
                    )}
                    {selectedPR.author && <span>Author: {selectedPR.author}</span>}
                  </div>
                </div>

                {/* PR Description */}
                <div>
                  <h4 className={`text-lg font-semibold mb-2 ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>
                    Description
                  </h4>
                  <div className={`rounded-lg p-4 ${
                    resolvedTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                  }`}>
                    <p className={`whitespace-pre-wrap ${
                      resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      {selectedPR.description}
                    </p>
                  </div>
                </div>

                {/* AI Summary */}
                {selectedPR.summary && selectedPR.summary !== selectedPR.description && (
                  <div>
                    <h4 className={`text-lg font-semibold mb-2 ${
                      resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      🤖 AI Summary
                    </h4>
                    <div className={`border rounded-lg p-4 ${
                      resolvedTheme === 'dark' 
                        ? 'bg-blue-900/20 border-blue-800' 
                        : 'bg-blue-50 border-blue-200'
                    }`}>
                      <p className={`whitespace-pre-wrap ${
                        resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                      }`}>
                        {selectedPR.summary}
                      </p>
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                {(selectedPR.created_at || selectedPR.updated_at) && (
                  <div>
                    <h4 className={`text-lg font-semibold mb-2 ${
                      resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      Timeline
                    </h4>
                    <div className={`rounded-lg p-4 space-y-2 ${
                      resolvedTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                    }`}>
                      {selectedPR.created_at && (
                        <p className={`text-sm ${
                          resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          <span className="font-medium">Created:</span> {new Date(selectedPR.created_at).toLocaleString()}
                        </p>
                      )}
                      {selectedPR.updated_at && (
                        <p className={`text-sm ${
                          resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          <span className="font-medium">Updated:</span> {new Date(selectedPR.updated_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className={`flex justify-end p-6 border-t ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <button
                onClick={() => setShowPRModal(false)}
                className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Documentation Details Modal */}
      {showDocModal && selectedDoc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden ${
            resolvedTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            {/* Modal Header */}
            <div className={`flex items-center justify-between p-6 border-b ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <div>
                <h2 className={`text-2xl font-bold ${
                  resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  {selectedDoc.title}
                </h2>
                <p className={`text-sm mt-1 ${
                  resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {selectedDoc.description}
                </p>
              </div>
              <button
                onClick={() => setShowDocModal(false)}
                className={`text-gray-400 ${
                  resolvedTheme === 'dark' ? 'hover:text-gray-300' : 'hover:text-gray-600'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[70vh]">
              <div className={`prose max-w-none ${
                resolvedTheme === 'dark' ? 'prose-invert' : 'prose-gray'
              }`}>
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Custom styling for markdown elements
                    h1: ({children}) => <h1 className={`text-3xl font-bold mb-4 ${
                      resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>{children}</h1>,
                    h2: ({children}) => <h2 className={`text-2xl font-semibold mb-3 mt-6 ${
                      resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>{children}</h2>,
                    h3: ({children}) => <h3 className={`text-xl font-semibold mb-2 mt-4 ${
                      resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>{children}</h3>,
                    p: ({children}) => <p className={`mb-4 leading-relaxed ${
                      resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>{children}</p>,
                    ul: ({children}) => <ul className={`list-disc list-inside mb-4 space-y-1 ${
                      resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>{children}</ul>,
                    ol: ({children}) => <ol className={`list-decimal list-inside mb-4 space-y-1 ${
                      resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>{children}</ol>,
                    li: ({children}) => <li className={`${
                      resolvedTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>{children}</li>,
                    code: ({children, className}) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className={`px-1 py-0.5 rounded text-sm font-mono ${
                          resolvedTheme === 'dark' 
                            ? 'bg-gray-700 text-gray-200' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {children}
                        </code>
                      ) : (
                        <code className={`block p-4 rounded-lg overflow-x-auto text-sm font-mono ${
                          resolvedTheme === 'dark' 
                            ? 'bg-gray-700 text-gray-200' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {children}
                        </code>
                      );
                    },
                    pre: ({children}) => <pre className={`p-4 rounded-lg overflow-x-auto mb-4 ${
                      resolvedTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-100'
                    }`}>{children}</pre>,
                    blockquote: ({children}) => <blockquote className={`border-l-4 border-blue-500 pl-4 italic mb-4 ${
                      resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>{children}</blockquote>,
                    a: ({children, href}) => <a href={href} className={`hover:underline ${
                      resolvedTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                    }`} target="_blank" rel="noopener noreferrer">{children}</a>,
                    table: ({children}) => <div className="overflow-x-auto mb-4"><table className={`min-w-full border ${
                      resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                    }`}>{children}</table></div>,
                    th: ({children}) => <th className={`border px-4 py-2 text-left font-semibold ${
                      resolvedTheme === 'dark' 
                        ? 'border-gray-700 bg-gray-700 text-white' 
                        : 'border-gray-200 bg-gray-50 text-gray-900'
                    }`}>{children}</th>,
                    td: ({children}) => <td className={`border px-4 py-2 ${
                      resolvedTheme === 'dark' 
                        ? 'border-gray-700 text-gray-300' 
                        : 'border-gray-200 text-gray-700'
                    }`}>{children}</td>,
                  }}
                >
                  {selectedDoc.content}
                </ReactMarkdown>
              </div>

              {/* Timestamps */}
              {(selectedDoc.created_at || selectedDoc.updated_at) && (
                <div className={`mt-8 pt-6 border-t ${
                  resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                }`}>
                  <h4 className={`text-lg font-semibold mb-2 ${
                    resolvedTheme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>
                    Document Info
                  </h4>
                  <div className={`rounded-lg p-4 space-y-2 ${
                    resolvedTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                  }`}>
                    {selectedDoc.created_at && (
                      <p className={`text-sm ${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        <span className="font-medium">Created:</span> {new Date(selectedDoc.created_at).toLocaleString()}
                      </p>
                    )}
                    {selectedDoc.updated_at && (
                      <p className={`text-sm ${
                        resolvedTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        <span className="font-medium">Updated:</span> {new Date(selectedDoc.updated_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className={`flex justify-end p-6 border-t ${
              resolvedTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <button
                onClick={() => setShowDocModal(false)}
                className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 