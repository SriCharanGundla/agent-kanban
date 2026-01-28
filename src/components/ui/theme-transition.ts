const resolveOrigin = (start: string) => {
  const width = window.innerWidth;
  const height = window.innerHeight;
  const inset = 24;

  switch (start) {
    case 'top-left':
      return { x: inset, y: inset };
    case 'top-right':
      return { x: width - inset, y: inset };
    case 'bottom-left':
      return { x: inset, y: height - inset };
    case 'bottom-right':
      return { x: width - inset, y: height - inset };
    case 'center':
    default:
      return { x: width / 2, y: height / 2 };
  }
};

export const useThemeTransition = () => {
  const startTransition = (
    update: () => void,
    { start = 'center', variant = 'circle' }: { start?: string; variant?: string } = {}
  ) => {
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      update();
      return;
    }

    const prefersReducedMotion = window.matchMedia('(prefers-reduce-motion: reduce)').matches;
    if (!('startViewTransition' in document) || prefersReducedMotion) {
      update();
      return;
    }

    const { x, y } = resolveOrigin(start);
    const maxRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    );

    const transition = (document as Document & { startViewTransition?: (callback: () => void) => { ready: Promise<void> } }).startViewTransition?.(() => {
      update();
    });

    if (!transition) {
      update();
      return;
    }

    transition.ready.then(() => {
      if (variant !== 'circle') return;
      const clip = [
        { clipPath: `circle(0px at ${x}px ${y}px)` },
        { clipPath: `circle(${maxRadius}px at ${x}px ${y}px)` },
      ];
      document.documentElement.animate(clip, {
        duration: 480,
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
        pseudoElement: '::view-transition-new(root)',
      });
    });
  };

  return { startTransition };
};
