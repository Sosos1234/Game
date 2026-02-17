import * as THREE from "https://unpkg.com/three@0.171.0/build/three.module.js";

const CARD_EVENT = "event";
const CARD_MONSTER = "monster";

const CONFIG = {
  partyNames: ["Warrior", "Mage", "Rogue"],
  heroHp: 14,
  heroPower: 2,
  maxRooms: 6,
  playableCards: 2,
  handEventCards: 2,
  handMonsterCards: 3,
};

const EVENT_TEMPLATES = [
  {
    name: "Campfire Respite",
    effectId: "campfire",
    description: "All living heroes recover 2 HP.",
    potency: 2,
  },
  {
    name: "Ceiling Trap",
    effectId: "trap",
    description: "All living heroes take 2 damage.",
    potency: 2,
  },
  {
    name: "Hidden Cache",
    effectId: "cache",
    description: "One random living hero recovers 4 HP.",
    potency: 4,
  },
  {
    name: "Dark Omen",
    effectId: "omen",
    description: "One random living hero takes 4 damage.",
    potency: 4,
  },
];

const MONSTER_TEMPLATES = [
  {
    name: "Goblin Ambush",
    description: "Quick raiders strike from both sides.",
    baseDanger: 1,
    reward: 14,
  },
  {
    name: "Skeleton Knight",
    description: "A disciplined undead duelist blocks the corridor.",
    baseDanger: 2,
    reward: 20,
  },
  {
    name: "Ogre Brute",
    description: "A heavy hitter with room-wide threat.",
    baseDanger: 3,
    reward: 26,
  },
  {
    name: "Cult Warlock",
    description: "Ritual magic weakens the party defense.",
    baseDanger: 2,
    reward: 22,
  },
  {
    name: "Cave Stalker",
    description: "A silent predator from the shadows.",
    baseDanger: 1,
    reward: 16,
  },
];

const canvas = document.getElementById("gameCanvas");
const statusEl = document.getElementById("status");
const partyEl = document.getElementById("party");
const logEl = document.getElementById("log");
const handEl = document.getElementById("hand");
const playBtn = document.getElementById("playBtn");
const restartBtn = document.getElementById("restartBtn");

let state = createState();
let hand = [];
const selectedIndexes = new Set();

let scene;
let camera;
let renderer;
let clock;

const heroVisuals = [];
const transientObjects = [];
let monstersGroup;
let effectsGroup;
let handCardsGroup;

initScene();
wireUi();
startNewCampaign();
animate();

function createState() {
  return {
    room: 1,
    score: 0,
    lastEvent: "Draw cards and play exactly two.",
    party: CONFIG.partyNames.map((name) => ({
      name,
      hp: CONFIG.heroHp,
      power: CONFIG.heroPower,
    })),
  };
}

function initScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x030712);
  scene.fog = new THREE.Fog(0x030712, 24, 44);

  camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 10, 17);
  camera.lookAt(0, 2, 0);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  clock = new THREE.Clock();

  const ambient = new THREE.AmbientLight(0xb5c7ff, 0.7);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight(0xdbeafe, 1.2);
  keyLight.position.set(6, 12, 8);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x7dd3fc, 0.45);
  rimLight.position.set(-8, 6, -6);
  scene.add(rimLight);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(36, 24),
    new THREE.MeshStandardMaterial({ color: 0x0b1222, metalness: 0.2, roughness: 0.95 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = 0;
  scene.add(floor);

  const grid = new THREE.GridHelper(36, 36, 0x22334c, 0x162033);
  grid.position.y = 0.01;
  scene.add(grid);

  monstersGroup = new THREE.Group();
  effectsGroup = new THREE.Group();
  handCardsGroup = new THREE.Group();

  scene.add(monstersGroup);
  scene.add(effectsGroup);
  scene.add(handCardsGroup);

  buildHeroVisuals();
  addDecor();

  window.addEventListener("resize", onWindowResize);
}

function addDecor() {
  const pillarGeom = new THREE.CylinderGeometry(0.35, 0.45, 4.8, 12);
  const pillarMat = new THREE.MeshStandardMaterial({ color: 0x1a2742, roughness: 0.75, metalness: 0.3 });
  const positions = [
    [-9, 2.4, -6],
    [9, 2.4, -6],
    [-9, 2.4, 6],
    [9, 2.4, 6],
  ];
  for (const [x, y, z] of positions) {
    const pillar = new THREE.Mesh(pillarGeom, pillarMat);
    pillar.position.set(x, y, z);
    scene.add(pillar);
  }
}

function buildHeroVisuals() {
  const xOffsets = [-4.5, 0, 4.5];
  for (let i = 0; i < state.party.length; i += 1) {
    const group = new THREE.Group();
    group.position.set(xOffsets[i], 0, -3.5);

    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry(0.75, 1.5, 5, 10),
      new THREE.MeshStandardMaterial({ color: 0x34d399, roughness: 0.35, metalness: 0.05 })
    );
    body.position.y = 1.4;
    group.add(body);

    const hpBack = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 0.18, 0.2),
      new THREE.MeshBasicMaterial({ color: 0x1e293b })
    );
    hpBack.position.set(0, 2.55, 0);
    group.add(hpBack);

    const hpAnchor = new THREE.Group();
    hpAnchor.position.set(-0.7, 2.55, 0.02);

    const hpFill = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 0.14, 0.12),
      new THREE.MeshBasicMaterial({ color: 0x22c55e })
    );
    hpFill.position.set(0.7, 0, 0);
    hpAnchor.add(hpFill);
    group.add(hpAnchor);

    scene.add(group);
    heroVisuals.push({
      hero: state.party[i],
      group,
      body,
      hpFill,
    });
  }
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function wireUi() {
  playBtn.addEventListener("click", playSelectedCards);
  restartBtn.addEventListener("click", startNewCampaign);
}

