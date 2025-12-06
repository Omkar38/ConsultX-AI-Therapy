import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";

export type SummaryMetrics = {
  primaryEmotion: string;
  sentiment: "positive" | "neutral" | "negative";
  userMessages: number;
  aiConfidence: number; // 0-100
};

// Mocked submit function
const mockSubmitFeedback = async (_payload: { rating: number; comment?: string }) => {
  await new Promise((r) => setTimeout(r, 800 + Math.random() * 800));
  return { ok: true };
};

export function SessionSummaryCard({ metrics }: { metrics: SummaryMetrics }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold">Session Summary</h3>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-500">Primary emotion</div>
          <div className="text-base font-medium">{metrics.primaryEmotion}</div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-500">Sentiment trend</div>
          <div className="text-base font-medium capitalize">{metrics.sentiment}</div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-500">User messages</div>
          <div className="text-base font-medium">{metrics.userMessages}</div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-500">AI confidence</div>
          <div className="text-base font-medium">{metrics.aiConfidence}%</div>
        </div>
      </div>
    </div>
  );
}

export function FeedbackForm({ onSuccess }: { onSuccess?: () => void }) {
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [touched, setTouched] = useState(false);

  const mutation = useMutation({
    mutationFn: async (payload: { rating: number; comment?: string }) => {
      return mockSubmitFeedback(payload);
    },
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!rating) return;
    try {
      setIsSubmitting(true);
      await mutation.mutateAsync({ rating, comment: comment.trim() || undefined });
      setRating(null);
      setComment("");
      setTouched(false);
      setIsSubmitting(false);
      onSuccess?.();
    } catch (err) {
      setIsSubmitting(false);
    }
  };

  const ratingError = touched && !rating;

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-4 mt-4">
      <h3 className="text-lg font-semibold">Feedback</h3>

      <div className="mt-3">
        <label className="block text-sm font-medium text-gray-700">
          Your rating <span className="text-red-500">*</span>
        </label>
        <div className="mt-2 flex items-center gap-2" role="radiogroup" aria-label="Star rating">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setRating(n)}
              aria-checked={rating === n}
              role="radio"
              className={`px-3 py-2 rounded-md border ${
                rating === n ? "bg-yellow-400 text-white border-yellow-500" : "bg-white"
              }`}
            >
              {n}★
            </button>
          ))}
        </div>
        {ratingError && <div className="text-red-600 text-sm mt-2">Please provide a rating.</div>}
      </div>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700">How did you feel about this session? (optional)</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          className="mt-2 w-full rounded-md border px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Share anything you'd like..."
        />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="submit"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Submitting..." : "Submit Feedback"}
        </button>
        {mutation.isSuccess && <div className="text-green-600">Thanks for your feedback!</div>}
        {mutation.isError && <div className="text-red-600">Failed to submit. Try again.</div>}
      </div>
    </form>
  );
}

export default function SessionFeedback({ metrics }: { metrics: SummaryMetrics }) {
  return (
    <div className="h-fit bg-gray-50 py-8 px-4 flex justify-center">
      <div className="max-w-2xl w-full">
        <SessionSummaryCard metrics={metrics} />
        <FeedbackForm onSuccess={() => {}} />
      </div>
    </div>
  );
}
