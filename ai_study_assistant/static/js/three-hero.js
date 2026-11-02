/**
 * StudyAI — Professional WebGL 3D Hero Experience
 * Powered by Three.js
 *
 * Features:
 * - Interactive 3D Quantum Neural Core (Icosahedron + Wireframe cage)
 * - Multi-axis gyroscopic orbital rings with realistic metallic & emission shaders
 * - Orbiting planetary particle nodes in 3D space
 * - Dynamic 3D lighting with mouse-tracking point light
 * - User drag-to-rotate with smooth inertial damping
 */

(function () {
    'use strict';

    if (typeof THREE === 'undefined') {
        console.warn('Three.js not loaded. Skipping 3D hero scene.');
        return;
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const container = document.getElementById('three-hero-container');
    if (!container) return;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();

    const width = container.clientWidth || 450;
    const height = container.clientHeight || 450;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 7.5;

    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    container.appendChild(renderer.domElement);

    // Group to hold all rotating elements
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // --- 1. THE CENTRAL QUANTUM CRYSTAL (Inner Core) ---
    const coreGeo = new THREE.IcosahedronGeometry(1.4, 0); // Faceted low-poly crystal
    const coreMat = new THREE.MeshPhysicalMaterial({
        color: 0x9333ea,
        emissive: 0x4f46e5,
        emissiveIntensity: 0.35,
        roughness: 0.15,
        metalness: 0.65,
        clearcoat: 1.0,
        clearcoatRoughness: 0.1,
        reflectivity: 0.9,
        flatShading: true,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    mainGroup.add(coreMesh);

    // Outer Wireframe Cage for the Crystal
    const wireframeGeo = new THREE.IcosahedronGeometry(1.65, 1);
    const wireframeMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        wireframe: true,
        transparent: true,
        opacity: 0.35,
    });
    const wireframeMesh = new THREE.Mesh(wireframeGeo, wireframeMat);
    mainGroup.add(wireframeMesh);

    // Floating Vertices Nodes on the Wireframe
    const nodeGeo = new THREE.SphereGeometry(0.04, 8, 8);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x56e0ff });
    const posAttr = wireframeGeo.attributes.position;
    const nodeInstanced = new THREE.InstancedMesh(nodeGeo, nodeMat, posAttr.count);
    const dummy = new THREE.Object3D();
    for (let i = 0; i < posAttr.count; i++) {
        dummy.position.set(posAttr.getX(i), posAttr.getY(i), posAttr.getZ(i));
        dummy.updateMatrix();
        nodeInstanced.setMatrixAt(i, dummy.matrix);
    }
    mainGroup.add(nodeInstanced);

    // --- 2. MULTI-AXIS GYROSCOPE ORBITAL RINGS ---
    // Ring 1 (Electric Violet, X-tilt)
    const ring1Geo = new THREE.TorusGeometry(2.35, 0.022, 16, 100);
    const ring1Mat = new THREE.MeshStandardMaterial({
        color: 0xa855f7,
        emissive: 0x7c3aed,
        emissiveIntensity: 0.5,
        roughness: 0.2,
        metalness: 0.8,
    });
    const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1.rotation.x = Math.PI / 3;
    mainGroup.add(ring1);

    // Ring 2 (Hyper Cyan, Y-tilt)
    const ring2Geo = new THREE.TorusGeometry(2.65, 0.018, 16, 100);
    const ring2Mat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0284c7,
        emissiveIntensity: 0.6,
        roughness: 0.2,
        metalness: 0.8,
    });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.y = Math.PI / 4;
    ring2.rotation.z = Math.PI / 6;
    mainGroup.add(ring2);

    // Ring 3 (Outer Neon Amber / Pink Horizon Ring)
    const ring3Geo = new THREE.TorusGeometry(3.0, 0.014, 16, 120);
    const ring3Mat = new THREE.MeshStandardMaterial({
        color: 0xec4899,
        emissive: 0xdb2777,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.7,
    });
    const ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
    ring3.rotation.x = -Math.PI / 5;
    ring3.rotation.y = Math.PI / 3;
    mainGroup.add(ring3);

    // --- 3. ORBITING PLANETARY SATELLITES ---
    const satelliteGroup = new THREE.Group();
    mainGroup.add(satelliteGroup);

    const satGeo1 = new THREE.SphereGeometry(0.12, 16, 16);
    const satMat1 = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x38bdf8,
        emissiveIntensity: 0.8,
        roughness: 0.1,
    });
    const sat1 = new THREE.Mesh(satGeo1, satMat1);
    satelliteGroup.add(sat1);

    const satGeo2 = new THREE.SphereGeometry(0.09, 16, 16);
    const satMat2 = new THREE.MeshStandardMaterial({
        color: 0xa855f7,
        emissive: 0xa855f7,
        emissiveIntensity: 0.8,
        roughness: 0.1,
    });
    const sat2 = new THREE.Mesh(satGeo2, satMat2);
    satelliteGroup.add(sat2);

    // --- 4. ORBITAL PARTICLE CLOUD (Starfield Motes) ---
    const particleCount = 280;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);

    const color1 = new THREE.Color(0xa855f7);
    const color2 = new THREE.Color(0x38bdf8);

    for (let i = 0; i < particleCount; i++) {
        const radius = 2.0 + Math.random() * 2.8;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);

        particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        particlePositions[i * 3 + 2] = radius * Math.cos(phi);

        const mixed = color1.clone().lerp(color2, Math.random());
        particleColors[i * 3] = mixed.r;
        particleColors[i * 3 + 1] = mixed.g;
        particleColors[i * 3 + 2] = mixed.b;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

    const particleMat = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.75,
        blending: THREE.AdditiveBlending,
    });
    const particlePoints = new THREE.Points(particleGeo, particleMat);
    mainGroup.add(particlePoints);

    // --- 5. LIGHTING SETUP ---
    const ambientLight = new THREE.AmbientLight(0x0f172a, 1.2);
    scene.add(ambientLight);

    const violetLight = new THREE.PointLight(0xa855f7, 3.5, 25);
    violetLight.position.set(-4, 4, 3);
    scene.add(violetLight);

    const cyanLight = new THREE.PointLight(0x38bdf8, 3.5, 25);
    cyanLight.position.set(4, -3, 3);
    scene.add(cyanLight);

    // Interactive pointer light
    const mouseLight = new THREE.PointLight(0xffffff, 1.5, 15);
    mouseLight.position.set(0, 0, 5);
    scene.add(mouseLight);

    // --- 6. MOUSE INTERACTION & DRAG-TO-ROTATE ---
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    let isDragging = false;
    let prevPointerX = 0;
    let prevPointerY = 0;
    let velX = 0;
    let velY = 0;

    const heroSection = container.closest('section') || container;

    heroSection.addEventListener('mousemove', (e) => {
        const rect = heroSection.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;

        targetX = x * 1.2;
        targetY = y * 1.2;

        // Position dynamic point light based on pointer
        mouseLight.position.x = x * 8;
        mouseLight.position.y = -y * 8;
    });

    container.addEventListener('pointerdown', (e) => {
        isDragging = true;
        prevPointerX = e.clientX;
        prevPointerY = e.clientY;
        container.style.cursor = 'grabbing';
    });

    window.addEventListener('pointermove', (e) => {
        if (!isDragging) return;
        const deltaX = e.clientX - prevPointerX;
        const deltaY = e.clientY - prevPointerY;
        prevPointerX = e.clientX;
        prevPointerY = e.clientY;

        velX = deltaY * 0.005;
        velY = deltaX * 0.005;

        mainGroup.rotation.x += velX;
        mainGroup.rotation.y += velY;
    });

    window.addEventListener('pointerup', () => {
        isDragging = false;
        container.style.cursor = 'grab';
    });

    container.style.cursor = 'grab';

    // Handle container resize
    function onResize() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (!w || !h) return;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }
    window.addEventListener('resize', onResize);

    // --- 7. ANIMATION LOOP ---
    let clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        const elapsedTime = clock.getElapsedTime();

        // Natural continuous rotation
        coreMesh.rotation.x += 0.004;
        coreMesh.rotation.y += 0.006;

        wireframeMesh.rotation.x -= 0.003;
        wireframeMesh.rotation.y -= 0.005;
        nodeInstanced.rotation.copy(wireframeMesh.rotation);

        ring1.rotation.z += 0.007;
        ring2.rotation.x += 0.005;
        ring3.rotation.z -= 0.004;

        particlePoints.rotation.y += 0.0015;

        // Orbiting satellites
        const satAngle1 = elapsedTime * 1.1;
        sat1.position.x = Math.cos(satAngle1) * 2.35;
        sat1.position.y = Math.sin(satAngle1) * 2.35 * Math.cos(Math.PI / 3);
        sat1.position.z = Math.sin(satAngle1) * 2.35 * Math.sin(Math.PI / 3);

        const satAngle2 = -elapsedTime * 0.85;
        sat2.position.x = Math.cos(satAngle2) * 2.65 * Math.cos(Math.PI / 4);
        sat2.position.y = Math.sin(satAngle2) * 2.65;
        sat2.position.z = Math.cos(satAngle2) * 2.65 * Math.sin(Math.PI / 4);

        // Core floating breathing oscillation
        coreMesh.position.y = Math.sin(elapsedTime * 1.5) * 0.12;
        wireframeMesh.position.y = coreMesh.position.y;
        nodeInstanced.position.y = coreMesh.position.y;

        // Apply mouse tilt with smooth easing (lerp) if not dragging
        if (!isDragging) {
            mouseX += (targetX - mouseX) * 0.06;
            mouseY += (targetY - mouseY) * 0.06;

            mainGroup.rotation.y += (mouseX - mainGroup.rotation.y * 0.15) * 0.04;
            mainGroup.rotation.x += (mouseY - mainGroup.rotation.x * 0.15) * 0.04;

            // Apply residual drag velocity damping
            velX *= 0.94;
            velY *= 0.94;
            mainGroup.rotation.x += velX;
            mainGroup.rotation.y += velY;
        }

        renderer.render(scene, camera);
    }

    animate();
})();
