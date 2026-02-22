'use strict';

// ─── Particle Configs for L8-L10 Icons ────────────────────────────────────
// Each key matches an icon_id that has "particle_config" set in ICON_METADATA.
// Configs use the tsParticles v3 slim bundle options schema.

const ICON_PARTICLE_CONFIGS = {

    // ── L8 ──────────────────────────────────────────────────────────────

    firefly_swarm: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 18 },
            color: { value: ['#aaff44', '#ffff00', '#88ee00'] },
            opacity: { value: { min: 0.2, max: 0.8 },
                       animation: { enable: true, speed: 0.8, sync: false } },
            size: { value: { min: 2, max: 4 } },
            move: { enable: true, speed: 0.6, direction: 'none',
                    random: true, outModes: { default: 'bounce' } },
        },
    },

    black_hole: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 30 },
            color: { value: ['#6600cc', '#330066', '#9900ff'] },
            opacity: { value: { min: 0.1, max: 0.6 } },
            size: { value: { min: 1, max: 3 } },
            move: { enable: true, speed: 1.2, direction: 'inside',
                    outModes: { default: 'destroy' }, attract: { enable: true, rotate: { x: 600, y: 1200 } } },
        },
    },

    meteor: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 20 },
            color: { value: ['#ff6600', '#ff3300', '#ffaa00'] },
            opacity: { value: { min: 0.3, max: 0.9 },
                       animation: { enable: true, speed: 1.5, sync: false } },
            size: { value: { min: 1, max: 3 } },
            move: { enable: true, speed: 2.0, direction: 'bottom-left',
                    random: true, outModes: { default: 'out' } },
        },
    },

    phoenix_master: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 25 },
            color: { value: ['#ff4400', '#ff8800', '#ffcc00'] },
            opacity: { value: { min: 0.2, max: 0.8 },
                       animation: { enable: true, speed: 2, sync: false } },
            size: { value: { min: 1.5, max: 4 } },
            move: { enable: true, speed: 1.5, direction: 'top',
                    random: true, outModes: { default: 'out' } },
        },
    },

    electric_storm: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 22 },
            color: { value: ['#00d4ff', '#ffffff', '#aaffff'] },
            opacity: { value: { min: 0.1, max: 0.9 },
                       animation: { enable: true, speed: 4, sync: false } },
            size: { value: { min: 0.5, max: 2 } },
            move: { enable: true, speed: 3, direction: 'none',
                    random: true, outModes: { default: 'bounce' } },
        },
    },

    // ── L9 ──────────────────────────────────────────────────────────────

    dragon_ember: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 32 },
            color: { value: ['#ff2200', '#ff6600', '#ff9900', '#ffdd00'] },
            opacity: { value: { min: 0.2, max: 0.85 },
                       animation: { enable: true, speed: 2, sync: false } },
            size: { value: { min: 1.5, max: 4.5 } },
            move: { enable: true, speed: 1.8, direction: 'top',
                    random: true, outModes: { default: 'out' } },
        },
    },

    spaceship: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 55 },
            color: { value: '#ffffff' },
            shape: { type: 'star' },
            opacity: { value: { min: 0.1, max: 0.65 },
                       animation: { enable: true, speed: 0.5, sync: false } },
            size: { value: { min: 0.5, max: 2 } },
            move: { enable: true, speed: 0.3, random: true,
                    outModes: { default: 'out' } },
        },
    },

    cosmic_wolf: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 40 },
            color: { value: ['#ffffff', '#aabbff', '#cc99ff', '#eeddff'] },
            opacity: { value: { min: 0.1, max: 0.6 },
                       animation: { enable: true, speed: 0.6, sync: false } },
            size: { value: { min: 0.5, max: 2.5 } },
            move: { enable: true, speed: 0.4, random: true,
                    outModes: { default: 'out' } },
        },
    },

    supernova: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 45 },
            color: { value: ['#ffffff', '#ffffaa', '#ffeeaa', '#ffd700', '#ff8800'] },
            opacity: { value: { min: 0.2, max: 0.9 },
                       animation: { enable: true, speed: 2.5, sync: false } },
            size: { value: { min: 1, max: 4 } },
            move: { enable: true, speed: 2.5, direction: 'outside',
                    random: true, outModes: { default: 'destroy' } },
        },
    },

    ice_titan: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 28 },
            color: { value: ['#aaddff', '#cceeFF', '#eef8ff', '#ffffff'] },
            shape: { type: ['circle', 'edge'] },
            opacity: { value: { min: 0.2, max: 0.7 },
                       animation: { enable: true, speed: 0.7, sync: false } },
            size: { value: { min: 1, max: 3.5 } },
            move: { enable: true, speed: 0.5, direction: 'bottom',
                    random: true, outModes: { default: 'out' } },
        },
    },

    // ── L10 ─────────────────────────────────────────────────────────────

    galaxy: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 75 },
            color: { value: ['#ffffff', '#aabbff', '#cc99ff', '#ffddff'] },
            opacity: { value: { min: 0.05, max: 0.55 },
                       animation: { enable: true, speed: 0.4, sync: false } },
            size: { value: { min: 0.3, max: 2 } },
            move: { enable: true, speed: 0.2, random: true,
                    outModes: { default: 'out' } },
        },
    },

    infinity_ultimate: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 40 },
            color: { value: ['#00d4ff', '#ffd700', '#ff006e', '#39ff14', '#8338ec'] },
            opacity: { value: { min: 0.2, max: 0.8 },
                       animation: { enable: true, speed: 1.5, sync: false } },
            size: { value: { min: 1, max: 3 } },
            move: { enable: true, speed: 1.0, direction: 'none',
                    random: true, outModes: { default: 'bounce' },
                    orbit: { enable: true, radius: 50, speed: { min: 0.5, max: 1.5 } } },
        },
    },

    titan_god: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 50 },
            color: { value: ['#ffd700', '#ffaa00', '#ffffff'] },
            opacity: { value: { min: 0.2, max: 0.85 },
                       animation: { enable: true, speed: 2, sync: false } },
            size: { value: { min: 1, max: 4 } },
            move: { enable: true, speed: 1.2, direction: 'outside',
                    random: true, outModes: { default: 'out' } },
        },
    },

    void_dragon: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 60 },
            color: { value: ['#ffffff', '#ccddff', '#9966ff'] },
            shape: { type: 'star' },
            opacity: { value: { min: 0.05, max: 0.7 },
                       animation: { enable: true, speed: 0.8, sync: false } },
            size: { value: { min: 0.3, max: 2.5 } },
            move: { enable: true, speed: 0.25, random: true,
                    outModes: { default: 'out' } },
        },
    },

    omega: {
        background: { color: { value: 'transparent' } },
        particles: {
            number: { value: 55 },
            color: { value: ['#ffffff', '#00ffff', '#ff00ff', '#ffd700'] },
            opacity: { value: { min: 0.15, max: 0.9 },
                       animation: { enable: true, speed: 3, sync: false } },
            size: { value: { min: 0.5, max: 3 } },
            move: { enable: true, speed: 2.0, random: true,
                    outModes: { default: 'out' } },
        },
    },
};


