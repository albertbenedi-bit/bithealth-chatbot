import type { WebSocketMessage } from '../types/api';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private messageHandlers: ((message: WebSocketMessage) => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor() {
    this.handleMessage = this.handleMessage.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleOpen = this.handleOpen.bind(this);
  }

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        if (this.sessionId === sessionId) {
          resolve();
          return;
        } else {
          this.disconnect();
        }
      }

      this.isConnecting = true;
      this.sessionId = sessionId;
      
      const wsUrl = this.getWebSocketUrl(sessionId);
      this.ws = new WebSocket(wsUrl);

      const onOpen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        console.log(`WebSocket connected for session: ${sessionId}`);
        resolve();
      };

      const onError = (error: Event) => {
        this.isConnecting = false;
        console.error('WebSocket connection error:', error);
        reject(new Error('Failed to connect to WebSocket'));
      };

      this.ws.addEventListener('open', onOpen, { once: true });
      this.ws.addEventListener('error', onError, { once: true });
      this.ws.addEventListener('message', this.handleMessage);
      this.ws.addEventListener('close', this.handleClose);
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.removeEventListener('message', this.handleMessage);
      this.ws.removeEventListener('close', this.handleClose);
      this.ws.removeEventListener('error', this.handleError);
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  onMessage(handler: (message: WebSocketMessage) => void): () => void {
    this.messageHandlers.push(handler);
    
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index > -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  send(message: object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
    }
  }

  private getWebSocketUrl(sessionId: string): string {
    const baseUrl = import.meta.env.VITE_BACKEND_ORCHESTRATOR_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace(/^http/, 'ws');
    return `${wsUrl}/ws/${sessionId}`;
  }

  private handleMessage(event: MessageEvent): void {
    // --- PUT YOUR CONSOLE.LOG HERE ---
    console.log('--- RAW WebSocket message received ---', event.data);
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log('DEBUG WS: Parsed WebSocket message in WebSocketService:', message);

      console.log('DEBUG WS: About to iterate through message handlers. Count:', this.messageHandlers.length); // <-- ADD THIS LOG
      this.messageHandlers.forEach(handler => {
        console.log('DEBUG WS: Invoking a handler from the list...'); // <-- ADD THIS LOG
        try {
          handler(message);
        } catch (error) {
          console.error('Error in WebSocket message handler:', error);
        }
      });
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket connection closed:', event.code, event.reason);
    this.ws = null;
    this.isConnecting = false;

    if (this.sessionId && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        if (this.sessionId) {
          this.connect(this.sessionId).catch(error => {
            console.error('Reconnection failed:', error);
          });
        }
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
  }

  private handleOpen(event: Event): void {
    console.log('WebSocket connection opened:', event);
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }
}

export const websocketService = new WebSocketService();
