'use client';

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export function RotatingGlobe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    const context = canvas?.getContext('2d');
    if (!canvas || !container || !context) return;

    let frame = 0;
    let width = 0;
    let height = 0;
    let rotation = 0;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const graticule = d3.geoGraticule10();
    const dots = Array.from({ length: 260 }, (_, index) => ({
      longitude: ((index * 137.508) % 360) - 180,
      latitude: Math.asin(1 - (2 * (index + .5)) / 260) * (180 / Math.PI),
    }));

    const draw = () => {
      const dpr = window.devicePixelRatio || 1;
      width = Math.max(240, container.clientWidth);
      height = Math.max(280, Math.min(440, width * .82));
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, width, height);

      const radius = Math.min(width, height) * .39;
      const projection = d3.geoOrthographic().scale(radius).translate([width * .52, height * .5]).clipAngle(90).rotate([rotation, -12]);
      const path = d3.geoPath(projection, context);
      context.beginPath();
      path({ type: 'Sphere' });
      context.fillStyle = 'rgba(8, 21, 38, .72)';
      context.fill();
      context.strokeStyle = 'rgba(110, 231, 249, .5)';
      context.lineWidth = 1;
      context.stroke();
      context.beginPath();
      path(graticule);
      context.strokeStyle = 'rgba(110, 231, 249, .18)';
      context.stroke();

      for (const dot of dots) {
        const point = projection([dot.longitude, dot.latitude]);
        if (!point) continue;
        const distance = Math.hypot(point[0] - width * .52, point[1] - height * .5);
        if (distance > radius) continue;
        const alpha = Math.max(.12, 1 - distance / radius) * .62;
        context.beginPath();
        context.arc(point[0], point[1], 1.25, 0, Math.PI * 2);
        context.fillStyle = `rgba(110, 231, 249, ${alpha})`;
        context.fill();
      }
    };

    const animate = () => {
      if (!reduceMotion.matches) rotation = (rotation + .14) % 360;
      draw();
      frame = requestAnimationFrame(animate);
    };

    const observer = new ResizeObserver(draw);
    observer.observe(container);
    draw();
    frame = requestAnimationFrame(animate);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); };
  }, []);

  return <figure className="ds-globe" aria-label="Global community signal map"><canvas ref={canvasRef} aria-hidden="true" /><figcaption>Global community signal map</figcaption></figure>;
}
