/**
 * StudyAI — Interactive 3D Ambient Space Engine
 * Generates an interactive 3D starry constellation with parallax depth,
 * kinetic mouse interaction, and a cybernetic horizon grid.
 */

(function () {
    'use strict';

    // Respect reduced motion preferences
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const canvas = document.getElementById('bg-3d-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
        width = canvas.width = window.innerWidth * dpr;
        height = canvas.height = window.innerHeight * dpr;
        ctx.scale(dpr, dpr);
    }
    window.addEventListener('resize', resize);
    resize();

    // Mouse tracking with smooth interpolation (lerp)
    const mouse = {
        x: window.innerWidth / 2,
        y: window.innerHeight / 2,
        targetX: window.innerWidth / 2,
        targetY: window.innerHeight / 2,
        speedX: 0,
        speedY: 0,
        radius: 180,
    };

    window.addEventListener('mousemove', (e) => {
        mouse.targetX = e.clientX;
        mouse.targetY = e.clientY;
    });

    window.addEventListener('mouseleave', () => {
        mouse.targetX = window.innerWidth / 2;
        mouse.targetY = window.innerHeight / 2;
    });

    // 3D Particles array
    const PARTICLE_COUNT = Math.min(Math.floor((window.innerWidth * window.innerHeight) / 14000), 120);
    const particles = [];
    const FOV = 450; // Camera focal length

    const COLOR_PALETTE = [
        'rgba(168, 85, 247, ', // Purple
        'rgba(56, 189, 248, ',  // Cyan
        'rgba(236, 72, 153, ',  // Pink
        'rgba(129, 140, 248, ', // Indigo
    ];

    class Particle3D {
        constructor() {
            this.reset(true);
        }

        reset(initial = false) {
            this.x = (Math.random() - 0.5) * window.innerWidth * 1.6;
            this.y = (Math.random() - 0.5) * window.innerHeight * 1.6;
            this.z = initial ? Math.random() * 1000 : 1000;
            this.vz = 0.4 + Math.random() * 0.8; // Moving forward towards camera
            this.baseSize = 1.2 + Math.random() * 2.2;
            this.color = COLOR_PALETTE[Math.floor(Math.random() * COLOR_PALETTE.length)];
            this.pulse = Math.random() * Math.PI * 2;
            this.pulseSpeed = 0.02 + Math.random() * 0.03;
        }

        update(cameraRotX, cameraRotY) {
            this.z -= this.vz;
            if (this.z <= 10) {
                this.reset();
            }

            this.pulse += this.pulseSpeed;

            // Apply camera parallax rotation
            const cosX = Math.cos(cameraRotX);
            const sinX = Math.sin(cameraRotX);
            const cosY = Math.cos(cameraRotY);
            const sinY = Math.sin(cameraRotY);

            // Rotate around Y axis
            let rx = this.x * cosY + this.z * sinY;
            let rz = -this.x * sinY + this.z * cosY;

            // Rotate around X axis
            let ry = this.y * cosX - rz * sinX;
            rz = this.y * sinX + rz * cosX;

            if (rz <= 20) rz = 20;

            // 3D perspective projection
            const scale = FOV / (FOV + rz);
            this.screenX = window.innerWidth / 2 + rx * scale;
            this.screenY = window.innerHeight / 2 + ry * scale;
            this.screenRadius = Math.max(0.2, this.baseSize * scale * (1 + 0.25 * Math.sin(this.pulse)));
            this.alpha = Math.min(1, Math.max(0.1, (1 - rz / 1100) * 0.85));

            // Mouse proximity kinetic repulsion
            const dx = this.screenX - mouse.x;
            const dy = this.screenY - mouse.y;
            const dist = Math.hypot(dx, dy);
            if (dist < mouse.radius) {
                const force = (1 - dist / mouse.radius) * 15;
                this.screenX += (dx / dist) * force;
                this.screenY += (dy / dist) * force;
            }
        }

        draw(ctx) {
            if (
                this.screenX < -50 ||
                this.screenX > window.innerWidth + 50 ||
                this.screenY < -50 ||
                this.screenY > window.innerHeight + 50
            ) {
                return;
            }

            // Glow aura
            ctx.beginPath();
            ctx.arc(this.screenX, this.screenY, this.screenRadius * 2.2, 0, Math.PI * 2);
            ctx.fillStyle = `${this.color}${this.alpha * 0.25})`;
            ctx.fill();

            // Core point
            ctx.beginPath();
            ctx.arc(this.screenX, this.screenY, this.screenRadius, 0, Math.PI * 2);
            ctx.fillStyle = `${this.color}${this.alpha})`;
            ctx.fill();
        }
    }

    // Initialize particles
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle3D());
    }

    // Floating 3D Geometric wireframe polyhedra (ambient floating artifacts)
    class FloatingGeometry {
        constructor() {
            this.x = (Math.random() - 0.5) * window.innerWidth * 0.8;
            this.y = (Math.random() - 0.5) * window.innerHeight * 0.8;
            this.z = 200 + Math.random() * 400;
            this.size = 28 + Math.random() * 24;
            this.rotX = Math.random() * Math.PI;
            this.rotY = Math.random() * Math.PI;
            this.rotZ = Math.random() * Math.PI;
            this.speedX = (Math.random() - 0.5) * 0.01;
            this.speedY = (Math.random() - 0.5) * 0.01;
            this.speedZ = (Math.random() - 0.5) * 0.01;
            // Octahedron vertices
            this.vertices = [
                [0, 1, 0],
                [0, -1, 0],
                [1, 0, 0],
                [-1, 0, 0],
                [0, 0, 1],
                [0, 0, -1],
            ];
            this.edges = [
                [0, 2], [0, 3], [0, 4], [0, 5],
                [1, 2], [1, 3], [1, 4], [1, 5],
                [2, 4], [4, 3], [3, 5], [5, 2]
            ];
        }

        update(cameraRotX, cameraRotY) {
            this.rotX += this.speedX;
            this.rotY += this.speedY;
            this.rotZ += this.speedZ;

            // Camera tilt response
            const targetX = (mouse.x - window.innerWidth / 2) * 0.0003;
            const targetY = (mouse.y - window.innerHeight / 2) * 0.0003;

            this.renderedVertices = this.vertices.map((v) => {
                let [x, y, z] = v;
                // Scale
                x *= this.size;
                y *= this.size;
                z *= this.size;

                // Rotation around X
                let y1 = y * Math.cos(this.rotX) - z * Math.sin(this.rotX);
                let z1 = y * Math.sin(this.rotX) + z * Math.cos(this.rotX);

                // Rotation around Y
                let x2 = x * Math.cos(this.rotY) + z1 * Math.sin(this.rotY);
                let z2 = -x * Math.sin(this.rotY) + z1 * Math.cos(this.rotY);

                // World position
                let wx = x2 + this.x;
                let wy = y1 + this.y;
                let wz = z2 + this.z;

                // Parallax
                wx += (mouse.x - window.innerWidth / 2) * 0.05;
                wy += (mouse.y - window.innerHeight / 2) * 0.05;

                const scale = FOV / (FOV + wz);
                return {
                    x: window.innerWidth / 2 + wx * scale,
                    y: window.innerHeight / 2 + wy * scale,
                    z: wz,
                };
            });
        }

        draw(ctx) {
            ctx.strokeStyle = 'rgba(139, 92, 246, 0.22)';
            ctx.lineWidth = 1;

            for (const [i1, i2] of this.edges) {
                const p1 = this.renderedVertices[i1];
                const p2 = this.renderedVertices[i2];
                if (!p1 || !p2) continue;

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }

            // Glow vertices
            for (const p of this.renderedVertices) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(56, 189, 248, 0.4)';
                ctx.fill();
            }
        }
    }

    const floatingGeometries = [new FloatingGeometry(), new FloatingGeometry(), new FloatingGeometry()];

    let cameraRotX = 0;
    let cameraRotY = 0;
    let targetCameraRotX = 0;
    let targetCameraRotY = 0;

    // Smooth animation loop
    function animate() {
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

        // Interpolate mouse
        mouse.x += (mouse.targetX - mouse.x) * 0.08;
        mouse.y += (mouse.targetY - mouse.y) * 0.08;

        targetCameraRotY = ((mouse.x - window.innerWidth / 2) / (window.innerWidth / 2)) * 0.12;
        targetCameraRotX = -((mouse.y - window.innerHeight / 2) / (window.innerHeight / 2)) * 0.12;

        cameraRotX += (targetCameraRotX - cameraRotX) * 0.05;
        cameraRotY += (targetCameraRotY - cameraRotY) * 0.05;

        // Update and draw particles
        for (let i = 0; i < particles.length; i++) {
            particles[i].update(cameraRotX, cameraRotY);
            particles[i].draw(ctx);
        }

        // Draw constellation lines between nearby particles
        const MAX_CONNECT_DIST = 95;
        ctx.lineWidth = 0.65;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const dx = p1.screenX - p2.screenX;
                const dy = p1.screenY - p2.screenY;
                const dist = Math.hypot(dx, dy);

                if (dist < MAX_CONNECT_DIST) {
                    const alpha = (1 - dist / MAX_CONNECT_DIST) * 0.22 * Math.min(p1.alpha, p2.alpha);
                    ctx.strokeStyle = `rgba(168, 85, 247, ${alpha})`;
                    ctx.beginPath();
                    ctx.moveTo(p1.screenX, p1.screenY);
                    ctx.lineTo(p2.screenX, p2.screenY);
                    ctx.stroke();
                }
            }
        }

        // Draw floating geometries
        for (const geo of floatingGeometries) {
            geo.update(cameraRotX, cameraRotY);
            geo.draw(ctx);
        }

        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
})();
