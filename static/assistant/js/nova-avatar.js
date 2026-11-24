import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const VALID_EMOTIONS = new Set([
    'neutral',
    'pensando',
    'hablando',
    'feliz',
    'celebrando',
    'disculpa',
]);

const CONFETTI_COLORS = [0xff6b35, 0x1e8f75, 0xfbbf24, 0x38bdf8, 0xf472b6];

/**
 * Procedural low-poly NovaGo delivery motorcycle + rider/visor head + cargo box.
 * Used as seamless fallback when static/assistant/models/nova.glb is not present.
 */
function buildProceduralMoto() {
    const root = new THREE.Group();
    const motoGroup = new THREE.Group();
    root.add(motoGroup);

    const matOrange = new THREE.MeshStandardMaterial({
        color: 0xff6b35,
        roughness: 0.35,
        metalness: 0.15,
    });
    const matSlate = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.55,
        metalness: 0.35,
    });
    const matTire = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.85,
        metalness: 0.1,
    });
    const matMetal = new THREE.MeshStandardMaterial({
        color: 0x94a3b8,
        roughness: 0.3,
        metalness: 0.75,
    });
    const matWhite = new THREE.MeshStandardMaterial({
        color: 0xf8fafc,
        roughness: 0.4,
        metalness: 0.1,
    });
    const matVisor = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0ea5e9,
        emissiveIntensity: 0.55,
        roughness: 0.15,
        metalness: 0.4,
    });
    const matHeadlight = new THREE.MeshStandardMaterial({
        color: 0xfef08a,
        emissive: 0xfacc15,
        emissiveIntensity: 0.8,
        roughness: 0.2,
    });

    // Wheels
    const wheelGeo = new THREE.TorusGeometry(0.28, 0.09, 10, 20);
    const hubGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.12, 12);
    hubGeo.rotateX(Math.PI / 2);

    const makeWheel = (xPos) => {
        const wheel = new THREE.Group();
        const tire = new THREE.Mesh(wheelGeo, matTire);
        const hub = new THREE.Mesh(hubGeo, matMetal);
        wheel.add(tire, hub);
        wheel.position.set(xPos, 0.3, 0);
        return wheel;
    };

    const frontWheel = makeWheel(0.72);
    const rearWheel = makeWheel(-0.68);
    motoGroup.add(frontWheel, rearWheel);

    // Chassis & engine block
    const chassis = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.26, 0.34), matSlate);
    chassis.position.set(0.02, 0.48, 0);
    motoGroup.add(chassis);

    const fairing = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.34, 0.38), matOrange);
    fairing.position.set(0.32, 0.68, 0);
    fairing.rotation.z = -0.18;
    motoGroup.add(fairing);

    // Front fork & handlebar
    const fork = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.72, 10), matMetal);
    fork.position.set(0.62, 0.64, 0);
    fork.rotation.z = 0.28;
    motoGroup.add(fork);

    const handlebar = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.58, 10), matSlate);
    handlebar.rotation.x = Math.PI / 2;
    handlebar.position.set(0.5, 0.96, 0);
    motoGroup.add(handlebar);

    // Headlight
    const headlight = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 12), matHeadlight);
    headlight.position.set(0.74, 0.82, 0);
    motoGroup.add(headlight);

    // Seat
    const seat = new THREE.Mesh(new THREE.BoxGeometry(0.56, 0.12, 0.34), matTire);
    seat.position.set(-0.08, 0.76, 0);
    motoGroup.add(seat);

    // NovaGo branded cargo box
    const cargoBox = new THREE.Group();
    cargoBox.position.set(-0.64, 0.95, 0);

    const boxBody = new THREE.Mesh(new THREE.BoxGeometry(0.64, 0.56, 0.58), matOrange);
    cargoBox.add(boxBody);

    const boxLid = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.09, 0.62), matSlate);
    boxLid.position.y = 0.29;
    cargoBox.add(boxLid);

    // Brand stripe on sides of cargo box
    const stripeGeo = new THREE.BoxGeometry(0.42, 0.14, 0.6);
    const stripe = new THREE.Mesh(stripeGeo, matWhite);
    stripe.position.y = 0.02;
    cargoBox.add(stripe);

    motoGroup.add(cargoBox);

    // Rider torso & animated helmet/visor head
    const torso = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.42, 0.36), matSlate);
    torso.position.set(0.04, 1.0, 0);
    torso.rotation.z = -0.2;
    motoGroup.add(torso);

    const headGroup = new THREE.Group();
    headGroup.position.set(0.12, 1.36, 0);

    const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.24, 16, 14), matOrange);
    helmet.scale.set(1.05, 0.96, 0.96);
    headGroup.add(helmet);

    const visor = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.14, 0.34), matVisor);
    visor.position.set(0.15, 0.01, 0);
    headGroup.add(visor);

    const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.16, 8), matMetal);
    antenna.position.set(-0.05, 0.27, 0);
    headGroup.add(antenna);

    const antennaTip = new THREE.Mesh(new THREE.SphereGeometry(0.035, 10, 10), matVisor);
    antennaTip.position.set(-0.05, 0.36, 0);
    headGroup.add(antennaTip);

    motoGroup.add(headGroup);

    // Subtle ground shadow disc
    const shadowMat = new THREE.MeshBasicMaterial({
        color: 0x0f172a,
        transparent: true,
        opacity: 0.18,
    });
    const shadowDisc = new THREE.Mesh(new THREE.CircleGeometry(1.05, 24), shadowMat);
    shadowDisc.rotation.x = -Math.PI / 2;
    shadowDisc.position.y = 0.02;
    root.add(shadowDisc);

    // Center model vertically and face slightly toward camera
    motoGroup.rotation.y = -0.45;
    root.position.y = -0.58;

    return {
        root,
        motoGroup,
        headGroup,
        cargoBox,
        visorMaterial: matVisor,
        frontWheel,
        rearWheel,
    };
}

