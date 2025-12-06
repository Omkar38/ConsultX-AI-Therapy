import { createFileRoute } from '@tanstack/react-router'
import TherapyChatInterface from '../components/TherapyChatInterface'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

export const Route = createFileRoute('/chat-old')({
  component: RouteComponent,
})

const queryClient = new QueryClient();

function RouteComponent() {
  return (
    <QueryClientProvider client={queryClient}>
      <TherapyChatInterface />
    </QueryClientProvider>
  );
}