function startNewCampaign() {
  state = createState();
  rebindHeroVisuals();
  selectedIndexes.clear();
  clearGroup(monstersGroup);
  clearGroup(effectsGroup);
  transientObjects.length = 0;
  clearGroup(handCardsGroup);
  hand = drawHand();
  announce("Кампания началась. Выбери ровно 2 карты.");
  updateUi();
  updateHeroVisuals();
  syncHandCards3d();
}

function rebindHeroVisuals() {
  for (let i = 0; i < heroVisuals.length; i += 1) {
    heroVisuals[i].hero = state.party[i];
  }
}

function drawHand() {
  const eventTemplates = sample(EVENT_TEMPLATES, CONFIG.handEventCards);
  const monsterTemplates = sample(MONSTER_TEMPLATES, CONFIG.handMonsterCards);

  const cards = eventTemplates.map((template) => ({
    name: template.name,
    cardType: CARD_EVENT,
    description: template.description,
    effectId: template.effectId,
    potency: template.potency,
  }));

  for (const template of monsterTemplates) {
    const danger = template.baseDanger + Math.floor((state.room - 1) / 2);
    const reward = template.reward + (state.room - 1) * 3;
    cards.push({
      name: template.name,
      cardType: CARD_MONSTER,
      description: template.description,
      danger,
      reward,
    });
  }

  shuffle(cards);
  return cards;
}

function sample(items, count) {
  const copy = [...items];
  shuffle(copy);
  return copy.slice(0, count);
}

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
}

function randInt(minInclusive, maxInclusive) {
  return minInclusive + Math.floor(Math.random() * (maxInclusive - minInclusive + 1));
}

function updateUi() {
  const survivors = getSurvivorsCount();
  statusEl.textContent = `Комната: ${Math.min(state.room, CONFIG.maxRooms)}/${CONFIG.maxRooms} | Выжившие: ${survivors}/3 | Счёт: ${state.score}`;
  partyEl.textContent = state.party
    .map((hero) => `${hero.name}: ${hero.hp} HP`)
    .join(" | ");

  handEl.innerHTML = "";
  hand.forEach((card, index) => {
    const cardEl = document.createElement("button");
    cardEl.type = "button";
    cardEl.className = `card ${card.cardType}${selectedIndexes.has(index) ? " selected" : ""}`;

    const title = document.createElement("div");
    title.className = "title";
    title.textContent = `${index + 1}. ${card.name}`;

    const description = document.createElement("div");
    description.textContent = card.description;

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent =
      card.cardType === CARD_EVENT
        ? `Тип: событие | effect=${card.effectId}`
        : `Тип: монстр | danger=${card.danger} | reward=${card.reward}`;

    cardEl.append(title, description, meta);
    cardEl.addEventListener("click", () => toggleCard(index));
    handEl.append(cardEl);
  });

  playBtn.disabled = selectedIndexes.size !== CONFIG.playableCards || isGameOver();
}

function toggleCard(index) {
  if (isGameOver()) {
    return;
  }
  if (selectedIndexes.has(index)) {
    selectedIndexes.delete(index);
  } else {
    if (selectedIndexes.size >= CONFIG.playableCards) {
      announce("Можно выбрать только 2 карты.");
      return;
    }
    selectedIndexes.add(index);
  }
  updateUi();
  syncHandCards3d();
}