/**
 * Creates 3D confetti particles for the 'celebrando' state.
 */
function createConfettiSystem(scene) {
    const group = new THREE.Group();
    group.visible = false;
    const geo = new THREE.BoxGeometry(0.07, 0.07, 0.02);
    const particles = [];

    for (let i = 0; i < 22; i += 1) {
        const mat = new THREE.MeshBasicMaterial({
            color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        });
        const mesh = new THREE.Mesh(geo, mat);
        const angle = (i / 22) * Math.PI * 2;
        const radius = 0.45 + (i % 4) * 0.22;
        mesh.position.set(
            Math.cos(angle) * radius,
            0.4 + (i % 5) * 0.25,
            Math.sin(angle) * radius
        );
        group.add(mesh);
        particles.push({
            mesh,
            baseX: mesh.position.x,
            baseZ: mesh.position.z,
            speed: 0.9 + (i % 5) * 0.25,
            phase: i * 0.55,
        });
    }

    scene.add(group);
    return { group, particles };
}

export class NovaAvatarController {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.modelUrl = options.modelUrl || '/static/assistant/models/nova.glb';
        this.emotion = 'neutral';
        this.pointerX = 0;
        this.pointerY = 0;
        this.isPaused = true;
        this.isDisposed = false;
        this.rafId = null;
        this.clock = new THREE.Clock();
        this.elapsed = 0;

        this.motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.reducedMotion = this.motionQuery.matches;

