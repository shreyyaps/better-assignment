import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/clerk-react";

import Dashboard from "./Dashboard";

const App = () => {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#1f2937,#0b0f1a_60%)]">
      <SignedIn>
        <header className="px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-white/50">AI Browser Agent</p>
            <h1 className="text-2xl font-display font-semibold">Prompt Orchestrator</h1>
          </div>
          <UserButton afterSignOutUrl="/" />
        </header>
        <Dashboard />
      </SignedIn>
      <SignedOut>
        <div className="min-h-screen flex items-center justify-center">
          <div className="card p-10 text-center max-w-md">
            <h1 className="text-3xl font-display font-semibold mb-4">AI Browser Agent</h1>
            <p className="text-white/70 mb-6">
              Sign in to run AI-orchestrated browser tasks safely in headless mode.
            </p>
            <SignInButton mode="modal">
              <button className="px-6 py-3 rounded-full bg-ember text-black font-semibold">
                Sign In
              </button>
            </SignInButton>
          </div>
        </div>
      </SignedOut>
    </div>
  );
};

export default App;
