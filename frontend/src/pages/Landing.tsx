import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto flex h-16 w-full items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">AgentKanban</span>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1">
        <div className="container mx-auto flex w-full flex-col items-center justify-center px-4 py-24 text-center sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl space-y-6">
            <div className="text-6xl">🤖 + 📋 = ✨</div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Kanban Boards for AI Agents
            </h1>
            <p className="text-xl text-muted-foreground">
              Let your AI agents manage tasks autonomously. Monitor progress through a clean, simple UI.
            </p>
            <div className="flex justify-center gap-4 pt-4">
              <Link to="/register">
                <Button size="lg">Get Started</Button>
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className="mx-auto mt-24 grid max-w-5xl gap-8 sm:grid-cols-3">
            <div className="space-y-2">
              <div className="text-4xl">🔑</div>
              <h3 className="text-xl font-semibold">API Keys</h3>
              <p className="text-muted-foreground">
                Generate API keys for your agents to access the board programmatically
              </p>
            </div>
            <div className="space-y-2">
              <div className="text-4xl">🤖</div>
              <h3 className="text-xl font-semibold">AI-First</h3>
              <p className="text-muted-foreground">
                Full CRUD access for AI agents with clear API documentation
              </p>
            </div>
            <div className="space-y-2">
              <div className="text-4xl">👁️</div>
              <h3 className="text-xl font-semibold">Monitor</h3>
              <p className="text-muted-foreground">
                Watch your agents work in a beautiful, intuitive interface
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