        this._initScene();
        this._bindEvents();
        this._loadModel();
    }

    _initScene() {
        const width = this.canvas.clientWidth || 76;
        const height = this.canvas.clientHeight || 76;

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            alpha: true,
            antialias: true,
            powerPreference: 'low-power',
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        this.renderer.setSize(width, height, false);

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 30);
        this.camera.position.set(0, 0.65, 3.25);
        this.camera.lookAt(0, 0.15, 0);

        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x334155, 1.35);
        this.scene.add(hemiLight);

        const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.45);
        keyLight.position.set(2.5, 4, 3);
        this.scene.add(keyLight);

        const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.65);
        rimLight.position.set(-2.5, 1.5, -2);
        this.scene.add(rimLight);

        this.confetti = createConfettiSystem(this.scene);
    }

    _loadModel() {
        const loader = new GLTFLoader();
        loader.load(
            this.modelUrl,
            (gltf) => {
                if (this.isDisposed) return;
                const model = gltf.scene;
                const box = new THREE.Box3().setFromObject(model);
                const size = new THREE.Vector3();
                box.getSize(size);
                const maxDim = Math.max(size.x, size.y, size.z) || 1;
                const scale = 1.7 / maxDim;
                model.scale.setScalar(scale);

                const center = new THREE.Vector3();
                box.getCenter(center);
                model.position.sub(center.multiplyScalar(scale));

                this.parts = {
                    root: model,
                    motoGroup: model,
                    headGroup: model.getObjectByName('Head') || null,
                    cargoBox: model.getObjectByName('CargoBox') || null,
                    visorMaterial: null,
                    frontWheel: null,
                    rearWheel: null,
                };
                this.scene.add(model);
                this.renderFrame(0);
            },
            undefined,
            () => {
                if (this.isDisposed) return;
                this.parts = buildProceduralMoto();
                this.scene.add(this.parts.root);
                this.renderFrame(0);
            }
        );
    }

    _bindEvents() {
        this._onPointerMove = (evt) => {
            const w = window.innerWidth || 1;
            const h = window.innerHeight || 1;
            this.pointerX = (evt.clientX / w) * 2 - 1;
            this.pointerY = (evt.clientY / h) * 2 - 1;
        };
        window.addEventListener('pointermove', this._onPointerMove, { passive: true });

        this._onMotionChange = (evt) => {
            this.reducedMotion = evt.matches;
            if (this.reducedMotion) {
                this._stopLoop();
                this.renderFrame(0);
            } else if (!this.isPaused) {
                this._startLoop();
            }
        };
        if (this.motionQuery.addEventListener) {
            this.motionQuery.addEventListener('change', this._onMotionChange);
        }

        if (typeof ResizeObserver !== 'undefined') {
            this._resizeObserver = new ResizeObserver(() => this.resize());
            this._resizeObserver.observe(this.canvas);
        }
    }

    resize() {
        if (this.isDisposed || !this.renderer || !this.camera) return;
        const width = this.canvas.clientWidth || 76;
        const height = this.canvas.clientHeight || 76;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height, false);
        this.renderFrame(0);
    }

    setEmotion(emotion) {
        this.emotion = VALID_EMOTIONS.has(emotion) ? emotion : 'neutral';
        if (this.confetti) {
            this.confetti.group.visible = this.emotion === 'celebrando' && !this.reducedMotion;
        }
        if (this.reducedMotion || this.isPaused) {
            this.renderFrame(0);
        }
    }

    resume() {
        if (this.isDisposed) return;
        this.isPaused = false;
        this.clock.start();
        this.resize();
        if (this.reducedMotion) {
            this.renderFrame(0);
        } else {
            this._startLoop();
        }
    }

    pause() {
        this.isPaused = true;
        this._stopLoop();
        this.clock.stop();
    }

    _startLoop() {
        if (this.rafId !== null || this.isPaused || this.reducedMotion || this.isDisposed) {
            return;
        }
        const tick = () => {
            if (this.isPaused || this.reducedMotion || this.isDisposed) {
                this.rafId = null;
                return;
            }
            const delta = Math.min(this.clock.getDelta(), 0.05);
            this.elapsed += delta;
            this.renderFrame(this.elapsed);
            this.rafId = window.requestAnimationFrame(tick);
        };
        this.rafId = window.requestAnimationFrame(tick);
    }

    _stopLoop() {
        if (this.rafId !== null) {
            window.cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
    }

    renderFrame(t) {
        if (this.isDisposed || !this.renderer) return;

        if (this.parts) {
            const { motoGroup, headGroup, cargoBox, visorMaterial, frontWheel, rearWheel } = this.parts;

            // Reset baseline transforms
            motoGroup.position.y = 0;
            motoGroup.rotation.x = 0;
            motoGroup.rotation.z = 0;
            if (headGroup) {
                headGroup.rotation.set(0, 0, 0);
                headGroup.position.y = headGroup === motoGroup ? 0 : 1.36;
            }
            if (cargoBox) {
                cargoBox.rotation.set(0, 0, 0);
            }
            if (visorMaterial) {
                visorMaterial.emissiveIntensity = 0.55;
            }

            if (this.reducedMotion) {
                if (this.emotion === 'disculpa' && headGroup && headGroup !== motoGroup) {
                    headGroup.rotation.z = -0.25;
                }
            } else {
                switch (this.emotion) {
                    case 'pensando':
                        motoGroup.position.y = Math.sin(t * 2.4) * 0.04;
                        if (cargoBox) {
                            cargoBox.rotation.y = t * 2.2;
                        }
                        if (headGroup && headGroup !== motoGroup) {
                            headGroup.rotation.x = Math.sin(t * 3.0) * 0.18;
                            headGroup.rotation.z = 0.12;
                        }
                        break;

                    case 'hablando':
                        motoGroup.position.y = Math.sin(t * 4.5) * 0.035;
                        if (headGroup && headGroup !== motoGroup) {
                            headGroup.rotation.z = Math.sin(t * 10.0) * 0.12;
                            headGroup.rotation.y = Math.sin(t * 3.5) * 0.12;
                        }
                        if (visorMaterial) {
                            visorMaterial.emissiveIntensity = 0.55 + Math.abs(Math.sin(t * 9.0)) * 0.85;
                        }
                        break;

                    case 'feliz':
                        motoGroup.position.y = Math.abs(Math.sin(t * 5.2)) * 0.18;
                        motoGroup.rotation.z = Math.sin(t * 5.2) * 0.08;
                        if (frontWheel && rearWheel) {
                            frontWheel.rotation.z -= 0.06;
                            rearWheel.rotation.z -= 0.06;
                        }
                        break;

                    case 'celebrando':
                        motoGroup.position.y = Math.abs(Math.sin(t * 6.5)) * 0.24;
                        motoGroup.rotation.y = -0.45 + Math.sin(t * 3.2) * 0.3;
                        if (visorMaterial) {
                            visorMaterial.emissiveIntensity = 1.2;
                        }
                        if (this.confetti && this.confetti.group.visible) {
                            this.confetti.particles.forEach((p) => {
                                const fall = ((t * p.speed + p.phase) % 1.8);
                                p.mesh.position.y = 1.35 - fall;
                                p.mesh.position.x = p.baseX + Math.sin(t * 3 + p.phase) * 0.12;
                                p.mesh.rotation.x = t * 4 + p.phase;
                                p.mesh.rotation.y = t * 3;
                            });
                        }
                        break;

                    case 'disculpa':
                        motoGroup.position.y = -0.04;
                        if (headGroup && headGroup !== motoGroup) {
                            headGroup.rotation.z = -0.28;
                            headGroup.rotation.y = Math.sin(t * 2.0) * 0.14;
                        } else {
                            motoGroup.rotation.z = -0.14;
                        }
                        if (visorMaterial) {
                            visorMaterial.emissiveIntensity = 0.25;
                        }
                        break;

                    case 'neutral':
                    default:
                        motoGroup.position.y = Math.sin(t * 2.0) * 0.045;
                        motoGroup.rotation.y = -0.45 + this.pointerX * 0.22;
                        if (headGroup && headGroup !== motoGroup) {
                            headGroup.rotation.y = this.pointerX * 0.25;
                            headGroup.rotation.z = -this.pointerY * 0.14;
                        }
                        break;
                }
            }
        }

        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        this.isDisposed = true;
        this.pause();
        window.removeEventListener('pointermove', this._onPointerMove);
        if (this.motionQuery.removeEventListener) {
            this.motionQuery.removeEventListener('change', this._onMotionChange);
        }
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
        }
        if (this.renderer) {
            this.renderer.dispose();
        }
    }
}