// ─── Particle Initialization Helpers ──────────────────────────────────────

/**
 * Initialize a tsParticles effect inside a container div.
 * Returns the tsParticles container instance or null.
 */
async function _loadParticles(containerId, iconId) {
    if (typeof tsParticles === 'undefined') return null;
    const config = ICON_PARTICLE_CONFIGS[iconId];
    if (!config) return null;
    try {
        return await tsParticles.load({ id: containerId, options: config });
    } catch (e) {
        console.warn('[gamification] tsParticles failed:', e);
        return null;
    }
}

/**
 * Inject a positioned particle canvas div into a host element.
 * Returns the canvas div element.
 */
function _injectParticleDiv(host, id) {
    let div = document.getElementById(id);
    if (!div) {
        div = document.createElement('div');
        div.id = id;
        div.style.cssText = 'position:absolute;inset:0;z-index:0;pointer-events:none;border-radius:inherit;';
        host.insertBefore(div, host.firstChild);
    }
    return div;
}


// ─── Login Page Particle Init ──────────────────────────────────────────────

/**
 * Initialize ambient particle effects for L8+ user cards on the login page.
 * Called after DOMContentLoaded.
 */
function initLoginParticles() {
    document.querySelectorAll('.user-card').forEach(function(card) {
        const level = parseInt(card.dataset.level || '0', 10);
        if (level < 8) return;

        const avatar = card.querySelector('.user-card-avatar');
        if (!avatar) return;
        const iconId = avatar.dataset.iconId;
        if (!iconId || !ICON_PARTICLE_CONFIGS[iconId]) return;

        // Ensure host has position:relative (icon-particle-host class handles this)
        avatar.classList.add('icon-particle-host');

        const uid = 'particles-login-' + iconId + '-' + Math.random().toString(36).slice(2, 6);
        _injectParticleDiv(avatar, uid);
        _loadParticles(uid, iconId);
    });
}


// ─── Profile Page Particle Init ───────────────────────────────────────────

let _activeProfileContainer = null;

/**
 * Initialize a particle effect behind the profile icon preview.
 * Destroys any previous particle container first.
 * @param {string} iconId - The currently-selected icon ID
 */
async function initProfileParticle(iconId) {
    // Destroy previous instance
    if (_activeProfileContainer) {
        try { _activeProfileContainer.destroy(); } catch (_) {}
        _activeProfileContainer = null;
    }

    const host = document.getElementById('profile-icon-preview');
    if (!host || !ICON_PARTICLE_CONFIGS[iconId]) return;

    const canvasId = 'profile-particle-canvas';
    _injectParticleDiv(host, canvasId);
    _activeProfileContainer = await _loadParticles(canvasId, iconId);
}
