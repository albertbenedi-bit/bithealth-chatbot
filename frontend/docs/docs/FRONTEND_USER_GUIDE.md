# Frontend User Guide

## Overview

The PV Chatbot Frontend is a healthcare-focused conversational AI platform that provides an intuitive interface for patients and healthcare staff to interact with AI-powered assistance for appointment management, information dissemination, and general healthcare inquiries.

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Backend Orchestrator service running on port 8000
- Authentication service running on port 8004 (optional for dummy auth)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/pjoetan/pv_chatbot_general.git
cd pv_chatbot_general/frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

4. **Start the development server:**
```bash
npm run dev
```

5. **Open your browser:**
Navigate to `http://localhost:5173`

## User Interface Overview

### Login Page

The application starts with a secure login page featuring:

- **Email/Password Form**: Standard authentication form
- **Demo Access Buttons**: Quick access for testing
  - **Patient Demo**: Login as a patient user
  - **Admin Demo**: Login as an administrator
- **Healthcare Branding**: Professional medical interface design
- **Responsive Design**: Works on desktop and mobile devices

### Main Chat Interface

After successful login, users access the main chat interface consisting of:

#### Sidebar (Left Panel)
- **User Profile**: Display name, role, and department
- **Settings Menu**: Access to user preferences and logout
- **New Chat Button**: Start a fresh conversation
- **Recent Conversations**: List of previous chat sessions with timestamps

#### Chat Area (Main Panel)
- **Welcome Screen**: Introduction and feature overview
- **Message History**: Scrollable conversation display
- **Message Input**: Text input with send button
- **Status Indicators**: Online status and typing indicators
- **Error Messages**: User-friendly error notifications

### Admin Dashboard

Administrators have access to a comprehensive dashboard featuring:

#### System Metrics
- **Active Sessions**: Current number of active chat sessions
- **Total Messages**: Cumulative message count processed
- **System Uptime**: Service availability duration
- **LLM Provider Status**: Current and fallback AI providers

#### Performance Monitoring
- **Response Times**: Average, 95th, and 99th percentile response times
- **Error Rates**: LLM provider errors, session errors, and timeouts
- **Intent Distribution**: Breakdown of conversation topics

#### Health Status
- **Service Health**: Overall system health indicator
- **Component Status**: Individual service status checks
- **Refresh Controls**: Manual and automatic data refresh options

## User Roles and Permissions

### Patient Role
- **Access**: Chat interface and personal session history
- **Features**: 
  - Schedule, reschedule, or cancel appointments
  - Get pre-admission and post-discharge information
  - Ask questions about hospital services
  - Receive personalized healthcare guidance
- **Restrictions**: Cannot access admin dashboard or system metrics

### Staff Role
- **Access**: Enhanced chat interface with additional features
- **Features**: All patient features plus:
  - Access to department-specific information
  - Priority message handling
  - Extended session capabilities
- **Restrictions**: Limited admin dashboard access

### Admin Role
- **Access**: Full system access including admin dashboard
- **Features**: All staff features plus:
  - System monitoring and analytics
  - User management capabilities
  - Performance metrics and health status
  - Configuration management

## Using the Chat Interface

### Starting a Conversation

1. **New Chat**: Click the "New Chat" button in the sidebar
2. **Type Message**: Enter your message in the input field at the bottom
3. **Send**: Click the send button or press Enter
4. **Wait for Response**: The AI will process and respond to your message

### Message Types

#### Patient Inquiries
- **Appointment Booking**: "I want to book an appointment with a cardiologist"
- **General Information**: "What are your visiting hours?"
- **Medical Questions**: "What should I prepare for my surgery?"
- **Emergency Situations**: "I have chest pain" (triggers human handoff)

#### Staff Inquiries
- **Department Information**: "Show me today's schedule for cardiology"
- **Patient Status**: "What's the status of patient ID 12345?"
- **Resource Availability**: "Are there any available OR slots today?"

### Session Management

#### Continuing Conversations
- **Session History**: Click on any previous conversation in the sidebar
- **Context Preservation**: Previous conversation context is maintained
- **Seamless Continuation**: Pick up where you left off

#### Managing Sessions
- **Multiple Sessions**: Maintain multiple concurrent conversations
- **Session Titles**: Automatically generated based on first message
- **Timestamps**: Last activity time displayed for each session

### Understanding AI Responses

#### Response Elements
- **Main Response**: The AI's answer to your question
- **Intent Classification**: What the AI understood your request to be
- **Confidence Score**: How confident the AI is in its understanding
- **Suggested Actions**: Recommended next steps
- **Processing Time**: How long the response took to generate

#### Special Indicators
- **Human Handoff Required**: When the AI determines human assistance is needed
- **Emergency Detection**: Urgent medical situations trigger immediate escalation
- **Appointment Actions**: Specific appointment-related follow-ups

## Admin Dashboard Usage

### Accessing the Dashboard

1. **Login as Admin**: Use admin credentials or demo button
2. **Navigate**: Go to `/admin` or use the navigation menu
3. **Dashboard Overview**: View real-time system metrics

