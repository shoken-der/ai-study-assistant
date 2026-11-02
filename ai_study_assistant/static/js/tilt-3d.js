/**
 * StudyAI — 3D Interactive Tilt & Holographic Lighting Engine
 * Provides physics-based 3D card tilt, dynamic specular glare reflections,
 * cursor glow aura, and hero 3D gyroscopic interactive parallax.
 */

(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // 1. Ambient Cursor Glow Follower
    function initCursorGlow() {
        const glow = document.createElement('div');
        glow.className = 'cursor-glow';
        document.body.appendChild(glow);

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let currentX = mouseX;
        let currentY = mouseY;
        let isVisible = false;

        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            if (!isVisible) {
                glow.style.opacity = '1';
                isVisible = true;
            }
        });

        document.addEventListener('mouseleave', () => {
            glow.style.opacity = '0';
            isVisible = false;
        });

        function renderGlow() {
            currentX += (mouseX - currentX) * 0.12;
            currentY += (mouseY - currentY) * 0.12;
            glow.style.transform = `translate3d(${currentX}px, ${currentY}px, 0) translate(-50%, -50%)`;
            requestAnimationFrame(renderGlow);
        }
        renderGlow();
    }

    // 2. 3D Card Tilt with Specular Glare
    function init3DTilt() {
        if (prefersReducedMotion) return;

        // Select all cards to elevate into 3D
        const cards = document.querySelectorAll(
            '.feature-card, .progress-stat, .interactive-3d-card, .glass-card:not(.no-tilt)'
        );

        cards.forEach((card) => {
            // Avoid applying tilt to huge containers or forms that don't need intense tilt
            if (card.offsetHeight > 750 || card.classList.contains('no-tilt')) return;

            // Create specular glare overlay if not present
            let glare = card.querySelector('.card-3d-glare');
            if (!glare) {
                glare = document.createElement('div');
                glare.className = 'card-3d-glare';
                card.appendChild(glare);
            }

            let bounds = null;
            let isHovered = false;
            let rafId = null;

            card.addEventListener('mouseenter', () => {
                bounds = card.getBoundingClientRect();
                isHovered = true;
                card.style.transition = 'transform 0.15s ease-out, box-shadow 0.25s ease';
            });

            card.addEventListener('mousemove', (e) => {
                if (!bounds) bounds = card.getBoundingClientRect();

                const mouseX = e.clientX - bounds.left;
                const mouseY = e.clientY - bounds.top;

                // Normalize from -0.5 to 0.5
                const xPct = mouseX / bounds.width - 0.5;
                const yPct = mouseY / bounds.height - 0.5;

                // Max rotation degrees
                const maxRotX = 14;
                const maxRotY = 14;

                const rotX = -yPct * maxRotX;
                const rotY = xPct * maxRotY;

                if (rafId) cancelAnimationFrame(rafId);
                rafId = requestAnimationFrame(() => {
                    card.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateZ(12px) scale3d(1.02, 1.02, 1.02)`;

                    // Move glare highlight to cursor position
                    const glareX = (mouseX / bounds.width) * 100;
                    const glareY = (mouseY / bounds.height) * 100;
                    glare.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0.04) 40%, transparent 75%)`;
                    glare.style.opacity = '1';

                    // Update dynamic glowing border angle
                    const angleRad = Math.atan2(mouseY - bounds.height / 2, mouseX - bounds.width / 2);
                    const angleDeg = ((angleRad * 180) / Math.PI + 360) % 360;
                    card.style.setProperty('--glow-angle', `${angleDeg}deg`);
                });
            });

            card.addEventListener('mouseleave', () => {
                isHovered = false;
                bounds = null;
                if (rafId) cancelAnimationFrame(rafId);

                card.style.transition = 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.6s ease';
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px) scale3d(1, 1, 1)';
                if (glare) {
                    glare.style.opacity = '0';
                }
            });
        });
    }

    // 3. Hero Visual 3D Gyroscope Mouse Parallax
    function initHeroGyroParallax() {
        if (prefersReducedMotion) return;

        const heroVisual = document.querySelector('.hero-visual');
        const orbit = document.querySelector('.orbit');
        if (!heroVisual || !orbit) return;

        let bounds = null;
        let isHovered = false;

        const heroSection = heroVisual.closest('section') || heroVisual;

        heroSection.addEventListener('mousemove', (e) => {
            if (!bounds) bounds = heroSection.getBoundingClientRect();

            const x = (e.clientX - bounds.left) / bounds.width - 0.5;
            const y = (e.clientY - bounds.top) / bounds.height - 0.5;

            const tiltX = -y * 28;
            const tiltY = x * 28;

            orbit.style.transform = `perspective(1200px) rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg) scale(1.05)`;
        });

        heroSection.addEventListener('mouseleave', () => {
            bounds = null;
            orbit.style.transition = 'transform 1s cubic-bezier(0.25, 1, 0.5, 1)';
            orbit.style.transform = 'perspective(1200px) rotateX(0deg) rotateY(0deg) scale(1)';
            setTimeout(() => {
                orbit.style.transition = '';
            }, 1000);
        });
    }

    // 4. Interactive 3D Flashcard Flip Setup
    function initFlashcard3D() {
        const flashcards = document.querySelectorAll('.flip-card');
        flashcards.forEach((card) => {
            if (card.dataset.flipBound) return;
            card.dataset.flipBound = 'true';
            card.addEventListener('click', function (e) {
                // If the click is inside a link or button other than the card itself, do not flip
                if (e.target.closest('a') || (e.target.tagName === 'BUTTON' && e.target !== card)) return;
                this.classList.toggle('is-flipped');
            });
        });
    }

    // 5. Button Ripple & 3D Shimmer
    function initButtonEffects() {
        const glowButtons = document.querySelectorAll('.btn-glow, .btn-glass, .btn-cyber');
        glowButtons.forEach((btn) => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                btn.style.setProperty('--btn-x', `${x}px`);
                btn.style.setProperty('--btn-y', `${y}px`);
            });
        });
    }

    // Initialize all 3D features once DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initCursorGlow();
            init3DTilt();
            initHeroGyroParallax();
            initFlashcard3D();
            initButtonEffects();
        });
    } else {
        initCursorGlow();
        init3DTilt();
        initHeroGyroParallax();
        initFlashcard3D();
        initButtonEffects();
    }
})();
