import { useTheme } from 'next-themes';
import { ThemeToggleButton } from '@/components/ui/theme-toggle-button';
import { useThemeTransition } from '@/components/ui/theme-transition';

const getResolvedTheme = (theme: string | undefined) => {
  if (theme === 'system' || !theme) {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
};

export function ModeToggle() {
  const { theme, setTheme } = useTheme();
  const { startTransition } = useThemeTransition();

  const handleToggle = () => {
    const resolvedTheme = getResolvedTheme(theme);
    const nextTheme = resolvedTheme === 'dark' ? 'light' : 'dark';
    startTransition(() => setTheme(nextTheme), { variant: 'circle', start: 'top-right' });
  };

  return <ThemeToggleButton theme={getResolvedTheme(theme)} onClick={handleToggle} />;
}
