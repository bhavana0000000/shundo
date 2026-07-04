import { useEffect, useRef } from 'react';

const COLORS = ['#2fb88f', '#3d7bc9', '#7a4fd6', '#3ec9dc', '#5a9fd6'];

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

    function drawPoint(p) {
      // Cheap radial gradient instead of ctx.filter blur - dramatically
      // faster since browsers don't have to run a real blur raster pass
      // on every shape, every frame.
      const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size);
      gradient.addColorStop(0, p.color);
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }

    function animate() {
      frameCount++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.globalCompositeOperation = 'screen';

      // Generate a new point roughly every 4th frame instead of every 2nd -
      // fewer points to draw = less work per frame, still looks continuous.
      if (mouseRef.current.active && frameCount % 4 === 0) {
        pointsRef.current.push({
          x: mouseRef.current.x,
          y: mouseRef.current.y,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          size: 22 + Math.random() * 14,
          life: 1,
        });
        // Much smaller cap (30 vs 90) - the biggest single perf win, since
        // every point costs a full radial-gradient + fill each frame.
        if (pointsRef.current.length > 30) pointsRef.current.shift();
      }

      pointsRef.current.forEach((p) => {
        p.life -= 0.02; // fades a bit faster to match the smaller cap
        ctx.globalAlpha = Math.max(p.life * 0.4, 0);
        drawPoint(p);
      });

      pointsRef.current = pointsRef.current.filter((p) => p.life > 0);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';

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
      }}
    />
  );
}
