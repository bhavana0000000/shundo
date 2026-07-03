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

    function animate() {
      frameCount++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.globalCompositeOperation = 'screen';

      if (mouseRef.current.active && frameCount % 2 === 0) {
        pointsRef.current.push({
          x: mouseRef.current.x,
          y: mouseRef.current.y,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          size: 20 + Math.random() * 16,
          life: 1,
        });
        if (pointsRef.current.length > 90) pointsRef.current.shift();
      }

      pointsRef.current.forEach((p) => {
        p.life -= 0.01;
        ctx.globalAlpha = Math.max(p.life * 0.45, 0);
        ctx.fillStyle = p.color;
        ctx.filter = 'blur(16px)';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * (1.4 - p.life * 0.4), 0, Math.PI * 2);
        ctx.fill();
      });

      pointsRef.current = pointsRef.current.filter((p) => p.life > 0);
      ctx.globalAlpha = 1;
      ctx.filter = 'none';
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