function playSelectedCards() {
  if (isGameOver()) {
    return;
  }
  if (selectedIndexes.size !== CONFIG.playableCards) {
    announce("Нужно выбрать ровно 2 карты.");
    return;
  }

  const picks = [...selectedIndexes];
  const messages = [];

  for (const index of picks) {
    const card = hand[index];
    const result = resolveCard(card);
    messages.push(`${card.cardType.toUpperCase()} - ${card.name}: ${result}`);
    if (isPartyDefeated()) {
      messages.push("Вся партия пала. Кампания провалена.");
      break;
    }
  }

  if (!isPartyDefeated()) {
    state.room += 1;
    if (isCampaignComplete()) {
      const bonus = getSurvivorsCount() * 25;
      state.score += bonus;
      messages.push(`Кампания завершена. Бонус за выживших: +${bonus}.`);
      spawnOrbEffect(0x22d3ee, 2.8);
    }
  }

  selectedIndexes.clear();

  if (!isGameOver()) {
    hand = drawHand();
  } else {
    hand = [];
  }

  announce(messages.join(" "));
  updateHeroVisuals();
  updateUi();
  syncHandCards3d();

  if (isGameOver()) {
    if (isCampaignComplete() && !isPartyDefeated()) {
      announce(`${state.lastEvent} Победа! Финальный счёт: ${state.score}.`);
    } else {
      announce(`${state.lastEvent} Поражение. Финальный счёт: ${state.score}.`);
      spawnOrbEffect(0xef4444, 3.2);
    }
  }
}

function resolveCard(card) {
  if (card.cardType === CARD_EVENT) {
    return applyEvent(card);
  }
  if (card.cardType === CARD_MONSTER) {
    return applyMonster(card);
  }
  return "Unknown card type.";
}

function applyEvent(card) {
  const living = getLivingHeroes();
  if (living.length === 0) {
    return "No heroes are alive to resolve this event.";
  }

  if (card.effectId === "campfire") {
    for (const hero of living) {
      changeHeroHp(hero, card.potency);
    }
    state.score += 8;
    spawnOrbEffect(0xf59e0b, 2.0);
    return "Отряд отдохнул у костра и восстановил силы.";
  }

  if (card.effectId === "trap") {
    for (const hero of living) {
      changeHeroHp(hero, -card.potency);
    }
    state.score -= 4;
    spawnOrbEffect(0xfb7185, 2.2);
    return "Ловушка ранила всех живых героев.";
  }

  const target = living[randInt(0, living.length - 1)];
  if (card.effectId === "cache") {
    changeHeroHp(target, card.potency);
    state.score += 10;
    spawnOrbEffect(0x4ade80, 2.0);
    return `${target.name} нашёл тайник и восстановил здоровье.`;
  }

  changeHeroHp(target, -card.potency);
  state.score += 2;
  spawnOrbEffect(0x9333ea, 2.0);
  return `${target.name} пострадал от мрачного знамения.`;
}

function applyMonster(card) {
  const living = getLivingHeroes();
  if (living.length === 0) {
    return "No heroes remain to face monsters.";
  }

  const partyRoll = living.reduce((sum, hero) => sum + randInt(1, 6) + hero.power, 0);
  const monsterRoll = randInt(1, 6) + card.danger * 3 + Math.max(0, state.room - 1);

  if (partyRoll >= monsterRoll) {
    state.score += card.reward;
    const margin = partyRoll - monsterRoll;
    spawnMonster(card, true);
    if (margin <= 2) {
      const target = living[randInt(0, living.length - 1)];
      changeHeroHp(target, -1);
      return `Победа над ${card.name}, но ${target.name} теряет 1 HP.`;
    }
    return `Отряд побеждает монстра: ${card.name}.`;
  }

  const damage = Math.max(1, card.danger);
  for (const hero of living) {
    changeHeroHp(hero, -damage);
  }
  state.score -= 6 * card.danger;
  spawnMonster(card, false);
  return `${card.name} оказался сильнее. Каждый герой теряет ${damage} HP.`;
}

function changeHeroHp(hero, delta) {
  hero.hp = clamp(hero.hp + delta, 0, CONFIG.heroHp);
}

function clamp(value, minValue, maxValue) {
  return Math.min(Math.max(value, minValue), maxValue);
}

function getLivingHeroes() {
  return state.party.filter((hero) => hero.hp > 0);
}

function getSurvivorsCount() {
  return getLivingHeroes().length;
}

function isPartyDefeated() {
  return getSurvivorsCount() === 0;
}

function isCampaignComplete() {
  return state.room > CONFIG.maxRooms;
}

