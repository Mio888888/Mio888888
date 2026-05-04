<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Mio - GitHub Link Splash Screen</title>
    <style>
        body { margin: 0; padding: 0; background-color: #f7f9f8; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif; overflow: hidden; }
        #splash-container { position: relative; width: 960px; height: 540px; overflow: hidden; background: radial-gradient(circle at center, #ffffff 0%, #eef3f0 100%); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.05); border-radius: 16px; }
        #webgl-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
        
        /* 调整底部 UI 层的布局 */
        #ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; pointer-events: none; padding-bottom: 50px; box-sizing: border-box; }

        /* 新增的 GitHub 链接样式 */
        .github-link {
            pointer-events: auto; /* 允许点击 */
            text-decoration: none;
            font-size: 15px;
            font-weight: 600;
            color: #00d26a; /* 品牌薄荷绿 */
            letter-spacing: 1px;
            padding: 10px 24px;
            border-radius: 30px;
            border: 1px solid rgba(0, 210, 106, 0.2);
            background: rgba(0, 210, 106, 0.05);
            backdrop-filter: blur(4px); /* 毛玻璃效果 */
            opacity: 0;
            transform: translateY(10px);
            animation: linkFadeIn 1s ease-out 2.8s forwards;
            transition: all 0.3s ease;
        }

        /* 鼠标悬停时的优雅交互 */
        .github-link:hover {
            background: rgba(0, 210, 106, 0.15);
            transform: translateY(-2px) !important; /* 覆盖动画结束后的状态 */
            box-shadow: 0 6px 16px rgba(0, 210, 106, 0.2);
            color: #00b359;
        }

        @keyframes linkFadeIn {
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    <script type="importmap">
        { "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js" } }
    </script>

</head>
<body>
    <div id="splash-container">
        <div id="webgl-canvas"></div>
        <div id="ui-layer">
            <!-- 替换了原本的 equalizer，改为可点击的 a 标签 -->
            <a href="https://github.com/你的用户名" target="_blank" class="github-link">This is my GitHub</a>
        </div>
    </div>

    <script type="module">
        import * as THREE from 'three';

        const container = document.getElementById('webgl-canvas');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const scene = new THREE.Scene();
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
        camera.position.z = 45;

        // 生成高清晰柔和圆形粒子贴图
        function createCircleTexture(blur = 14) {
            const canvas = document.createElement('canvas');
            canvas.width = 64; canvas.height = 64;
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
            gradient.addColorStop(0, 'rgba(255,255,255,1)');
            gradient.addColorStop(0.3, 'rgba(255,255,255,0.8)');
            gradient.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 64, 64);
            return new THREE.CanvasTexture(canvas);
        }
        const particleTexture = createCircleTexture();
        const largeBokehTexture = createCircleTexture(20);

        // --- 1. 背景气泡粒子 ---
        const bgParticleCount = 800;
        const bgGeometry = new THREE.BufferGeometry();
        const bgPositions = new Float32Array(bgParticleCount * 3);
        const bgColors = new Float32Array(bgParticleCount * 3);

        const colorBrand = new THREE.Color("#00d26a");
        const colorLight = new THREE.Color("#a3e8b8");
        const colorGray = new THREE.Color("#e0e8e4");

        for (let i = 0; i < bgParticleCount; i++) {
            bgPositions[i * 3] = (Math.random() - 0.5) * 80;
            bgPositions[i * 3 + 1] = (Math.random() - 0.5) * 80;
            bgPositions[i * 3 + 2] = (Math.random() - 0.5) * 80;

            const randColor = Math.random();
            let c = colorGray;
            if (randColor > 0.7) c = colorLight;
            if (randColor > 0.9) c = colorBrand;

            bgColors[i * 3] = c.r; bgColors[i * 3 + 1] = c.g; bgColors[i * 3 + 2] = c.b;
        }

        bgGeometry.setAttribute('position', new THREE.BufferAttribute(bgPositions, 3));
        bgGeometry.setAttribute('color', new THREE.BufferAttribute(bgColors, 3));

        const bgMaterial = new THREE.PointsMaterial({
            size: 0.4, vertexColors: true, map: particleTexture, transparent: true, opacity: 0.5,
            blending: THREE.NormalBlending, depthWrite: false
        });
        const bgParticles = new THREE.Points(bgGeometry, bgMaterial);
        scene.add(bgParticles);


        // --- 2. 前景散景层 ---
        const bokehGroup = new THREE.Group();
        for(let i=0; i<15; i++) {
            const mat = new THREE.SpriteMaterial({
                map: largeBokehTexture, transparent: true, opacity: Math.random() * 0.2 + 0.05,
                blending: THREE.NormalBlending, color: Math.random() > 0.5 ? 0x00d26a : 0x00e88a
            });
            const sprite = new THREE.Sprite(mat);
            sprite.position.set((Math.random() - 0.5) * 60, (Math.random() - 0.5) * 60, 15 + Math.random() * 20);
            const scale = Math.random() * 15 + 5;
            sprite.scale.set(scale, scale, 1);
            sprite.userData = { vy: Math.random() * 0.03 + 0.01, rx: Math.random() * 0.02 };
            bokehGroup.add(sprite);
        }
        scene.add(bokehGroup);


        // --- 3. 高清粒子文字 "Mio" ---
        function getTextParticleData(text) {
            const tCanvas = document.createElement('canvas');
            const tWidth = 600; const tHeight = 300;
            tCanvas.width = tWidth; tCanvas.height = tHeight;
            const ctx = tCanvas.getContext('2d', { willReadFrequently: true });

            ctx.fillStyle = '#ffffff';
            ctx.font = '900 160px Arial, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, tWidth / 2, tHeight / 2);

            const imgData = ctx.getImageData(0, 0, tWidth, tHeight).data;
            const targetPos = [];
            const startPos = [];
            const pColors = [];

            const textColorCore = new THREE.Color("#1a1a1a");
            const textColorHighlight = new THREE.Color("#00d26a");

            const step = 2;

            for (let y = 0; y < tHeight; y += step) {
                for (let x = 0; x < tWidth; x += step) {
                    const index = (y * tWidth + x) * 4;
                    if (imgData[index + 3] > 128) {
                        const px = (x - tWidth / 2) * 0.08;
                        const py = -(y - tHeight / 2) * 0.08;
                        const pz = (Math.random() - 0.5) * 2;

                        targetPos.push(px, py, pz);

                        startPos.push(
                            px + (Math.random() - 0.5) * 80,
                            py + (Math.random() - 0.5) * 80,
                            pz + (Math.random() - 0.5) * 80
                        );

                        const c = Math.random() > 0.4 ? textColorHighlight : textColorCore;
                        pColors.push(c.r, c.g, c.b);
                    }
                }
            }
            return { targetPos, startPos, pColors };
        }

        const textData = getTextParticleData('Mio');
        const textGeometry = new THREE.BufferGeometry();
        textGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(textData.startPos), 3));
        textGeometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(textData.pColors), 3));

        const textMaterial = new THREE.PointsMaterial({
            size: 0.2,
            vertexColors: true,
            map: particleTexture,
            transparent: true,
            opacity: 0.9,
            blending: THREE.NormalBlending,
            depthWrite: false
        });

        const textParticles = new THREE.Points(textGeometry, textMaterial);
        textParticles.position.y = 1;
        scene.add(textParticles);


        // --- 4. 动画控制 ---
        let clock = new THREE.Clock();
        let convergeProgress = 0;

        function animate() {
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            const elapsedTime = clock.getElapsedTime();

            bgParticles.rotation.y = elapsedTime * 0.05;
            bokehGroup.children.forEach(sprite => {
                sprite.position.y += sprite.userData.vy;
                sprite.position.x += Math.sin(elapsedTime + sprite.position.y) * sprite.userData.rx;
                if(sprite.position.y > 40) sprite.position.y = -40;
            });

            convergeProgress += (1 - convergeProgress) * delta * 1.5;

            const textPosArray = textParticles.geometry.attributes.position.array;
            for (let i = 0; i < textData.targetPos.length / 3; i++) {
                let ix = i * 3, iy = i * 3 + 1, iz = i * 3 + 2;

                textPosArray[ix] = THREE.MathUtils.lerp(textPosArray[ix], textData.targetPos[ix], convergeProgress * 0.03);
                textPosArray[iy] = THREE.MathUtils.lerp(textPosArray[iy], textData.targetPos[iy], convergeProgress * 0.03);
                textPosArray[iz] = THREE.MathUtils.lerp(textPosArray[iz], textData.targetPos[iz], convergeProgress * 0.03);

                if (convergeProgress > 0.9) {
                    textPosArray[ix] += Math.sin(elapsedTime * 1.5 + iy) * 0.001;
                    textPosArray[iy] += Math.cos(elapsedTime * 1.5 + ix) * 0.001;
                }
            }
            textParticles.geometry.attributes.position.needsUpdate = true;

            textParticles.position.y = 1 + Math.sin(elapsedTime * 1.2) * 0.15;

            camera.position.z = THREE.MathUtils.lerp(camera.position.z, 22 + Math.sin(elapsedTime * 0.3) * 1.0, 0.02);
            camera.lookAt(0, 0, 0);

            renderer.render(scene, camera);
        }

        animate();
    </script>

</body>
</html>
