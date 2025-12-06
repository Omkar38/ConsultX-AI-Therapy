import { Link } from "@tanstack/react-router";

export default function Header() {
  return (
    <header className="h-[10%] w-full bg-white/60 backdrop-blur-sm border-b">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-2xl font-semibold text-slate-900">ConsultX</Link>

        <nav className="hidden sm:flex items-center gap-4">
          <Link to="/chat" className="text-sm text-slate-600 hover:text-slate-900">Chat</Link>
          <Link to="/feedback" className="text-sm text-slate-600 hover:text-slate-900">Feedback</Link>
        </nav>

        <div className="sm:hidden">
          <Link to="/chat" className="text-sm text-slate-600 hover:text-slate-900">Chat</Link>
        </div>
      </div>
    </header>
  );
}
