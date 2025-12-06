import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getSessionSummary } from "@/lib/api";
import type { SessionSummary } from "@/types/session";
import { Clock, MessageSquare, TrendingDown, TrendingUp, Minus, AlertTriangle, Phone, Heart, CheckCircle } from "lucide-react";

// Add custom CSS for line-clamp
const styles = `
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
`;

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}

export const Route = createFileRoute("/feedback/$sessionId")({
  component: RouteComponent,
});

function RouteComponent() {
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get sessionId from URL parameters
  const { sessionId } = Route.useParams();

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        // Use real API call
        const sessionSummary = await getSessionSummary(sessionId);
        setSummary(sessionSummary);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session summary');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [sessionId]);

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getSentimentTrend = (avgSentiment: number): string => {
    if (avgSentiment > 0.5) return 'improving';
    if (avgSentiment < -0.) return 'declining';
    return 'stable';
  };

  const getSentimentIcon = (avgSentiment: number) => {
    const trend = getSentimentTrend(avgSentiment);
    switch (trend) {
      case 'improving': return <TrendingUp className="w-5 h-5 text-[#6BAF7A]" />;
      case 'declining': return <TrendingDown className="w-5 h-5 text-[#C46262]" />;
      default: return <Minus className="w-5 h-5 text-[#4A90A0]" />;
    }
  };

  const getRiskColor = (tier: string): string => {
    switch (tier) {
      case 'crisis': return 'text-[#C46262] bg-red-50';
      case 'high': return 'text-[#E7C45B] bg-yellow-50';
      case 'caution': return 'text-[#E7C45B] bg-yellow-50';
      default: return 'text-[#6BAF7A] bg-green-50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F4F2] flex items-center justify-center">
        <div className="text-[#4A90A0]">Loading session summary...</div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-[#F6F4F2] flex items-center justify-center">
        <div className="max-w-md mx-auto bg-white rounded-xl p-6 text-center">
          <AlertTriangle className="w-12 h-12 text-[#E7C45B] mx-auto mb-4" />
          <p className="text-gray-700 mb-4">{error || 'Unable to load session summary'}</p>
          <Link 
            to="/dashboard" 
            className="inline-flex items-center px-5 py-3 bg-[#4A90A0] text-white rounded-lg hover:bg-[#3a7a8a] transition-colors"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F4F2] relative">
      {/* Dashboard Button - Top Right */}
      <div className="absolute top-4 right-4 z-10">
        <Link 
          to="/dashboard" 
          className="inline-flex items-center px-4 py-2 bg-[#4A90A0] text-white rounded-lg hover:bg-[#3a7a8a] transition-colors shadow-lg"
        >
          ← Dashboard
        </Link>
      </div>
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-medium text-gray-900 mb-2">Session Complete</h1>
          <p className="text-gray-600">Here's a summary of your conversation</p>
        </div>

        {/* Session Overview */}
        <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-medium text-gray-900 mb-4">Session Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#D8EFE8] rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-[#4A90A0]" />
                <div>
                  <div className="text-sm text-gray-600">Duration</div>
                  <div className="text-lg font-medium">{formatDuration(summary.summary.duration_seconds)}</div>
                </div>
              </div>
            </div>
            <div className="bg-[#E3E2F0] rounded-lg p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-5 h-5 text-[#6879A1]" />
                <div>
                  <div className="text-sm text-gray-600">User Messages</div>
                  <div className="text-lg font-medium">{summary.summary.metrics.user_turns}</div>
                </div>
              </div>
            </div>
            <div className="bg-[#E3E2F0] rounded-lg p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-5 h-5 text-[#6879A1]" />
                <div>
                  <div className="text-sm text-gray-600">Assistant Messages</div>
                  <div className="text-lg font-medium">{summary.summary.metrics.assistant_turns}</div>
                </div>
              </div>
            </div>
            {/* <div className="bg-[#D8EFE8] rounded-lg p-4">
              <div className="flex items-center gap-3">
                {getSentimentIcon(summary.summary.metrics.avg_sentiment)}
                <div>
                  <div className="text-sm text-gray-600">Sentiment Trend</div>
                  <div className="text-lg font-medium capitalize">{getSentimentTrend(summary.summary.metrics.avg_sentiment)}</div>
                </div>
              </div>
            </div> */}
          </div>
        </div>

        {/* Sentiment Analysis
        <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-medium text-gray-900 mb-4">Conversation Insights</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Sentiment Distribution</span>
                <span>Average: {(summary.summary.metrics.avg_sentiment * 100).toFixed(0)}%</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-lg font-medium text-green-700">{summary.summary.metrics.band_counts?.positive || 0}</div>
                  <div className="text-xs text-green-600">Positive</div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <div className="text-lg font-medium text-gray-700">{summary.summary.metrics.band_counts?.neutral || 0}</div>
                  <div className="text-xs text-gray-600">Neutral</div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <div className="text-lg font-medium text-red-700">{summary.summary.metrics.band_counts?.negative || 0}</div>
                  <div className="text-xs text-red-600">Negative</div>
                </div>
              </div>
            </div>
          </div>
        </div> */}

        {/* Risk Assessment */}
        <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-medium text-gray-900 mb-4">Wellbeing Check</h2>
          <div className="space-y-4">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(summary.summary.metrics.max_risk_tier)}`}>
              Highest Concern Level: {summary.summary.metrics.max_risk_tier.toUpperCase()}
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(summary.summary.metrics.tier_counts || {}).map(([tier, count]) => (
                <div key={tier} className="bg-gray-50 p-3 rounded-lg text-center">
                  <div className="text-lg font-medium">{count}</div>
                  <div className="text-xs text-gray-600 capitalize">{tier}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Suggested Resources */}
        {summary.summary.metrics.suggested_resources && summary.summary.metrics.suggested_resources.length > 0 ? (
          <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-xl font-medium text-gray-900 mb-4">Recommended Resources</h2>
            <div className="space-y-3">
              {summary.summary.metrics.suggested_resources.map((resource, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-[#D8EFE8] rounded-lg">
                  {resource.type === 'hotline' ? (
                    <Phone className="w-5 h-5 text-[#4A90A0]" />
                  ) : (
                    <Heart className="w-5 h-5 text-[#4A90A0]" />
                  )}
                  {resource.link ? (
                    <a 
                      href={resource.link} 
                      className="text-[#4A90A0] hover:text-[#3a7a8a] font-medium"
                    >
                      {resource.label}
                    </a>
                  ) : (
                    <span className="text-gray-700 font-medium">{resource.label}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-xl font-medium text-gray-900 mb-4">Recommended Resources</h2>
            <div className="text-center text-gray-500 py-8">
              No specific resources recommended for this session.
            </div>
          </div>
        )}

        {/* Clinical Notes */}
        {summary.summary.notes && summary.summary.notes.length > 0 ? (
          <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-xl font-medium text-gray-900 mb-4">Session Notes</h2>
            <div className="space-y-2">
              {summary.summary.notes.map((note, index) => (
                <div key={index} className="flex items-start gap-3 text-gray-700">
                  <CheckCircle className="w-4 h-4 text-[#6BAF7A] mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{note}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-xl font-medium text-gray-900 mb-4">Session Notes</h2>
            <div className="text-center text-gray-500 py-8">
              No clinical notes available for this session.
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default RouteComponent;