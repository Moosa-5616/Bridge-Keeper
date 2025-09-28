// Game constants
const SCREEN_WIDTH = 1024;
const SCREEN_HEIGHT = 768;
const FPS = 60;

// Colors
const COLORS = {
    forest_green: '#2C5F2D',
    forest_light: '#4CAF50',
    earth_brown: '#8B4513',
    earth_light: '#CD853F',
    flood_red: '#B22222',
    flood_dark: '#8B0000',
    bridge_blue: '#4682B4',
    bridge_light: '#87CEEB',
    village_beige: '#F5DEB3',
    village_light: '#FFF8DC',
    dark_grey: '#2F4F4F',
    light_grey: '#C0C0C0',
    gold: '#FFD700',
    silver: '#C0C0C0',
    white: '#FFFFFF',
    black: '#000000'
};

// Game states
const GameState = {
    MENU: 'menu',
    PLAYING: 'playing',
    PAUSED: 'paused',
    GAME_OVER: 'game_over',
    TUTORIAL: 'tutorial'
};

// Game class
class BridgeKeeperGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.state = GameState.MENU;
        this.running = true;
        
        // Game elements
        this.villageElements = [];
        this.placedObjects = [];
        this.bridgeSegments = [];
        this.particles = [];
        
        // Game state
        this.resources = { wood: 0, stone: 0, metal: 0 };
        this.villagersAlive = 0;
        this.initialVillagers = 0;
        this.villagersSaved = 0;
        this.bridgeProgress = 0;
        this.bridgeRequired = 100;
        this.floodTimer = 300; // 5 minutes
        this.moralStanding = 100;
        this.totalVillagersDisplaced = 0;
        
        // Character
        this.character = {
            x: 300,
            y: 300,
            targetX: 300,
            targetY: 300,
            speed: 150,
            moving: false,
            size: 20,
            animationFrame: 0,
            animationTimer: 0
        };
        
        // Input handling
        this.keys = {};
        this.mousePos = { x: 0, y: 0 };
        this.lastUpdateTime = 0;
        
        // UI elements
        this.hoveredElement = null;
        this.selectedElement = null;
        this.showConfirmation = false;
        this.confirmationElement = null;
        
        this.setupEventListeners();
        this.initializeVillage();
        this.updateUI();
        this.gameLoop();
    }
    
    setupEventListeners() {
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
            this.handleKeyPress(e.code);
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
        });
        
        // Mouse events
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mousePos.x = (e.clientX - rect.left) * (SCREEN_WIDTH / rect.width);
            this.mousePos.y = (e.clientY - rect.top) * (SCREEN_HEIGHT / rect.height);
            this.handleHover();
        });
        
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (SCREEN_WIDTH / rect.width);
            const y = (e.clientY - rect.top) * (SCREEN_HEIGHT / rect.height);
            this.handleClick(x, y);
        });
        
        // Menu button events
        document.getElementById('startGame').addEventListener('click', () => this.startGame());
        document.getElementById('playAgain').addEventListener('click', () => this.startGame());
        document.getElementById('backToMenu').addEventListener('click', () => this.showMenu());
        document.getElementById('resumeGame').addEventListener('click', () => this.resumeGame());
        document.getElementById('mainMenu').addEventListener('click', () => this.showMenu());
        
        // Confirmation dialog
        document.getElementById('confirmYes').addEventListener('click', () => this.confirmAction(true));
        document.getElementById('confirmNo').addEventListener('click', () => this.confirmAction(false));
    }
    
    initializeVillage() {
        this.villageElements = [];
        
        // Generate houses in a grid pattern
        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 5; col++) {
                const x = 60 + col * 90 + (Math.random() - 0.5) * 30;
                const y = 120 + row * 120 + (Math.random() - 0.5) * 30;
                const villagers = Math.floor(Math.random() * 5) + 2;
                
                this.villageElements.push({
                    type: 'house',
                    x: x,
                    y: y,
                    width: 40,
                    height: 40,
                    villagers: villagers,
                    resources: { wood: Math.floor(Math.random() * 3) + 2, stone: Math.floor(Math.random() * 2) + 1 },
                    description: 'Family house',
                    dismantled: false
                });
                
                this.initialVillagers += villagers;
            }
        }
        
        // Generate trees
        for (let i = 0; i < 25; i++) {
            let x, y, attempts = 0;
            do {
                x = Math.random() * 520 + 40;
                y = Math.random() * 400 + 300;
                attempts++;
            } while (this.isPositionOccupied(x, y, 50) && attempts < 50);
            
            this.villageElements.push({
                type: 'tree',
                x: x,
                y: y,
                width: 24,
                height: 32,
                villagers: 0,
                resources: { wood: Math.floor(Math.random() * 3) + 1 },
                description: 'Tree',
                dismantled: false
            });
        }
        
        // Generate infrastructure
        const infrastructureTypes = ['well', 'fence', 'shed', 'statue'];
        for (let i = 0; i < 10; i++) {
            let x, y, attempts = 0;
            do {
                x = Math.random() * 470 + 80;
                y = Math.random() * 500 + 200;
                attempts++;
            } while (this.isPositionOccupied(x, y, 45) && attempts < 50);
            
            const type = infrastructureTypes[Math.floor(Math.random() * infrastructureTypes.length)];
            let villagers = 0, resources = {}, width = 32, height = 24;
            
            switch (type) {
                case 'well':
                    villagers = Math.floor(Math.random() * 3) + 1;
                    resources = { stone: 2, metal: 1 };
                    width = height = 28;
                    break;
                case 'fence':
                    resources = { wood: 1 };
                    width = 40; height = 16;
                    break;
                case 'shed':
                    villagers = Math.random() < 0.5 ? 1 : 0;
                    resources = { wood: 2, metal: 1 };
                    break;
                case 'statue':
                    resources = { stone: 1, metal: 1 };
                    width = 24; height = 32;
                    break;
            }
            
            this.villageElements.push({
                type: type,
                x: x,
                y: y,
                width: width,
                height: height,
                villagers: villagers,
                resources: resources,
                description: type.charAt(0).toUpperCase() + type.slice(1),
                dismantled: false
            });
            
            this.initialVillagers += villagers;
        }
        
        this.villagersAlive = this.initialVillagers;
        
        // Generate initial resources on ground
        for (let i = 0; i < 10; i++) {
            this.placedObjects.push({
                x: Math.random() * 500 + 50,
                y: Math.random() * 600 + 50,
                type: 'log'
            });
        }

        for (let i = 0; i < 5; i++) {
            this.placedObjects.push({
                x: Math.random() * 500 + 50,
                y: Math.random() * 600 + 50,
                type: 'stone'
            });
        }
    }
    
    isPositionOccupied(x, y, radius) {
        for (const element of this.villageElements) {
            const dist = Math.sqrt((x - element.x) ** 2 + (y - element.y) ** 2);
            if (dist < radius) return true;
        }
        return false;
    }
    
    handleKeyPress(keyCode) {
        if (this.state === GameState.PLAYING) {
            if (keyCode === 'Escape') {
                this.pauseGame();
            } else if (keyCode === 'KeyE' || keyCode === 'Space') {
                this.interactWithNearby();
            }
        } else if (this.state === GameState.PAUSED && keyCode === 'Escape') {
            this.resumeGame();
        } else if (this.state === GameState.MENU && keyCode === 'Space') {
            this.startGame();
        }
    }
    
    handleClick(x, y) {
        if (this.state !== GameState.PLAYING) return;
        
        // Check if clicking on a village element
        for (const element of this.villageElements) {
            if (!element.dismantled && 
                x >= element.x && x <= element.x + element.width &&
                y >= element.y && y <= element.y + element.height) {
                
                if (element.type === 'house' && element.villagers > 0) {
                    this.showConfirmationDialog(element);
                } else {
                    this.dismantleElement(element);
                }
                return;
            }
        }
        
        // Check if clicking on placed objects
        for (let i = this.placedObjects.length - 1; i >= 0; i--) {
            const obj = this.placedObjects[i];
            const dist = Math.sqrt((x - obj.x) ** 2 + (y - obj.y) ** 2);
            if (dist < 15) {
                this.collectObject(obj, i);
                return;
            }
        }
        
        // Move character to clicked position anywhere on screen
        this.character.targetX = Math.max(0, Math.min(SCREEN_WIDTH, x));
        this.character.targetY = Math.max(0, Math.min(SCREEN_HEIGHT, y));
        this.character.moving = true;
    }
    
    handleHover() {
        if (this.state !== GameState.PLAYING) return;
        
        this.hoveredElement = null;
        for (const element of this.villageElements) {
            if (!element.dismantled && 
                this.mousePos.x >= element.x && this.mousePos.x <= element.x + element.width &&
                this.mousePos.y >= element.y && this.mousePos.y <= element.y + element.height) {
                this.hoveredElement = element;
                break;
            }
        }
    }
    
    showConfirmationDialog(element) {
        this.confirmationElement = element;
        document.getElementById('confirmTitle').textContent = 'Destroy Family Home?';
        document.getElementById('confirmMessage').textContent = 
            `This will displace ${element.villagers} villagers and affect your moral standing. Are you sure?`;
        document.getElementById('confirmDialog').classList.remove('hidden');
        this.showConfirmation = true;
    }
    
    confirmAction(confirmed) {
        document.getElementById('confirmDialog').classList.add('hidden');
        this.showConfirmation = false;
        
        if (confirmed && this.confirmationElement) {
            this.dismantleElement(this.confirmationElement);
        }
        
        this.confirmationElement = null;
    }
    
    dismantleElement(element) {
        // Add resources
        for (const [resource, amount] of Object.entries(element.resources)) {
            if (this.resources[resource] !== undefined) {
                this.resources[resource] += amount;
            }
        }
        
        // Handle moral consequences
        let moralImpact = 0;
        switch (element.type) {
            case 'house': moralImpact = -25; break;
            case 'well': moralImpact = -15; break;
            case 'statue': moralImpact = -8; break;
            case 'shed': moralImpact = -5; break;
            case 'tree': moralImpact = -2; break;
            case 'fence': moralImpact = -1; break;
        }
        
        this.moralStanding += moralImpact;
        this.moralStanding = Math.max(0, Math.min(200, this.moralStanding));
        
        // Displace villagers
        this.villagersAlive -= element.villagers;
        this.totalVillagersDisplaced += element.villagers;
        
        // Create particles
        this.createDestructionParticles(element.x + element.width/2, element.y + element.height/2);
        
        element.dismantled = true;
        this.updateUI();
    }
    
    collectObject(obj, index) {
        if (obj.type === 'log') {
            this.resources.wood += 1;
        } else if (obj.type === 'stone') {
            this.resources.stone += 1;
        }
        
        this.placedObjects.splice(index, 1);
        this.createCollectionParticles(obj.x, obj.y);
        this.updateUI();
    }
    
    interactWithNearby() {
        const char = this.character;
        const interactionRange = 40;
        
        // Check for village elements
        for (const element of this.villageElements) {
            if (!element.dismantled) {
                const dist = Math.sqrt((char.x - (element.x + element.width/2)) ** 2 + 
                                     (char.y - (element.y + element.height/2)) ** 2);
                if (dist < interactionRange) {
                    if (element.type === 'house' && element.villagers > 0) {
                        this.showConfirmationDialog(element);
                    } else {
                        this.dismantleElement(element);
                    }
                    return;
                }
            }
        }
        
        // Check for placed objects
        for (let i = this.placedObjects.length - 1; i >= 0; i--) {
            const obj = this.placedObjects[i];
            const dist = Math.sqrt((char.x - obj.x) ** 2 + (char.y - obj.y) ** 2);
            if (dist < interactionRange) {
                this.collectObject(obj, i);
                return;
            }
        }
    }
    
    createDestructionParticles(x, y) {
        // Wood chips and debris
        for (let i = 0; i < 12; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 6,
                vy: (Math.random() - 0.5) * 6 - 2,
                life: 1.5,
                color: i % 3 === 0 ? '#8B4513' : i % 3 === 1 ? '#A0522D' : '#654321',
                size: Math.random() * 4 + 2,
                type: 'debris',
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.2
            });
        }
        
        // Dust cloud
        for (let i = 0; i < 8; i++) {
            this.particles.push({
                x: x + (Math.random() - 0.5) * 20,
                y: y + (Math.random() - 0.5) * 20,
                vx: (Math.random() - 0.5) * 2,
                vy: -Math.random() * 2,
                life: 2.0,
                color: `rgba(139, 115, 85, ${Math.random() * 0.6 + 0.2})`,
                size: Math.random() * 8 + 4,
                type: 'dust'
            });
        }
    }
    
    createCollectionParticles(x, y) {
        // Sparkle effect
        for (let i = 0; i < 8; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 3,
                vy: -Math.random() * 4 - 1,
                life: 1.2,
                color: i % 2 === 0 ? '#FFD700' : '#FFA500',
                size: Math.random() * 3 + 1,
                type: 'sparkle',
                twinkle: Math.random() * Math.PI * 2
            });
        }
        
        // Rising '+' indicators
        this.particles.push({
            x: x,
            y: y - 10,
            vx: 0,
            vy: -2,
            life: 2.0,
            color: '#00FF00',
            size: 16,
            type: 'text',
            text: '+1'
        });
    }
    
    updateGame(dt) {
        if (this.state !== GameState.PLAYING) return;
        
        // Update flood timer
        this.floodTimer -= dt;
        if (this.floodTimer <= 0) {
            this.endGame();
            return;
        }
        
        // Update character
        this.updateCharacter(dt);
        
        // Update particles
        this.updateParticles(dt);
        
        // Auto-build bridge
        this.autoBuildBridge();
        
        // Check win condition
        if (this.bridgeProgress >= this.bridgeRequired) {
            this.villagersSaved = this.villagersAlive;
            this.endGame();
        }
        
        this.updateUI();
    }
    
    updateCharacter(dt) {
        const char = this.character;
        
        // Handle keyboard movement (takes priority over mouse movement)
        let moveX = 0, moveY = 0;
        if (this.keys['KeyW'] || this.keys['ArrowUp']) moveY = -1;
        if (this.keys['KeyS'] || this.keys['ArrowDown']) moveY = 1;
        if (this.keys['KeyA'] || this.keys['ArrowLeft']) moveX = -1;
        if (this.keys['KeyD'] || this.keys['ArrowRight']) moveX = 1;
        
        if (moveX !== 0 || moveY !== 0) {
            // Keyboard movement - stop mouse movement and move directly
            const speed = char.speed * dt;
            const newX = char.x + moveX * speed;
            const newY = char.y + moveY * speed;
            
            // Allow movement across entire screen
            char.x = Math.max(0, Math.min(SCREEN_WIDTH, newX));
            char.y = Math.max(0, Math.min(SCREEN_HEIGHT, newY));
            
            char.moving = true;
            char.targetX = char.x; // Update target to current position
            char.targetY = char.y;
        } else if (char.moving && (Math.abs(char.targetX - char.x) > 3 || Math.abs(char.targetY - char.y) > 3)) {
            // Mouse movement - only move if we're not close to target
            const dx = char.targetX - char.x;
            const dy = char.targetY - char.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            const speed = char.speed * dt;
            const newX = char.x + (dx / distance) * speed;
            const newY = char.y + (dy / distance) * speed;
            
            // Allow movement across entire screen
            char.x = Math.max(0, Math.min(SCREEN_WIDTH, newX));
            char.y = Math.max(0, Math.min(SCREEN_HEIGHT, newY));
        } else {
            char.moving = false;
        }
        
        // Update animation
        if (char.moving) {
            char.animationTimer += dt;
            if (char.animationTimer >= 0.15) {
                char.animationFrame = (char.animationFrame + 1) % 4;
                char.animationTimer = 0;
            }
        } else {
            char.animationFrame = 0;
        }
    }
    
    updateParticles(dt) {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            
            // Update position
            particle.x += particle.vx * dt * 60;
            particle.y += particle.vy * dt * 60;
            
            // Apply gravity (less for dust and text)
            if (particle.type === 'dust') {
                particle.vy += 0.05 * dt * 60;
            } else if (particle.type === 'text') {
                // Text floats up with no gravity
            } else {
                particle.vy += 0.15 * dt * 60;
            }
            
            // Update rotation for debris
            if (particle.type === 'debris' && particle.rotationSpeed) {
                particle.rotation += particle.rotationSpeed * dt * 60;
            }
            
            // Update twinkle for sparkles
            if (particle.type === 'sparkle') {
                particle.twinkle += dt * 4;
            }
            
            // Fade out
            particle.life -= dt;
            
            if (particle.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
    }
    
    autoBuildBridge() {
    // Reduced resource requirements for easier bridge building
    const woodNeeded = 5;
    const stoneNeeded = 2;
    const metalNeeded = 0;

        while (this.resources.wood >= woodNeeded &&
               this.resources.stone >= stoneNeeded &&
               this.resources.metal >= metalNeeded &&
               this.bridgeSegments.length < 5) {

            this.resources.wood -= woodNeeded;
            this.resources.stone -= stoneNeeded;
            this.resources.metal -= metalNeeded;

            this.bridgeSegments.push({
                y: SCREEN_HEIGHT - (this.bridgeSegments.length + 1) * (SCREEN_HEIGHT / 5),
                completed: true
            });

            this.bridgeProgress = (this.bridgeSegments.length / 5) * this.bridgeRequired;
        }
    }
    
    updateUI() {
        document.getElementById('wood').textContent = this.resources.wood;
        document.getElementById('stone').textContent = this.resources.stone;
        document.getElementById('metal').textContent = this.resources.metal;
        document.getElementById('villagers').textContent = this.villagersAlive;
        document.getElementById('timeLeft').textContent = Math.ceil(this.floodTimer);
        document.getElementById('bridgeProgress').textContent = Math.round(this.bridgeProgress);
        document.getElementById('moralStanding').textContent = this.moralStanding;

        // Show total materials needed to fully build the bridge
        const totalSegments = 5;
        const woodNeeded = 5; // must match autoBuildBridge()
        const stoneNeeded = 2;
        const metalNeeded = 0;
        const builtSegments = this.bridgeSegments.length;
        const remainingSegments = totalSegments - builtSegments;
        const totalWood = woodNeeded * totalSegments;
        const totalStone = stoneNeeded * totalSegments;
        const totalMetal = metalNeeded * totalSegments;
        const remainingWood = woodNeeded * remainingSegments;
        const remainingStone = stoneNeeded * remainingSegments;
        const remainingMetal = metalNeeded * remainingSegments;
        document.getElementById('bridgeMaterialsNeeded').textContent =
            `Total: 🪵${totalWood} 🪨${totalStone} ⚙️${totalMetal} | Left: 🪵${remainingWood} 🪨${remainingStone} ⚙️${remainingMetal}`;
    }
    
    startGame() {
        this.state = GameState.PLAYING;
        document.getElementById('menuScreen').classList.add('hidden');
        document.getElementById('gameOverScreen').classList.add('hidden');
        document.getElementById('pauseScreen').classList.add('hidden');
        document.getElementById('ui').style.display = 'grid';
        
        // Reset game state
        this.resources = { wood: 0, stone: 0, metal: 0 };
        this.bridgeProgress = 0;
        this.bridgeSegments = [];
        this.particles = [];
        this.floodTimer = 300;
        this.moralStanding = 100;
        this.totalVillagersDisplaced = 0;
        this.villagersSaved = 0;
        
        this.character.x = 300;
        this.character.y = 300;
        this.character.targetX = 300;
        this.character.targetY = 300;
        this.character.moving = false;
        
        this.initializeVillage();
        this.updateUI();
    }
    
    pauseGame() {
        this.state = GameState.PAUSED;
        document.getElementById('pauseScreen').classList.remove('hidden');
    }
    
    resumeGame() {
        this.state = GameState.PLAYING;
        document.getElementById('pauseScreen').classList.add('hidden');
    }
    
    showMenu() {
        this.state = GameState.MENU;
        document.getElementById('menuScreen').classList.remove('hidden');
        document.getElementById('gameOverScreen').classList.add('hidden');
        document.getElementById('pauseScreen').classList.add('hidden');
        document.getElementById('ui').style.display = 'none';
    }
    
    endGame() {
        this.state = GameState.GAME_OVER;
        document.getElementById('gameOverScreen').classList.remove('hidden');
        document.getElementById('ui').style.display = 'none';
        
        const title = document.getElementById('gameOverTitle');
        const stats = document.getElementById('gameOverStats');
        
        if (this.bridgeProgress >= this.bridgeRequired) {
            title.textContent = 'Victory!';
            title.style.color = '#4CAF50';
        } else {
            title.textContent = 'Game Over';
            title.style.color = '#B22222';
        }
        
        stats.innerHTML = `
            <p><strong>Villagers Saved:</strong> ${this.villagersSaved} / ${this.initialVillagers}</p>
            <p><strong>Bridge Progress:</strong> ${Math.round(this.bridgeProgress)}%</p>
            <p><strong>Moral Standing:</strong> ${this.moralStanding}</p>
            <p><strong>Time Remaining:</strong> ${Math.ceil(Math.max(0, this.floodTimer))}s</p>
            <p><strong>Villagers Displaced:</strong> ${this.totalVillagersDisplaced}</p>
        `;
    }
    
    render() {
        const ctx = this.ctx;
        
        // Clear screen
        ctx.fillStyle = COLORS.village_beige;
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
        
        if (this.state === GameState.PLAYING || this.state === GameState.PAUSED) {
            this.renderGame();
        }
    }
    
    renderGame() {
        const ctx = this.ctx;
        
        // Draw background grass texture
        this.drawBackground();
        
        // Draw shadows first (behind everything)
        this.drawShadows();
        
        // Draw village elements
        for (const element of this.villageElements) {
            if (!element.dismantled) {
                this.drawVillageElement(element);
            }
        }
        
        // Draw placed objects
        for (const obj of this.placedObjects) {
            this.drawPlacedObject(obj);
        }
        
        // Draw character
        this.drawCharacter();
        
        // Draw enhanced river with water animation
        this.drawRiver();
        
        // Draw enhanced bridge
        this.drawBridge();
        
        // Draw particles with enhanced effects
        for (const particle of this.particles) {
            ctx.save();
            ctx.globalAlpha = particle.life / (particle.type === 'dust' ? 2.0 : particle.type === 'text' ? 2.0 : 1.5);
            
            if (particle.type === 'debris') {
                // Rotating debris pieces
                ctx.translate(particle.x, particle.y);
                ctx.rotate(particle.rotation || 0);
                ctx.fillStyle = particle.color;
                ctx.fillRect(-particle.size/2, -particle.size/2, particle.size, particle.size/2);
                
            } else if (particle.type === 'dust') {
                // Dust clouds
                ctx.fillStyle = particle.color;
                ctx.beginPath();
                ctx.arc(0, 0, particle.size, 0, Math.PI * 2);
                ctx.fill();
                
            } else if (particle.type === 'sparkle') {
                // Twinkling sparkles
                const twinkle = Math.sin(particle.twinkle + Date.now() * 0.01) * 0.5 + 0.5;
                ctx.globalAlpha *= twinkle;
                ctx.fillStyle = particle.color;
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fill();
                
                // Add sparkle rays
                ctx.strokeStyle = particle.color;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(particle.x - particle.size*2, particle.y);
                ctx.lineTo(particle.x + particle.size*2, particle.y);
                ctx.moveTo(particle.x, particle.y - particle.size*2);
                ctx.lineTo(particle.x, particle.y + particle.size*2);
                ctx.stroke();
                
            } else if (particle.type === 'text') {
                // Floating text
                ctx.fillStyle = particle.color;
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.font = `bold ${particle.size}px monospace`;
                ctx.textAlign = 'center';
                ctx.strokeText(particle.text, particle.x, particle.y);
                ctx.fillText(particle.text, particle.x, particle.y);
                
            } else {
                // Default circular particles
                ctx.fillStyle = particle.color;
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fill();
            }
            
            ctx.restore();
        }
        
        // Draw hover effect with glow
        if (this.hoveredElement) {
            this.drawHoverGlow(this.hoveredElement);
        }
        
        // Draw flood warning with enhanced effect
        if (this.floodTimer < 60) {
            this.drawFloodWarning();
        }
        
        // Draw environmental details
        this.drawEnvironmentalDetails();
    }
    
    drawBackground() {
        const ctx = this.ctx;
        
        // Create detailed grass terrain with depth
        const grassGradient = ctx.createRadialGradient(300, 400, 0, 300, 400, 600);
        grassGradient.addColorStop(0, '#9ACD32');
        grassGradient.addColorStop(0.6, '#8FBC8F');
        grassGradient.addColorStop(1, '#7CFC00');
        ctx.fillStyle = grassGradient;
        ctx.fillRect(0, 0, 600, SCREEN_HEIGHT);
        
        // Detailed grass texture overlay
        for (let x = 0; x < 600; x += 12) {
            for (let y = 0; y < SCREEN_HEIGHT; y += 12) {
                const noise = Math.random();
                if (noise > 0.7) {
                    // Grass clumps
                    ctx.fillStyle = `rgba(34, 139, 34, ${0.3 + noise * 0.4})`;
                    ctx.fillRect(x, y, 8, 8);
                    
                    // Individual grass blades
                    ctx.fillStyle = '#228B22';
                    for (let i = 0; i < 5; i++) {
                        const gx = x + Math.random() * 8;
                        const gy = y + Math.random() * 8;
                        const height = 2 + Math.random() * 3;
                        ctx.fillRect(gx, gy - height, 1, height);
                    }
                }
                
                // Add small flowers occasionally
                if (Math.random() > 0.95) {
                    const colors = ['#FFB6C1', '#FFFACD', '#E6E6FA'];
                    ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
                    ctx.beginPath();
                    ctx.arc(x + 4, y + 4, 2, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }
        
        // Enhanced dirt paths with realistic texture
        ctx.fillStyle = '#8B7355';
        ctx.fillRect(250, 0, 80, SCREEN_HEIGHT);
        
        // Path worn texture
        ctx.fillStyle = '#A0522D';
        for (let y = 0; y < SCREEN_HEIGHT; y += 10) {
            for (let x = 255; x < 325; x += 8) {
                if (Math.random() > 0.6) {
                    const size = 2 + Math.random() * 4;
                    ctx.fillRect(x + Math.random() * 6, y + Math.random() * 8, size, size/2);
                }
            }
        }
        
        // Path edge definition
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(250, 0);
        ctx.lineTo(250, SCREEN_HEIGHT);
        ctx.moveTo(330, 0);
        ctx.lineTo(330, SCREEN_HEIGHT);
        ctx.stroke();
        
        // Add atmospheric perspective
        const atmosphereGradient = ctx.createLinearGradient(0, 0, 0, SCREEN_HEIGHT);
        atmosphereGradient.addColorStop(0, 'rgba(135, 206, 235, 0.1)');
        atmosphereGradient.addColorStop(1, 'rgba(255, 255, 255, 0.05)');
        ctx.fillStyle = atmosphereGradient;
        ctx.fillRect(0, 0, 600, SCREEN_HEIGHT);
    }
    
    drawShadows() {
        const ctx = this.ctx;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        
        for (const element of this.villageElements) {
            if (!element.dismantled) {
                // Draw shadow offset slightly
                ctx.fillRect(element.x + 3, element.y + element.height + 2, element.width, 4);
            }
        }
    }
    
    drawRiver() {
        const ctx = this.ctx;
        
        // Water base
        const gradient = ctx.createLinearGradient(600, 0, 700, 0);
        gradient.addColorStop(0, '#4682B4');
        gradient.addColorStop(0.5, '#87CEEB');
        gradient.addColorStop(1, '#4682B4');
        ctx.fillStyle = gradient;
        ctx.fillRect(600, 0, 100, SCREEN_HEIGHT);
        
        // Water animation waves
        const time = Date.now() * 0.002;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 2;
        
        for (let y = 0; y < SCREEN_HEIGHT; y += 30) {
            ctx.beginPath();
            ctx.moveTo(600, y);
            for (let x = 600; x <= 700; x += 5) {
                const wave = Math.sin((x - 600) * 0.05 + time + y * 0.01) * 3;
                ctx.lineTo(x, y + wave);
            }
            ctx.stroke();
        }
        
        // Riverbank details
        ctx.fillStyle = '#8B7355';
        ctx.fillRect(595, 0, 10, SCREEN_HEIGHT);
        ctx.fillRect(695, 0, 10, SCREEN_HEIGHT);
        
        // Add some rocks along the bank
        ctx.fillStyle = '#708090';
        for (let y = 50; y < SCREEN_HEIGHT; y += 80) {
            ctx.beginPath();
            ctx.arc(598 + Math.random() * 6, y + Math.random() * 20, 3 + Math.random() * 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    drawBridge() {
        const ctx = this.ctx;
        
        // Bridge foundation
        ctx.fillStyle = '#2F4F4F';
        ctx.fillRect(610, 0, 80, SCREEN_HEIGHT);
        
        // Bridge side rails
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(615, 0, 8, SCREEN_HEIGHT);
        ctx.fillRect(677, 0, 8, SCREEN_HEIGHT);
        
        // Bridge segments with detailed planks
        for (const segment of this.bridgeSegments) {
            // Main plank
            ctx.fillStyle = '#D2691E';
            ctx.fillRect(623, segment.y, 54, SCREEN_HEIGHT / 20 - 2);
            
            // Plank details
            ctx.fillStyle = '#8B4513';
            ctx.fillRect(623, segment.y, 54, 2);
            ctx.fillRect(623, segment.y + SCREEN_HEIGHT / 20 - 4, 54, 2);
            
            // Vertical supports
            for (let x = 630; x < 670; x += 15) {
                ctx.fillRect(x, segment.y + 2, 3, SCREEN_HEIGHT / 20 - 6);
            }
            
            // Add wood grain texture
            ctx.strokeStyle = '#A0522D';
            ctx.lineWidth = 1;
            for (let i = 0; i < 3; i++) {
                ctx.beginPath();
                ctx.moveTo(625 + i * 15, segment.y + 2);
                ctx.lineTo(625 + i * 15 + 10, segment.y + SCREEN_HEIGHT / 20 - 4);
                ctx.stroke();
            }
        }
    }
    
    drawHoverGlow(element) {
        const ctx = this.ctx;
        
        // Outer glow
        ctx.save();
        ctx.shadowColor = COLORS.gold;
        ctx.shadowBlur = 10;
        ctx.strokeStyle = COLORS.gold;
        ctx.lineWidth = 3;
        ctx.strokeRect(element.x - 4, element.y - 4, element.width + 8, element.height + 8);
        
        // Inner highlight
        ctx.shadowBlur = 0;
        ctx.strokeStyle = 'rgba(255, 215, 0, 0.6)';
        ctx.lineWidth = 2;
        ctx.strokeRect(element.x - 2, element.y - 2, element.width + 4, element.height + 4);
        ctx.restore();
    }
    
    drawFloodWarning() {
        const ctx = this.ctx;
        const time = Date.now() * 0.005;
        const intensity = Math.abs(Math.sin(time)) * 0.4 + 0.1;
        
        // Animated warning overlay
        ctx.save();
        ctx.globalAlpha = intensity;
        
        // Gradient from bottom
        const gradient = ctx.createLinearGradient(0, SCREEN_HEIGHT - 60, 0, SCREEN_HEIGHT);
        gradient.addColorStop(0, 'rgba(178, 34, 34, 0)');
        gradient.addColorStop(1, 'rgba(178, 34, 34, 0.8)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, SCREEN_HEIGHT - 60, 600, 60);
        
        // Warning text
        ctx.globalAlpha = Math.abs(Math.sin(time * 2)) * 0.8 + 0.2;
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 24px monospace';
        ctx.textAlign = 'center';
        ctx.strokeStyle = '#8B0000';
        ctx.lineWidth = 2;
        
        const warningText = 'FLOOD WARNING!';
        ctx.strokeText(warningText, 300, SCREEN_HEIGHT - 20);
        ctx.fillText(warningText, 300, SCREEN_HEIGHT - 20);
        
        ctx.restore();
    }
    
    drawEnvironmentalDetails() {
        const ctx = this.ctx;
        
        // Add some scattered stones
        ctx.fillStyle = '#708090';
        const stones = [[120, 200], [450, 350], [200, 600], [380, 150]];
        for (const [x, y] of stones) {
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Add small bushes
        ctx.fillStyle = '#228B22';
        const bushes = [[80, 250], [500, 400], [150, 550]];
        for (const [x, y] of bushes) {
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(x + 6, y - 3, 6, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    drawVillageElement(element) {
        const ctx = this.ctx;
        
        switch (element.type) {
            case 'house':
                this.drawDetailedHouse(ctx, element);
                break;
            case 'tree':
                this.drawDetailedTree(ctx, element);
                break;
            case 'well':
                this.drawDetailedWell(ctx, element);
                break;
            case 'fence':
                this.drawDetailedFence(ctx, element);
                break;
            case 'shed':
                this.drawDetailedShed(ctx, element);
                break;
            case 'statue':
                this.drawDetailedStatue(ctx, element);
                break;
        }
        
        // Show villager count with enhanced styling
        if (element.villagers > 0) {
            const centerX = element.x + element.width/2;
            const iconY = element.y - 15;
            
            // Background bubble
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(centerX, iconY, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            
            // Villager icon text
            ctx.fillStyle = '#333';
            ctx.font = 'bold 14px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(element.villagers.toString(), centerX, iconY + 5);
        }
    }
    
    drawDetailedHouse(ctx, element) {
        const x = element.x, y = element.y, w = element.width, h = element.height;
        
        // House foundation/base
        ctx.fillStyle = '#8B7355';
        ctx.fillRect(x - 2, y + h - 3, w + 4, 5);
        
        // Main walls with texture
        const wallGradient = ctx.createLinearGradient(x, y, x + w, y);
        wallGradient.addColorStop(0, '#F5DEB3');
        wallGradient.addColorStop(0.5, '#FFFFFF');
        wallGradient.addColorStop(1, '#F5DEB3');
        ctx.fillStyle = wallGradient;
        ctx.fillRect(x, y, w, h);
        
        // Wall details/texture
        ctx.strokeStyle = '#DDD';
        ctx.lineWidth = 1;
        for (let i = 1; i < 4; i++) {
            ctx.beginPath();
            ctx.moveTo(x, y + i * h/4);
            ctx.lineTo(x + w, y + i * h/4);
            ctx.stroke();
        }
        
        // Roof with gradient
        const roofGradient = ctx.createLinearGradient(x, y - 15, x, y);
        roofGradient.addColorStop(0, '#DC143C');
        roofGradient.addColorStop(1, '#8B0000');
        ctx.fillStyle = roofGradient;
        
        ctx.beginPath();
        ctx.moveTo(x - 6, y);
        ctx.lineTo(x + w/2, y - 18);
        ctx.lineTo(x + w + 6, y);
        ctx.closePath();
        ctx.fill();
        
        // Roof ridge
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - 6, y);
        ctx.lineTo(x + w/2, y - 18);
        ctx.lineTo(x + w + 6, y);
        ctx.stroke();
        
        // Door with details
        const doorX = x + w/2 - 6;
        const doorY = y + h - 16;
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(doorX, doorY, 12, 16);
        
        // Door frame
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        ctx.strokeRect(doorX, doorY, 12, 16);
        
        // Door handle
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(doorX + 9, doorY + 8, 1.5, 0, Math.PI * 2);
        ctx.fill();
        
        // Windows
        const windowSize = 8;
        const windowY = y + 8;
        
        // Left window
        ctx.fillStyle = '#87CEEB';
        ctx.fillRect(x + 6, windowY, windowSize, windowSize);
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x + 6, windowY, windowSize, windowSize);
        
        // Window cross
        ctx.beginPath();
        ctx.moveTo(x + 10, windowY);
        ctx.lineTo(x + 10, windowY + windowSize);
        ctx.moveTo(x + 6, windowY + 4);
        ctx.lineTo(x + 6 + windowSize, windowY + 4);
        ctx.stroke();
        
        // Right window
        ctx.fillStyle = '#87CEEB';
        ctx.fillRect(x + w - 6 - windowSize, windowY, windowSize, windowSize);
        ctx.strokeRect(x + w - 6 - windowSize, windowY, windowSize, windowSize);
        
        // Window cross
        ctx.beginPath();
        ctx.moveTo(x + w - 10, windowY);
        ctx.lineTo(x + w - 10, windowY + windowSize);
        ctx.moveTo(x + w - 6 - windowSize, windowY + 4);
        ctx.lineTo(x + w - 6, windowY + 4);
        ctx.stroke();
        
        // Chimney
        ctx.fillStyle = '#696969';
        ctx.fillRect(x + w - 8, y - 12, 6, 15);
        ctx.fillStyle = '#A9A9A9';
        ctx.fillRect(x + w - 8, y - 15, 6, 3);
    }
    
    drawDetailedTree(ctx, element) {
        const x = element.x + element.width/2;
        const y = element.y;
        
        // Trunk with texture
        const trunkGradient = ctx.createLinearGradient(x - 4, y, x + 4, y);
        trunkGradient.addColorStop(0, '#8B4513');
        trunkGradient.addColorStop(0.5, '#A0522D');
        trunkGradient.addColorStop(1, '#8B4513');
        
        ctx.fillStyle = trunkGradient;
        ctx.fillRect(x - 4, y + element.height - 12, 8, 12);
        
        // Trunk texture lines
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 1;
        for (let i = 0; i < 3; i++) {
            ctx.beginPath();
            ctx.moveTo(x - 4, y + element.height - 10 + i * 3);
            ctx.lineTo(x + 4, y + element.height - 10 + i * 3);
            ctx.stroke();
        }
        
        // Multiple layers of leaves for depth
        const leafColors = ['#228B22', '#32CD32', '#90EE90'];
        const leafSizes = [15, 12, 9];
        
        for (let i = 0; i < 3; i++) {
            ctx.fillStyle = leafColors[i];
            ctx.beginPath();
            ctx.arc(x + (i-1) * 3, y + 10 - i * 2, leafSizes[i], 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Leaf highlights
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(x - 5, y + 5, 4, 0, Math.PI * 2);
        ctx.fill();
    }
    
    drawDetailedWell(ctx, element) {
        const centerX = element.x + element.width/2;
        const centerY = element.y + element.height/2;
        const radius = element.width/2;
        
        // Well base with stone texture
        ctx.fillStyle = '#A9A9A9';
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Stone pattern
        ctx.strokeStyle = '#696969';
        ctx.lineWidth = 1;
        for (let angle = 0; angle < Math.PI * 2; angle += Math.PI/4) {
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
            ctx.stroke();
        }
        
        // Well interior (dark water)
        ctx.fillStyle = '#000080';
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius - 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Water reflection
        ctx.fillStyle = 'rgba(135, 206, 235, 0.6)';
        ctx.beginPath();
        ctx.arc(centerX - 3, centerY - 3, 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Well rim
        ctx.strokeStyle = '#2F4F4F';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // Bucket rope and pulley
        ctx.strokeStyle = '#8B4513';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(centerX + radius - 5, element.y - 5);
        ctx.lineTo(centerX + radius - 5, centerY - 8);
        ctx.stroke();
        
        // Small bucket
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(centerX + radius - 8, centerY - 10, 6, 4);
    }
    
    drawDetailedFence(ctx, element) {
        const x = element.x, y = element.y, w = element.width, h = element.height;
        
        // Fence posts with texture
        ctx.fillStyle = '#8B4513';
        for (let i = 0; i <= w; i += 10) {
            ctx.fillRect(x + i, y, 3, h);
            
            // Post tops
            ctx.fillStyle = '#A0522D';
            ctx.fillRect(x + i - 1, y - 2, 5, 4);
            ctx.fillStyle = '#8B4513';
        }
        
        // Horizontal rails
        ctx.fillStyle = '#A0522D';
        ctx.fillRect(x, y + h/3, w, 3);
        ctx.fillRect(x, y + 2*h/3, w, 3);
        
        // Wood grain details
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 1;
        for (let i = 0; i < w; i += 20) {
            ctx.beginPath();
            ctx.moveTo(x + i, y + h/3);
            ctx.lineTo(x + i + 15, y + h/3 + 3);
            ctx.stroke();
        }
    }
    
    drawDetailedShed(ctx, element) {
        const x = element.x, y = element.y, w = element.width, h = element.height;
        
        // Shed walls
        ctx.fillStyle = '#D2691E';
        ctx.fillRect(x, y, w, h);
        
        // Wall paneling
        ctx.strokeStyle = '#8B4513';
        ctx.lineWidth = 1;
        for (let i = 0; i < h; i += 6) {
            ctx.beginPath();
            ctx.moveTo(x, y + i);
            ctx.lineTo(x + w, y + i);
            ctx.stroke();
        }
        
        // Simple slanted roof
        ctx.fillStyle = '#654321';
        ctx.beginPath();
        ctx.moveTo(x - 2, y);
        ctx.lineTo(x + w/3, y - 8);
        ctx.lineTo(x + w + 2, y - 3);
        ctx.lineTo(x + w, y);
        ctx.closePath();
        ctx.fill();
        
        // Door
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(x + w - 12, y + h - 15, 10, 15);
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 1;
        ctx.strokeRect(x + w - 12, y + h - 15, 10, 15);
        
        // Door handle
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(x + w - 4, y + h - 8, 1, 0, Math.PI * 2);
        ctx.fill();
    }
    
    drawDetailedStatue(ctx, element) {
        const centerX = element.x + element.width/2;
        const y = element.y;
        
        // Statue base
        ctx.fillStyle = '#A9A9A9';
        ctx.fillRect(element.x, y + element.height - 8, element.width, 8);
        
        // Base details
        ctx.strokeStyle = '#696969';
        ctx.lineWidth = 1;
        ctx.strokeRect(element.x, y + element.height - 8, element.width, 8);
        
        // Statue pillar
        ctx.fillStyle = '#D3D3D3';
        ctx.fillRect(centerX - 4, y, 8, element.height - 8);
        
        // Pillar highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.fillRect(centerX - 4, y, 2, element.height - 8);
        
        // Statue figure (simple)
        ctx.fillStyle = '#C0C0C0';
        ctx.beginPath();
        ctx.arc(centerX, y + 6, 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Figure body
        ctx.fillRect(centerX - 2, y + 8, 4, 8);
        
        // Decorative elements
        ctx.strokeStyle = '#696969';
        ctx.lineWidth = 1;
        for (let i = 0; i < 3; i++) {
            ctx.beginPath();
            ctx.moveTo(element.x + 2, y + element.height - 20 + i * 4);
            ctx.lineTo(element.x + element.width - 2, y + element.height - 20 + i * 4);
            ctx.stroke();
        }
    }
    
    drawPlacedObject(obj) {
        const ctx = this.ctx;
        
        if (obj.type === 'log') {
            ctx.fillStyle = COLORS.earth_brown;
            ctx.fillRect(obj.x - 8, obj.y - 3, 16, 6);
        } else if (obj.type === 'stone') {
            ctx.fillStyle = COLORS.light_grey;
            ctx.beginPath();
            ctx.arc(obj.x, obj.y, 6, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    drawCharacter() {
        const ctx = this.ctx;
        const char = this.character;
        
        // Animation bobbing
        const bobOffset = char.moving ? Math.sin(char.animationFrame * 0.8) * 2 : 0;
        const legOffset = char.moving ? Math.sin(char.animationFrame * 1.2) * 1.5 : 0;
        
        // Character shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.ellipse(char.x, char.y + char.size/2 + 3, char.size/2 + 2, 4, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Legs (animated walking)
        ctx.fillStyle = '#654321';
        ctx.fillRect(char.x - 4, char.y + char.size/4 + legOffset, 3, char.size/2);
        ctx.fillRect(char.x + 1, char.y + char.size/4 - legOffset, 3, char.size/2);
        
        // Body (tunic)
        const bodyGradient = ctx.createLinearGradient(char.x - char.size/2, char.y - char.size/3, char.x + char.size/2, char.y + char.size/3);
        bodyGradient.addColorStop(0, '#4682B4');
        bodyGradient.addColorStop(0.5, '#87CEEB');
        bodyGradient.addColorStop(1, '#4682B4');
        ctx.fillStyle = bodyGradient;
        ctx.fillRect(char.x - char.size/2, char.y - char.size/3 + bobOffset, char.size, char.size/1.5);
        
        // Body outline
        ctx.strokeStyle = '#2F4F4F';
        ctx.lineWidth = 1;
        ctx.strokeRect(char.x - char.size/2, char.y - char.size/3 + bobOffset, char.size, char.size/1.5);
        
        // Arms (animated)
        const armSwing = char.moving ? Math.sin(char.animationFrame * 1.1) * 1 : 0;
        ctx.fillStyle = '#FDBCB4';
        
        // Left arm
        ctx.save();
        ctx.translate(char.x - char.size/2 - 2, char.y - char.size/6 + bobOffset);
        ctx.rotate(armSwing * 0.3);
        ctx.fillRect(-1, -2, 3, char.size/3);
        ctx.restore();
        
        // Right arm
        ctx.save();
        ctx.translate(char.x + char.size/2 + 2, char.y - char.size/6 + bobOffset);
        ctx.rotate(-armSwing * 0.3);
        ctx.fillRect(-2, -2, 3, char.size/3);
        ctx.restore();
        
        // Head
        ctx.fillStyle = '#FDBCB4';
        ctx.beginPath();
        ctx.arc(char.x, char.y - char.size/2 + bobOffset, char.size/3, 0, Math.PI * 2);
        ctx.fill();
        
        // Head outline
        ctx.strokeStyle = '#CD853F';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Hair
        ctx.fillStyle = '#8B4513';
        ctx.beginPath();
        ctx.arc(char.x - 1, char.y - char.size/2 - 2 + bobOffset, char.size/3 - 1, 0, Math.PI);
        ctx.fill();
        
        // Eyes
        ctx.fillStyle = '#000';
        ctx.beginPath();
        ctx.arc(char.x - 2, char.y - char.size/2 - 1 + bobOffset, 1, 0, Math.PI * 2);
        ctx.arc(char.x + 2, char.y - char.size/2 - 1 + bobOffset, 1, 0, Math.PI * 2);
        ctx.fill();
        
        // Nose (tiny line)
        ctx.strokeStyle = '#CD853F';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(char.x, char.y - char.size/2 + 1 + bobOffset);
        ctx.lineTo(char.x, char.y - char.size/2 + 3 + bobOffset);
        ctx.stroke();
        
        // Belt
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(char.x - char.size/2, char.y + bobOffset, char.size, 3);
        
        // Belt buckle
        ctx.fillStyle = '#FFD700';
        ctx.fillRect(char.x - 2, char.y + bobOffset, 4, 3);
        
        // Tools on belt (pickaxe handle)
        if (char.moving) {
            ctx.strokeStyle = '#8B4513';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(char.x + char.size/2 + 3, char.y + bobOffset);
            ctx.lineTo(char.x + char.size/2 + 3, char.y + char.size/3 + bobOffset);
            ctx.stroke();
        }
    }
    
    gameLoop() {
        const currentTime = Date.now();
        const dt = Math.min((currentTime - this.lastUpdateTime) / 1000, 1/30); // Cap at 30fps minimum
        this.lastUpdateTime = currentTime;
        
        this.updateGame(dt);
        this.render();
        
        if (this.running) {
            requestAnimationFrame(() => this.gameLoop());
        }
    }
}

// Start the game when the page loads
window.addEventListener('load', () => {
    new BridgeKeeperGame();
});