# Frontend Architecture Documentation

## System Overview

The PV Chatbot Frontend implements a modern React-based architecture designed for healthcare conversational AI applications. It follows component-based design principles with clear separation of concerns, modular authentication, and scalable state management.

## Architectural Principles

### 1. Component-Based Architecture

The application is built using React's component-based architecture, promoting:
- **Reusability**: Components can be reused across different parts of the application
- **Maintainability**: Clear separation of concerns makes code easier to maintain
- **Testability**: Individual components can be tested in isolation
- **Scalability**: New features can be added without affecting existing functionality

### 2. Modular Design

```mermaid
graph TB
    App["App.tsx<br/>Main Application"]
    
    subgraph "Authentication Layer"
        AuthContext["AuthContext<br/>State Management"]
        LoginPage["LoginPage<br/>Login Interface"]
        ProtectedRoute["ProtectedRoute<br/>Access Control"]
    end
    
    subgraph "Chat Interface"
        ChatLayout["ChatLayout<br/>Main Container"]
        ChatSidebar["ChatSidebar<br/>Session History"]
        ChatArea["ChatArea<br/>Message Interface"]
    end
    
    subgraph "Admin Interface"
        AdminDashboard["AdminDashboard<br/>System Monitoring"]
    end
    
    subgraph "Service Layer"
        ApiService["ApiService<br/>Backend Integration"]
        Types["TypeScript Types<br/>Data Contracts"]
    end
    
    App --> AuthContext
    App --> LoginPage
    App --> ProtectedRoute
    
    ProtectedRoute --> ChatLayout
    ProtectedRoute --> AdminDashboard
    
    ChatLayout --> ChatSidebar
    ChatLayout --> ChatArea
    
    ChatArea --> ApiService
    AdminDashboard --> ApiService
    AuthContext --> ApiService
    
    ApiService --> Types
```

### 3. Separation of Concerns

The architecture clearly separates different responsibilities:

- **Presentation Layer**: React components handle UI rendering and user interactions
- **Business Logic Layer**: Custom hooks and context providers manage application state
- **Data Access Layer**: API service handles all backend communication
- **Type Safety Layer**: TypeScript interfaces ensure type safety across the application

### 4. State Management Strategy

```mermaid
graph LR
    subgraph "Global State"
        AuthContext["Authentication State<br/>User, Token, Role"]
    end
    
    subgraph "Component State"
        ChatState["Chat State<br/>Messages, Sessions"]
        AdminState["Admin State<br/>Metrics, Health"]
        UIState["UI State<br/>Loading, Errors"]
    end
    
    AuthContext --> ChatState
    AuthContext --> AdminState
    AuthContext --> UIState
```

## Component Architecture

### Authentication System

#### AuthContext Provider

```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}

interface AuthContextType {
  authState: AuthState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
```

**Design Principles:**
- **Single Source of Truth**: All authentication state managed in one place
- **Provider Pattern**: Context provides auth state to entire application
- **Immutable Updates**: State updates follow immutable patterns
- **Error Handling**: Comprehensive error handling for auth operations

#### Modular Authentication Design

The authentication system is designed for future extensibility:

```mermaid
graph TB
    AuthContext["AuthContext<br/>Core Auth Logic"]
    
    subgraph "Current Implementation"
        DummyAuth["Dummy Auth<br/>Always Succeeds"]
    end
    
    subgraph "Future Providers"
        GoogleAuth["Google Workspace<br/>OAuth Integration"]
        EntraAuth["Microsoft Entra<br/>Azure AD"]
        CognitoAuth["AWS Cognito<br/>Identity Pool"]
        InternalAuth["Internal DB<br/>PostgreSQL"]
    end
    
    AuthContext --> DummyAuth
    AuthContext -.-> GoogleAuth
    AuthContext -.-> EntraAuth
    AuthContext -.-> CognitoAuth
    AuthContext -.-> InternalAuth
```

### Chat Interface Architecture

#### Component Hierarchy

```mermaid
graph TB
    ChatLayout["ChatLayout<br/>Session Management"]
    
    ChatSidebar["ChatSidebar<br/>- User Profile<br/>- Session List<br/>- New Chat Button"]
    
    ChatArea["ChatArea<br/>- Message Display<br/>- Input Interface<br/>- Error Handling"]
    
    ChatLayout --> ChatSidebar
    ChatLayout --> ChatArea
    
    subgraph "Data Flow"
        SessionState["Session State<br/>Current Session<br/>Session History"]
        MessageState["Message State<br/>Conversation History<br/>Input State"]
    end
    
    ChatLayout --> SessionState
    ChatArea --> MessageState
```

#### State Management Flow

```mermaid
sequenceDiagram
    participant U as User
    participant CA as ChatArea
    participant CL as ChatLayout
    participant API as ApiService
    participant B as Backend

    U->>CA: Send Message
    CA->>CA: Update UI (optimistic)
    CA->>API: POST /chat
    API->>B: HTTP Request
    B->>API: Chat Response
    API->>CA: Response Data
    CA->>CL: Update Session
    CL->>CL: Update Session List
```

