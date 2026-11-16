<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const params = inject("params");

const el = ref(null);
let renderer, scene, camera, controls, raf;
let gFace, gPinion;          // 两个转动组
let angFace = 0, angPinion = 0;
let running = ref(true);
let speed = ref(1);
let wire = ref(false);

const info = ref({ mesh: "—", tris: 0 });

/* ---------------- 构建模型 ---------------- */
function disposeGroup(g) {
  if (!g) return;
  g.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) {
      if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
      else o.material.dispose();
    }
  });
  scene.remove(g);
}

function build() {
  if (!scene) return;
  disposeGroup(gFace);
  disposeGroup(gPinion);

  const p = params;
  const p2 = Math.PI / 2;

  // ---- 尺度归一：面齿轮外半径 -> 5 单位 ----
  const R_OUT = 5;
  const k = R_OUT / Math.max(p.r_out, 1);
  const rOut = p.r_out * k;
  const rIn = Math.max(p.r_in * k, rOut * 0.35);
  const bW = Math.max((p.b || p.r_out - p.r_in) * k, rOut * 0.08);
  const toothH = Math.min(Math.max(p.m * k * 1.6, rOut * 0.05), rOut * 0.16);
  const discH = Math.max(toothH * 0.9, rOut * 0.06);

  const r1 = Math.max(((p.m * p.z1) / 2) * k, rOut * 0.08);
  // 小齿轮沿轴向的可见长度：真实齿宽远小于半径，这里取长径比 ≈2.6 便于观察
  const pinionLen = Math.max(rOut * 0.42, r1 * 2.6);

  // 材质（浅背景下的金属色：提亮以呈现钢质感，避免发紫发灰）
  const matSteel = new THREE.MeshStandardMaterial({
    color: 0x7aa5d6, metalness: 0.62, roughness: 0.3,
    flatShading: false, wireframe: wire.value,
  });
  const matSteel2 = new THREE.MeshStandardMaterial({
    color: 0x577aa8, metalness: 0.5, roughness: 0.46,
    wireframe: wire.value,
  });
  const matPin = new THREE.MeshStandardMaterial({
    color: 0xb4cdea, metalness: 0.72, roughness: 0.22,
    wireframe: wire.value,
  });

  /* ============ 面齿轮 ============ */
  gFace = new THREE.Group();

  // 盘
  const disc = new THREE.Mesh(
    new THREE.CylinderGeometry(rOut, rOut, discH, 96),
    matSteel2
  );
  disc.position.y = -discH / 2 + toothH * 0.15;
  disc.castShadow = true; disc.receiveShadow = true;
  gFace.add(disc);

  // 中心孔（薄环，替代原来的高轮毂，避免出现怪阴影）
  const hub = new THREE.Mesh(
    new THREE.CylinderGeometry(rIn * 0.42, rIn * 0.42, discH * 0.55, 40, 1, true),
    matSteel2
  );
  hub.position.y = discH * 0.08;
  hub.material.side = THREE.DoubleSide;
  gFace.add(hub);

  // 径向齿
  const N = Math.max(12, Math.min(Math.round(p.z2), 72));
  const toothRatio = 0.42;
  const dTheta = (Math.PI * 2) / N;
  const toothW0 = dTheta * toothRatio * rIn;    // 内端宽
  const toothW1 = dTheta * toothRatio * rOut;   // 外端宽
  const radLen = rOut - rIn;

  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2;
    // 用 ExtrudeGeometry 做梯形截面（内窄外宽）
    const shape = new THREE.Shape();
    shape.moveTo(-toothW0 / 2, 0);
    shape.lineTo(toothW0 / 2, 0);
    shape.lineTo(toothW1 / 2, radLen);
    shape.lineTo(-toothW1 / 2, radLen);
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: toothH, bevelEnabled: true, bevelSize: toothH * 0.12,
      bevelThickness: toothH * 0.12, bevelSegments: 1,
    });
    const m = new THREE.Mesh(geo, matSteel);
    m.rotation.x = -p2;                 // 让 extrude 方向朝 +y
    m.rotation.z = a - p2;              // 沿圆周排布
    m.position.set(Math.cos(a) * rIn, toothH * 0.2, Math.sin(a) * rIn);
    // 修正：旋转后位置需按径向重新摆
    m.position.set(Math.cos(a) * rIn, toothH * 0.2, -Math.sin(a) * rIn);
    m.castShadow = true;
    gFace.add(m);
  }

  gFace.position.y = 0;
  scene.add(gFace);

  /* ============ 小齿轮 ============ */
  gPinion = new THREE.Group();

  // 圆柱体（轴沿 x）
  const cyl = new THREE.Mesh(
    new THREE.CylinderGeometry(r1, r1, pinionLen, 48),
    matPin
  );
  cyl.rotation.z = p2;
  cyl.castShadow = true;
  gPinion.add(cyl);

  // 轮齿（沿圆周的棱）
  const z1 = Math.max(8, Math.min(Math.round(p.z1), 48));
  const tH = r1 * 0.22;
  const tW = ((Math.PI * 2) / z1) * r1 * 0.42;
  for (let i = 0; i < z1; i++) {
    const a = (i / z1) * Math.PI * 2;
    const geo = new THREE.BoxGeometry(pinionLen, tH, tW);
    const m = new THREE.Mesh(geo, matPin);
    const rr = r1 + tH * 0.34;
    m.position.set(0, Math.cos(a) * rr, Math.sin(a) * rr);
    m.rotation.x = -a;
    m.castShadow = true;
    gPinion.add(m);
  }

  // 位置：轴线与面齿轮轴线正交相交，圆柱压在外圈齿顶上
  const meshR = rIn + (rOut - rIn) * 0.72;
  gPinion.position.set(meshR + pinionLen * 0.10, toothH + r1 * 0.96, 0);
  gPinion.rotation.z = 0;
  scene.add(gPinion);

  // 统计
  let tris = 0;
  [gFace, gPinion].forEach((g) => g.traverse((o) => {
    if (o.geometry?.index) tris += o.geometry.index.count / 3;
    else if (o.geometry?.attributes?.position) tris += o.geometry.attributes.position.count / 3;
  }));
  info.value = {
    mesh: `z₂=${Math.round(p.z2)}（显示 ${N}）· z₁=${Math.round(p.z1)}（显示 ${z1}）`,
    tris: Math.round(tris),
  };
}