function isGameOver() {
  return isPartyDefeated() || isCampaignComplete();
}

function announce(message) {
  state.lastEvent = message;
  logEl.textContent = message;
}

function updateHeroVisuals() {
  for (const visual of heroVisuals) {
    const hpRatio = visual.hero.hp / CONFIG.heroHp;
    visual.hpFill.scale.x = Math.max(hpRatio, 0.001);
    visual.hpFill.position.x = 0.7 * visual.hpFill.scale.x;

    if (visual.hero.hp > 0) {
      visual.body.material.color.setHex(0x34d399);
      visual.group.position.y = 0;
    } else {
      visual.body.material.color.setHex(0x475569);
      visual.group.position.y = -0.15;
    }
  }
}

function syncHandCards3d() {
  clearGroup(handCardsGroup);
  if (hand.length === 0) {
    return;
  }

  const startX = -6.4;
  const step = 3.2;
  for (let i = 0; i < hand.length; i += 1) {
    const card = hand[i];
    const selected = selectedIndexes.has(i);
    const color = card.cardType === CARD_EVENT ? 0x0284c7 : 0xb91c1c;
    const emissive = selected ? 0x22d3ee : 0x000000;
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.12, 1.65),
      new THREE.MeshStandardMaterial({
        color,
        emissive,
        roughness: 0.45,
        metalness: 0.25,
      })
    );
    mesh.position.set(startX + i * step, 0.9, 7);
    mesh.rotation.x = -0.2;
    mesh.userData.floatOffset = Math.random() * Math.PI * 2;
    handCardsGroup.add(mesh);
  }
}

function spawnMonster(card, wonByParty) {
  const size = 0.7 + card.danger * 0.28;
  const color = wonByParty ? 0x6366f1 : 0xdc2626;
  const mesh = new THREE.Mesh(
    new THREE.OctahedronGeometry(size, 0),
    new THREE.MeshStandardMaterial({
      color,
      emissive: wonByParty ? 0x312e81 : 0x7f1d1d,
      roughness: 0.35,
      metalness: 0.55,
    })
  );
  mesh.position.set(randInt(-8, 8) * 0.55, 1.2 + Math.random() * 1.0, randInt(-2, 6) * 0.5 - 1.5);
  monstersGroup.add(mesh);
  transientObjects.push({
    mesh,
    life: 3.1,
    spin: (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random()),
    rise: 0.2 + Math.random() * 0.2,
  });
}

function spawnOrbEffect(color, life) {
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 18, 16),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.86 })
  );
  mesh.position.set(randInt(-5, 5) * 0.6, 1.8, -1 + Math.random() * 5);
  effectsGroup.add(mesh);
  transientObjects.push({
    mesh,
    life,
    spin: 1.2,
    rise: 0.5,
  });
}

function clearGroup(group) {
  while (group.children.length > 0) {
    const child = group.children[0];
    group.remove(child);
    if (child.geometry) {
      child.geometry.dispose();
    }
    if (child.material) {
      if (Array.isArray(child.material)) {
        for (const material of child.material) {
          material.dispose();
        }
      } else {
        child.material.dispose();
      }
    }
  }
}

function updateTransientObjects(delta) {
  for (let i = transientObjects.length - 1; i >= 0; i -= 1) {
    const item = transientObjects[i];
    item.life -= delta;
    item.mesh.rotation.y += item.spin * delta;
    item.mesh.position.y += item.rise * delta;

    if (item.mesh.material && "opacity" in item.mesh.material) {
      item.mesh.material.opacity = Math.max(item.life / 2.6, 0);
    }

    if (item.life <= 0) {
      if (item.mesh.parent) {
        item.mesh.parent.remove(item.mesh);
      }
      if (item.mesh.geometry) {
        item.mesh.geometry.dispose();
      }
      if (item.mesh.material) {
        item.mesh.material.dispose();
      }
      transientObjects.splice(i, 1);
    }
  }
}

function animate() {
  requestAnimationFrame(animate);
  const elapsed = clock.getElapsedTime();
  const delta = clock.getDelta();

  camera.position.x = Math.sin(elapsed * 0.23) * 1.25;
  camera.position.z = 17 + Math.cos(elapsed * 0.19) * 0.9;
  camera.lookAt(0, 2.1, 0);

  for (const mesh of handCardsGroup.children) {
    const phase = mesh.userData.floatOffset || 0;
    mesh.position.y = 0.9 + Math.sin(elapsed * 1.3 + phase) * 0.05;
  }

  updateTransientObjects(delta);
  renderer.render(scene, camera);
}