### Admin Dashboard Architecture

#### Metrics Management

```mermaid
graph TB
    AdminDashboard["AdminDashboard<br/>Main Container"]
    
    subgraph "Metrics Components"
        SystemMetrics["System Metrics<br/>- Active Sessions<br/>- Message Count<br/>- Uptime"]
        PerformanceMetrics["Performance Metrics<br/>- Response Times<br/>- Error Rates<br/>- Intent Distribution"]
        HealthStatus["Health Status<br/>- Service Health<br/>- Provider Status"]
    end
    
    subgraph "Data Management"
        MetricsState["Metrics State<br/>Real-time Data"]
        RefreshLogic["Refresh Logic<br/>Auto/Manual Update"]
        ErrorHandling["Error Handling<br/>Fallback UI"]
    end
    
    AdminDashboard --> SystemMetrics
    AdminDashboard --> PerformanceMetrics
    AdminDashboard --> HealthStatus
    
    AdminDashboard --> MetricsState
    AdminDashboard --> RefreshLogic
    AdminDashboard --> ErrorHandling
```

## Data Flow Architecture

### Request/Response Flow

```mermaid
sequenceDiagram
    participant C as Component
    participant AS as ApiService
    participant I as Interceptor
    participant B as Backend

    C->>AS: API Call
    AS->>I: Request Interceptor
    I->>I: Add Auth Token
    I->>B: HTTP Request
    B->>I: HTTP Response
    I->>I: Response Interceptor
    I->>AS: Processed Response
    AS->>C: Return Data
    
    Note over C,B: Error handling at each layer
```

### Error Handling Strategy

```mermaid
graph TB
    APIError["API Error"]
    
    subgraph "Error Types"
        NetworkError["Network Error<br/>Connection Issues"]
        AuthError["Auth Error<br/>401/403 Status"]
        ValidationError["Validation Error<br/>400/422 Status"]
        ServerError["Server Error<br/>500 Status"]
    end
    
    subgraph "Error Handling"
        Retry["Retry Logic<br/>Exponential Backoff"]
        Fallback["Fallback UI<br/>Graceful Degradation"]
        UserMessage["User Message<br/>Friendly Error Display"]
        Logging["Error Logging<br/>Debug Information"]
    end
    
    APIError --> NetworkError
    APIError --> AuthError
    APIError --> ValidationError
    APIError --> ServerError
    
    NetworkError --> Retry
    AuthError --> UserMessage
    ValidationError --> UserMessage
    ServerError --> Fallback
    
    Retry --> Logging
    Fallback --> Logging
    UserMessage --> Logging
```

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant B as Backend

    U->>F: Login Credentials
    F->>A: Authentication Request
    A->>A: Validate Credentials
    A->>F: JWT Token + User Info
    F->>F: Store in Memory
    
    loop API Requests
        F->>B: Request + Bearer Token
        B->>B: Validate Token
        B->>F: Protected Resource
    end
    
    U->>F: Logout
    F->>F: Clear Token
    F->>A: Logout Request (optional)
```

### Role-Based Access Control

```mermaid
graph TB
    User["User Login"]
    
    subgraph "Role Assignment"
        Patient["Patient Role<br/>- Chat Access<br/>- Session History"]
        Staff["Staff Role<br/>- Chat Access<br/>- Extended Features"]
        Admin["Admin Role<br/>- Full Access<br/>- Dashboard<br/>- Metrics"]
    end
    
    subgraph "Route Protection"
        PublicRoutes["Public Routes<br/>- Login Page"]
        ProtectedRoutes["Protected Routes<br/>- Chat Interface"]
        AdminRoutes["Admin Routes<br/>- Dashboard<br/>- Metrics"]
    end
    
    User --> Patient
    User --> Staff
    User --> Admin
    
    Patient --> PublicRoutes
    Patient --> ProtectedRoutes
    
    Staff --> PublicRoutes
    Staff --> ProtectedRoutes
    
    Admin --> PublicRoutes
    Admin --> ProtectedRoutes
    Admin --> AdminRoutes
```

## Performance Architecture

### Code Splitting Strategy

```mermaid
graph TB
    MainBundle["Main Bundle<br/>Core Components"]
    
    subgraph "Route-Based Splitting"
        ChatBundle["Chat Bundle<br/>Chat Components"]
        AdminBundle["Admin Bundle<br/>Dashboard Components"]
        AuthBundle["Auth Bundle<br/>Login Components"]
    end
    
    subgraph "Component-Based Splitting"
        UIBundle["UI Bundle<br/>shadcn/ui Components"]
        UtilsBundle["Utils Bundle<br/>Helper Functions"]
    end
    
    MainBundle --> ChatBundle
    MainBundle --> AdminBundle
    MainBundle --> AuthBundle
    
    ChatBundle --> UIBundle
    AdminBundle --> UIBundle
    AuthBundle --> UIBundle
    
    UIBundle --> UtilsBundle