### Monitoring System Health

#### Key Metrics to Watch
- **Active Sessions**: Normal range 10-100, high load >200
- **Response Times**: Target <2 seconds average
- **Error Rates**: Should be <5% for optimal performance
- **Uptime**: Target 99.9% availability

#### Health Status Indicators
- **Green (Healthy)**: All systems operational
- **Yellow (Degraded)**: Some issues but functional
- **Red (Unhealthy)**: Critical issues requiring attention

### Performance Analysis

#### Response Time Analysis
- **Average Response Time**: Overall system performance
- **95th Percentile**: Performance for most users
- **99th Percentile**: Worst-case performance scenarios

#### Intent Distribution
- **Popular Intents**: Most common user requests
- **Trending Topics**: Emerging conversation patterns
- **Success Rates**: Intent classification accuracy

### Troubleshooting

#### Common Issues
1. **High Error Rates**: Check backend service connectivity
2. **Slow Response Times**: Monitor system resources
3. **Failed Sessions**: Verify database connectivity
4. **Authentication Issues**: Check auth service status

## Mobile Usage

### Responsive Design
- **Adaptive Layout**: Interface adjusts to screen size
- **Touch Optimization**: Buttons and inputs sized for touch
- **Swipe Navigation**: Gesture support for mobile devices

### Mobile-Specific Features
- **Collapsible Sidebar**: Saves screen space on small devices
- **Optimized Typing**: Mobile keyboard optimization
- **Offline Indicators**: Network status awareness

## Accessibility Features

### Keyboard Navigation
- **Tab Navigation**: Full keyboard accessibility
- **Keyboard Shortcuts**: Quick actions via keyboard
- **Focus Indicators**: Clear focus states for all interactive elements

### Screen Reader Support
- **ARIA Labels**: Proper labeling for screen readers
- **Semantic HTML**: Meaningful HTML structure
- **Alt Text**: Descriptive text for images and icons

### Visual Accessibility
- **High Contrast**: Sufficient color contrast ratios
- **Scalable Text**: Respects browser zoom settings
- **Color Independence**: Information not conveyed by color alone

## Security and Privacy

### Data Protection
- **Encryption**: All data transmitted over HTTPS
- **Session Security**: Secure session management
- **Token-Based Auth**: JWT tokens for authentication

### Privacy Considerations
- **Data Minimization**: Only necessary data collected
- **Session Isolation**: User sessions are isolated
- **Audit Logging**: Security events are logged

### Best Practices
- **Regular Logout**: Log out when finished
- **Secure Passwords**: Use strong authentication credentials
- **Report Issues**: Report security concerns immediately

## Troubleshooting

### Common Issues and Solutions

#### Login Problems
- **Issue**: Cannot log in with credentials
- **Solution**: Verify auth service is running, check network connectivity
- **Workaround**: Use demo login buttons for testing

#### Chat Not Working
- **Issue**: Messages not sending or receiving responses
- **Solution**: Check backend orchestrator service status
- **Workaround**: Refresh page and try again

#### Admin Dashboard Empty
- **Issue**: No metrics or data displayed
- **Solution**: Verify backend services are running and accessible
- **Workaround**: Use refresh button to reload data

#### Performance Issues
- **Issue**: Slow loading or response times
- **Solution**: Check network connection and server resources
- **Workaround**: Clear browser cache and reload

### Error Messages

#### Authentication Errors
- **"Invalid credentials"**: Check username/password
- **"Session expired"**: Log in again
- **"Access denied"**: Verify user role permissions

#### API Errors
- **"Failed to send message"**: Backend service unavailable
- **"Session not found"**: Session may have expired
- **"Service unavailable"**: Temporary service interruption

### Getting Help

#### Support Channels
- **Technical Issues**: Contact system administrator
- **User Questions**: Refer to this user guide
- **Feature Requests**: Submit through proper channels

#### Debug Information
- **Browser Console**: Check for error messages
- **Network Tab**: Monitor API requests
- **Version Info**: Note application version for support

## Advanced Features

### Keyboard Shortcuts
- **Ctrl/Cmd + Enter**: Send message
- **Ctrl/Cmd + N**: New chat
- **Ctrl/Cmd + /**: Focus search
- **Esc**: Close modals or cancel actions

### URL Navigation
- **Direct Links**: Share specific chat sessions
- **Bookmarking**: Bookmark frequently used sections
- **Browser History**: Use back/forward navigation

### Integration Features
- **Copy/Paste**: Rich text support for messages
- **File Attachments**: Future support for document sharing
- **Export Options**: Future support for conversation export

## Configuration Options

### User Preferences
- **Language**: Interface language selection (future)
- **Notifications**: Message and system notifications
- **Theme**: Light/dark mode preferences (future)

### Admin Configuration
- **System Settings**: Backend service URLs
- **Feature Flags**: Enable/disable specific features
- **Monitoring**: Adjust refresh intervals and thresholds

This user guide provides comprehensive information for effectively using the PV Chatbot Frontend. For additional support or questions not covered in this guide, please contact your system administrator.
