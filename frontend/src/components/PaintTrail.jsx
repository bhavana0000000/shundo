import { useEffect, useRef } from 'react';

const COLORS = [
  [47, 184, 143],   // teal
  [61, 123, 201],   // blue
  [122, 79, 214],   // violet
  [62, 201, 220],   // cyan
  [90, 159, 214],   // sky blue
];

export default function PaintTrail() {
  const canvasRef = useRef(null);
  const pointsRef = useRef([]);
  const mouseRef = useRef({ x: -1000, y: -1000, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationId;
    let frameCount = 0;

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    function handleMove(e) {
      mouseRef.current = { x: e.clientX, y: e.clientY, active: true };
    }
    window.addEventListener('mousemove', handleMove);

    function animate() {
      frameCount++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Spawn a new drifting blob every couple frames - cheap now since
      // there's no per-shape blur to compute, just a plain filled circle.
      if (mouseRef.current.active && frameCount % 2 === 0) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.25 + Math.random() * 0.5;
        pointsRef.current.push({
          x: mouseRef.current.x,
          y: mouseRef.current.y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          size: 30 + Math.random() * 22,
          life: 1,
        });
        if (pointsRef.current.length > 34) pointsRef.current.shift();
      }

      pointsRef.current.forEach((p) => {
        p.life -= 0.01; // slower fade = longer, smoother trail
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.985;
        p.vy *= 0.985;

        const [r, g, b] = p.color;
        ctx.globalAlpha = Math.max(p.life * 0.6, 0);
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });

      pointsRef.current = pointsRef.current.filter((p) => p.life > 0);
      ctx.globalAlpha = 1;

      animationId = requestAnimationFrame(animate);
    }
    animate();

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMove);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', top: 0, left: 0,
        width: '100vw', height: '100vh',
        zIndex: 1, pointerEvents: 'none',
        filter: 'blur(22px)', // the soft halo look - one cheap GPU blur
                              // pass on the whole canvas, instead of
                              // per-shape blur which caused the lag
        mixBlendMode: 'multiply',
      }}
    />
  );
}
