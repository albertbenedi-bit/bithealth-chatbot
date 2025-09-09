import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Activity, 
  MessageSquare, 
  Users, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { MetricsData, HealthStatus } from '../../types/api';
import { apiService } from '../../services/api';

export function AdminDashboard() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [metricsData, healthData] = await Promise.all([
        apiService.getMetrics(),
        apiService.getHealth(),
      ]);
      
      setMetrics(metricsData);
      setHealth(healthData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4" />;
      case 'degraded': return <AlertTriangle className="h-4 w-4" />;
      case 'unhealthy': return <XCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  if (loading && !metrics) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-4">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600" />
            <p className="text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">System monitoring and analytics</p>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdated && (
            <p className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
          <Button onClick={fetchData} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {getHealthStatusIcon(health.status)}
              <span>System Health</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-lg font-semibold ${getHealthStatusColor(health.status)}`}>
                  {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
                </p>
                <p className="text-sm text-gray-600">Service: {health.service}</p>
                <p className="text-sm text-gray-600">Version: {health.version}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">
                  Checked: {new Date(health.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {metrics && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.active_sessions}</div>
                <p className="text-xs text-muted-foreground">
                  Currently active conversations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.total_messages_processed}</div>
                <p className="text-xs text-muted-foreground">
                  Messages processed today
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.response_times.avg_ms}ms</div>
                <p className="text-xs text-muted-foreground">
                  P95: {metrics.response_times.p95_ms}ms
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatUptime(metrics.uptime_seconds)}</div>
                <p className="text-xs text-muted-foreground">
                  Current session uptime
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Intent Distribution</CardTitle>
                <CardDescription>Most common user intents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(metrics.intent_distribution)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([intent, count]) => (
                      <div key={intent} className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">
                          {intent.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{
                                width: `${(count / Math.max(...Object.values(metrics.intent_distribution))) * 100}%`
                              }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Rates</CardTitle>
                <CardDescription>System error monitoring</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">LLM Provider Errors</span>
                    <span className={`text-sm font-bold ${
                      metrics.error_rates.llm_provider_errors > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metrics.error_rates.llm_provider_errors}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Session Errors</span>
                    <span className={`text-sm font-bold ${
                      metrics.error_rates.session_errors > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metrics.error_rates.session_errors}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Agent Timeouts</span>
                    <span className={`text-sm font-bold ${
                      metrics.error_rates.agent_timeouts > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metrics.error_rates.agent_timeouts}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>LLM Configuration</CardTitle>
              <CardDescription>Current language model setup</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-700">Primary Provider</p>
                  <p className="text-lg font-semibold text-blue-600">{metrics.llm_provider}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Fallback Provider</p>
                  <p className="text-lg font-semibold text-green-600">{metrics.fallback_provider}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