```

### Caching Strategy

```mermaid
graph TB
    subgraph "Browser Caching"
        StaticAssets["Static Assets<br/>Images, CSS, JS"]
        APIResponses["API Responses<br/>Short-term Cache"]
    end
    
    subgraph "Application Caching"
        SessionCache["Session Cache<br/>Current Session Data"]
        UserCache["User Cache<br/>Profile Information"]
        MetricsCache["Metrics Cache<br/>Dashboard Data"]
    end
    
    subgraph "Cache Invalidation"
        TimeBasedInvalidation["Time-based<br/>TTL Expiration"]
        EventBasedInvalidation["Event-based<br/>User Actions"]
    end
    
    StaticAssets --> TimeBasedInvalidation
    APIResponses --> TimeBasedInvalidation
    SessionCache --> EventBasedInvalidation
    UserCache --> EventBasedInvalidation
    MetricsCache --> TimeBasedInvalidation
```

## Scalability Considerations

### Component Scalability

1. **Lazy Loading**: Components loaded on-demand
2. **Memoization**: React.memo for expensive components
3. **Virtual Scrolling**: For large message lists (future)
4. **Pagination**: For session history

### State Management Scalability

1. **Context Splitting**: Separate contexts for different domains
2. **Reducer Pattern**: For complex state updates
3. **Middleware**: For logging and debugging
4. **Persistence**: Local storage for offline capability

### API Scalability

1. **Request Batching**: Combine multiple requests
2. **Debouncing**: Reduce API call frequency
3. **Caching**: Reduce redundant requests
4. **Retry Logic**: Handle temporary failures

## Development Architecture

### Build System

```mermaid
graph LR
    Source["Source Code<br/>TypeScript/React"]
    
    subgraph "Build Pipeline"
        TypeCheck["Type Checking<br/>TypeScript Compiler"]
        Bundling["Bundling<br/>Vite"]
        Optimization["Optimization<br/>Minification/Tree Shaking"]
    end
    
    subgraph "Output"
        DevBuild["Development Build<br/>Fast Rebuild"]
        ProdBuild["Production Build<br/>Optimized"]
    end
    
    Source --> TypeCheck
    TypeCheck --> Bundling
    Bundling --> Optimization
    
    Optimization --> DevBuild
    Optimization --> ProdBuild
```

### Testing Architecture

```mermaid
graph TB
    subgraph "Testing Layers"
        UnitTests["Unit Tests<br/>Component Testing"]
        IntegrationTests["Integration Tests<br/>API Integration"]
        E2ETests["E2E Tests<br/>User Journeys"]
    end
    
    subgraph "Testing Tools"
        Jest["Jest<br/>Test Runner"]
        RTL["React Testing Library<br/>Component Testing"]
        MSW["MSW<br/>API Mocking"]
        Playwright["Playwright<br/>E2E Testing"]
    end
    
    UnitTests --> Jest
    UnitTests --> RTL
    IntegrationTests --> MSW
    E2ETests --> Playwright
```

## Deployment Architecture

### Environment Strategy

```mermaid
graph TB
    subgraph "Development"
        DevEnv["Development<br/>- Hot Reload<br/>- Debug Mode<br/>- Mock APIs"]
    end
    
    subgraph "Staging"
        StagingEnv["Staging<br/>- Production Build<br/>- Real APIs<br/>- Testing"]
    end
    
    subgraph "Production"
        ProdEnv["Production<br/>- Optimized Build<br/>- CDN<br/>- Monitoring"]
    end
    
    DevEnv --> StagingEnv
    StagingEnv --> ProdEnv
```

### Configuration Management

```typescript
// Environment-specific configuration
interface Config {
  apiUrl: string;
  authUrl: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    debugMode: boolean;
    mockAuth: boolean;
    analytics: boolean;
  };
}
```

## Future Architecture Enhancements

### Planned Improvements

1. **Real-time Communication**
   - WebSocket integration for live chat
   - Server-sent events for notifications

2. **Offline Capability**
   - Service worker implementation
   - Local data persistence
   - Sync when online

3. **Micro-frontend Architecture**
   - Module federation
   - Independent deployments
   - Team autonomy

4. **Advanced State Management**
   - Redux Toolkit for complex state
   - RTK Query for data fetching
   - Optimistic updates

5. **Enhanced Security**
   - Content Security Policy
   - Subresource Integrity
   - Token refresh mechanism

### Monitoring and Observability

```mermaid
graph TB
    subgraph "Frontend Monitoring"
        ErrorTracking["Error Tracking<br/>Sentry/Bugsnag"]
        PerformanceMonitoring["Performance<br/>Web Vitals"]
        UserAnalytics["User Analytics<br/>Usage Patterns"]
    end
    
    subgraph "Logging"
        ClientLogs["Client-side Logs<br/>Console/Remote"]
        APILogs["API Logs<br/>Request/Response"]
        UserActions["User Actions<br/>Click Tracking"]
    end
    
    ErrorTracking --> ClientLogs
    PerformanceMonitoring --> APILogs
    UserAnalytics --> UserActions
```

This architecture provides a solid foundation for the healthcare chatbot frontend while maintaining flexibility for future enhancements and integrations.
