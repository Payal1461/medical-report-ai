import { useState, type FormEvent } from 'react';
import { Activity, ShieldCheck, HeartPulse } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';

export function AuthPage() {
  const { login, signup } = useAuth();
  const { showError } = useToast();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await signup(name, email, password);
      }
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left — brand panel */}
      <div
        className="hidden lg:flex flex-col justify-between p-12 text-white relative overflow-hidden"
        style={{ background: 'linear-gradient(160deg, #2f8f8a 0%, #3a6b6e 55%, #2d5260 100%)' }}
      >
        <div className="flex items-center gap-2.5 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center backdrop-blur-sm">
            <Activity size={22} />
          </div>
          <span className="text-lg font-semibold tracking-tight">MedInsight AI</span>
        </div>

        <div className="relative z-10 space-y-6 max-w-md">
          <h1 className="text-4xl font-semibold leading-tight" style={{ fontFamily: 'Fraunces, Georgia, serif' }}>
            Understand your lab results, clearly and calmly.
          </h1>
          <p className="text-white/80 leading-relaxed">
            Upload your medical report and get an AI-powered breakdown of every biomarker —
            what it means, why it matters, and what to watch.
          </p>
          <div className="flex flex-col gap-3 pt-2">
            <Feature icon={<ShieldCheck size={18} />} text="Private — your data stays on your account" />
            <Feature icon={<HeartPulse size={18} />} text="Plain-language explanations for every result" />
          </div>
        </div>

        <p className="text-sm text-white/50 relative z-10">
          Not a substitute for professional medical advice.
        </p>

        {/* decorative circles */}
        <div className="absolute -bottom-32 -right-24 w-96 h-96 rounded-full bg-white/5" />
        <div className="absolute -top-20 -right-10 w-64 h-64 rounded-full bg-white/5" />
      </div>

      {/* Right — form */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-sm fade-up">
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'var(--teal-soft)' }}
            >
              <Activity size={22} style={{ color: 'var(--teal)' }} />
            </div>
            <span className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>MedInsight AI</span>
          </div>

          <h2 className="text-2xl font-semibold mb-1.5" style={{ color: 'var(--ink)' }}>
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="text-sm mb-7" style={{ color: 'var(--muted)' }}>
            {mode === 'login'
              ? 'Sign in to view your reports and insights.'
              : 'Start understanding your health reports in minutes.'}
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--ink)' }}>
                  Full name
                </label>
                <input
                  className="input-field"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  autoComplete="name"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--ink)' }}>
                Email
              </label>
              <input
                className="input-field"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--ink)' }}>
                Password
              </label>
              <input
                className="input-field"
                type="password"
                required
                minLength={4}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            <button type="submit" className="btn-primary w-full" disabled={busy}>
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <p className="text-sm text-center mt-6" style={{ color: 'var(--muted)' }}>
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
              className="font-medium hover:underline"
              style={{ color: 'var(--teal)' }}
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function Feature({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2.5 text-white/90">
      <span className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
        {icon}
      </span>
      <span className="text-sm">{text}</span>
    </div>
  );
}
