import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 text-slate-800 animate-fade-in">
          <div className="max-w-md w-full text-center bg-white p-8 rounded-2xl border border-slate-200 shadow-lg">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 text-red-600 mb-6">
              <AlertTriangle size={32} />
            </div>
            
            <h2 className="text-2xl font-extrabold text-slate-900 mb-2">
              Application Error
            </h2>
            
            <p className="text-slate-600 mb-6 text-sm">
              An unexpected error occurred while rendering this view. Your data is safe, but we need to reset the page.
            </p>

            {this.state.error && (
              <pre className="text-left text-xs bg-slate-50 p-4 rounded-lg border border-slate-200 overflow-x-auto text-red-600 mb-6 max-h-40">
                {this.state.error.toString()}
              </pre>
            )}

            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors shadow-sm"
            >
              <RefreshCw size={16} />
              Reset Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