/* ---------------- 动画 ---------------- */
function animate() {
  raf = requestAnimationFrame(animate);
  if (running.value) {
    const w = 0.35 * speed.value;
    angFace += w * 0.016;
    angPinion -= w * (params.z2 / params.z1) * 0.016;
    if (gFace) gFace.rotation.y = angFace;
    if (gPinion) gPinion.rotation.x = angPinion;
  }
  controls?.update();
  renderer?.render(scene, camera);
}

/* ---------------- 初始化 ---------------- */
onMounted(() => {
  scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0xf4f6fa, 20, 48);

  const w = el.value.clientWidth, h = el.value.clientHeight;
  camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 200);
  camera.position.set(9, 7.5, 11);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  el.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.minDistance = 4;
  controls.maxDistance = 34;
  controls.target.set(0, 1.2, 0);

  // 光照（浅色场景：环境光为主，避免过曝）
  scene.add(new THREE.AmbientLight(0xffffff, 1.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.75);
  key.position.set(8, 14, 9);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.near = 1; key.shadow.camera.far = 50;
  key.shadow.camera.left = -14; key.shadow.camera.right = 14;
  key.shadow.camera.top = 14; key.shadow.camera.bottom = -14;
  key.shadow.bias = -0.0012;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x7eadde, 1.0);
  rim.position.set(-9, 5, -9);
  scene.add(rim);
  const fill = new THREE.DirectionalLight(0xffe0b0, 0.55);
  fill.position.set(4, -4, 7);
  scene.add(fill);

  // 地面网格
  const grid = new THREE.GridHelper(26, 26, 0xc3cede, 0xdfe6ef);
  grid.position.y = -2.2;
  grid.material.transparent = true;
  grid.material.opacity = 0.75;
  scene.add(grid);

  build();
  animate();

  window.addEventListener("resize", onResize);
});

function onResize() {
  if (!renderer || !el.value) return;
  const w = el.value.clientWidth, h = el.value.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

onBeforeUnmount(() => {
  cancelAnimationFrame(raf);
  window.removeEventListener("resize", onResize);
  controls?.dispose();
  renderer?.dispose();
  if (el.value?.contains(renderer?.domElement)) {
    el.value.removeChild(renderer.domElement);
  }
});

watch(params, () => build(), { deep: true });
watch(wire, () => build());
watch(speed, () => {});
</script>

<template>
  <div class="mv">
    <div class="view" ref="el"></div>

    <div class="hud">
      <div class="row">
        <button class="btn sm" :class="{ on: running }" @click="running = !running">
          {{ running ? "⏸ 暂停" : "▶ 播放" }}
        </button>
        <button class="btn sm" :class="{ on: speed === 0.4 }" @click="speed = 0.4">0.4×</button>
        <button class="btn sm" :class="{ on: speed === 1 }" @click="speed = 1">1×</button>
        <button class="btn sm" :class="{ on: speed === 2.5 }" @click="speed = 2.5">2.5×</button>
        <button class="btn sm ghost" :class="{ on: wire }" @click="wire = !wire">线框</button>
      </div>
      <div class="meta">
        <span>{{ info.mesh }}</span>
        <span>三角面 {{ info.tris.toLocaleString() }}</span>
        <span style="color:var(--dim2)">左键旋转 · 滚轮缩放 · 右键平移</span>
      </div>
    </div>

    <div class="axis">
      <div class="ax y">面齿轮轴 ω₂</div>
      <div class="ax x">小齿轮轴 ω₁</div>
      <div class="ax deg">γ = 90°</div>
    </div>
  </div>
</template>

<style scoped>
.mv { flex: 1; position: relative; min-width: 0; background:
  radial-gradient(1100px 640px at 50% 8%, #ffffff 0%, #eef2f8 62%, #e6ecf4 100%); }
.view { position: absolute; inset: 0; }
.hud {
  position: absolute; left: 18px; bottom: 16px;
  display: flex; flex-direction: column; gap: 9px;
}
.hud .row { display: flex; gap: 6px; }
.meta {
  display: flex; gap: 16px; font-size: 10.5px; color: var(--dim2);
  font-family: Consolas, monospace;
  background: rgba(255, 255, 255, 0.78); padding: 5px 10px;
  border-radius: 7px; border: 1px solid var(--line);
  backdrop-filter: blur(6px);
}
.axis { position: absolute; right: 20px; top: 18px; text-align: right; }
.ax {
  font-size: 10.5px; letter-spacing: 0.04em; margin-bottom: 5px;
  font-family: Consolas, monospace; font-weight: 500;
}
.ax.y { color: #0e7490; }
.ax.x { color: #b45309; }
.ax.deg { color: var(--dim2); }
</style>
