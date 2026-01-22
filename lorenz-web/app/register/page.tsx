'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirm_password) {
      setError('Le password non coincidono');
      toast({
        title: 'Errore',
        description: 'Le password non coincidono',
        variant: 'destructive',
      });
      return;
    }

    if (formData.password.length < 8) {
      setError('La password deve essere di almeno 8 caratteri');
      toast({
        title: 'Errore',
        description: 'La password deve essere di almeno 8 caratteri',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
      });
      api.setToken(response.access_token);
      toast({
        title: 'Registrazione completata',
        description: 'Benvenuto in LORENZ!',
        variant: 'success',
      });
      router.push('/onboarding');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        toast({
          title: 'Errore di registrazione',
          description: err.message,
          variant: 'destructive',
        });
      } else {
        setError('Si è verificato un errore. Riprova.');
        toast({
          title: 'Errore',
          description: 'Si è verificato un errore. Riprova.',
          variant: 'destructive',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 lorenz-gradient items-center justify-center">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-white mb-4">LORENZ</h1>
          <p className="text-xl text-white/80 max-w-md">
            Il tuo assistente personale AI per gestire email, calendario e comunicazioni
          </p>
        </div>
      </div>

      {/* Right side - Register form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-4xl font-bold lorenz-gradient-text">LORENZ</h1>
          </div>

          <h2 className="text-2xl font-semibold mb-2">Crea un account</h2>
          <p className="text-muted-foreground mb-8">
            Inizia a usare il tuo assistente personale AI
          </p>

          {error && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium mb-2">
                Nome Completo
              </label>
              <input
                id="full_name"
                type="text"
                value={formData.full_name}
                onChange={(e) =>
                  setFormData({ ...formData, full_name: e.target.value })
                }
                className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                placeholder="Mario Rossi"
                required
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className="w-full px-4 py-2 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                placeholder="nome@esempio.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="w-full px-4 py-2 pr-12 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium mb-2">
                Conferma Password
              </label>
              <div className="relative">
                <input
                  id="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirm_password}
                  onChange={(e) =>
                    setFormData({ ...formData, confirm_password: e.target.value })
                  }
                  className="w-full px-4 py-2 pr-12 rounded-lg bg-muted border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 lorenz-gradient text-white font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Registrazione in corso...' : 'Registrati'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-muted-foreground">
              Hai già un account?{' '}
              <Link href="/login" className="text-primary hover:underline">
                Accedi
              </Link>
            </p>
          </div>

          <p className="mt-8 text-xs text-muted-foreground text-center">
            Registrandoti accetti i nostri{' '}
            <a href="#" className="text-primary hover:underline">
              Termini di Servizio
            </a>{' '}
            e la{' '}
            <a href="#" className="text-primary hover:underline">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
