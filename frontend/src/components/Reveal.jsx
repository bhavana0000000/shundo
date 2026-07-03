import { useReveal } from '../hooks/useReveal';

export default function Reveal({ children, delay = 0, className = '' }) {
  const [ref, visible] = useReveal();

  return (
    <div
      ref={ref}
      className={`reveal ${visible ? 'reveal-in' : ''} ${className}`}
      style={{ transitionDelay: visible ? `${delay}ms` : '0ms' }}
    >
      {children}
    </div>
  );
}
