// Toggle mobile menu
function toggleMenu() {
    const navLinks = document.getElementById('navLinks');
    navLinks.classList.toggle('active');
}

// Toggle abstract visibility
function toggleAbstract(button) {
    const abstractContent = button.nextElementSibling;
    abstractContent.classList.toggle('show');
    
    // Change button text
    if (abstractContent.classList.contains('show')) {
        button.textContent = 'Hide Abstract';
    } else {
        button.textContent = 'Abstract';
    }
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(e) {
    const nav = document.querySelector('nav');
    const navLinks = document.getElementById('navLinks');
    const menuToggle = document.querySelector('.menu-toggle');
    
    if (!nav.contains(e.target) && navLinks.classList.contains('active')) {
        navLinks.classList.remove('active');
    }
});

// Open the mobile menu from the keyboard
const menuToggleButton = document.querySelector('.menu-toggle');
if (menuToggleButton) {
    menuToggleButton.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleMenu();
        }
    });
}

// On phones and tablets, open links in the same tab. In-app browsers (opened from X,
// LinkedIn, Instagram, ...) often silently ignore links that ask for a new tab.
const touchDevice = window.matchMedia('(hover: none) and (pointer: coarse)').matches;

function openLinksInSameTab(root) {
    if (!touchDevice) {
        return;
    }
    root.querySelectorAll('a[target="_blank"]').forEach(function(a) {
        a.removeAttribute('target');
    });
}

openLinksInSameTab(document);

// Light / dark theme toggle (light is the default; the choice is remembered)
const themeToggle = document.querySelector('.theme-toggle');
if (themeToggle) {
    const root = document.documentElement;
    const themeLabel = themeToggle.querySelector('.theme-label');

    function syncThemeToggle() {
        const dark = root.dataset.theme === 'dark';
        themeLabel.textContent = dark ? 'Light' : 'Dark';
        themeToggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    }

    themeToggle.addEventListener('click', function() {
        const dark = root.dataset.theme !== 'dark';
        if (dark) {
            root.dataset.theme = 'dark';
        } else {
            delete root.dataset.theme;
        }
        try {
            localStorage.setItem('theme', dark ? 'dark' : 'light');
        } catch (e) {}
        syncThemeToggle();
    });

    syncThemeToggle();
}

// Section headings: show how many entries each holds, and number them when a page has several
function slugify(text) {
    return text.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function countEntries(el, title) {
    const count = function(selector) {
        return (el.matches(selector) ? 1 : 0) + el.querySelectorAll(selector).length;
    };
    const kinds = [
        ['.in-progress-item', 'project'],
        ['.talk-item:has(.mention-source)', 'mention'],
        ['.year-section .talk-item', 'talk'],
        ['.talk-item', 'essay'],
        ['.discussion-item', 'discussion'],
        ['.mentor-item', 'mentor'],
        ['.gallery-item', 'photo']
    ];
    for (const [selector, noun] of kinds) {
        const n = count(selector);
        if (n) {
            return { n: n, noun: noun };
        }
    }
    if (el.matches('.paper-item')) {
        return { n: 1, noun: /essay/i.test(title.textContent) ? 'essay' : 'paper' };
    }
    return { n: 0, noun: '' };
}

function enhanceSections(root) {
    const titles = Array.from(root.children).filter(function(el) {
        return el.matches('h2.section-title');
    });

    titles.forEach(function(title, i) {
        let total = 0;
        let noun = '';
        for (let el = title.nextElementSibling; el && !el.matches('h2.section-title'); el = el.nextElementSibling) {
            const found = countEntries(el, title);
            total += found.n;
            noun = noun || found.noun;
        }

        const head = document.createElement('div');
        head.className = 'sec-head';
        head.id = slugify(title.textContent);
        title.replaceWith(head);

        if (titles.length > 1) {
            const num = document.createElement('span');
            num.className = 'sec-num';
            num.textContent = String(i + 1).padStart(2, '0');
            head.append(num);
        }
        head.append(title);

        const countEl = document.createElement('span');
        countEl.className = 'sec-count';
        countEl.textContent = total ? total + ' ' + noun + (total === 1 ? '' : 's') : '';
        head.append(countEl);
    });
}

document.querySelectorAll('.page-content').forEach(enhanceSections);

// Homepage: show the research list from research.html, so papers are edited in one place
const homeResearch = document.getElementById('home-research');
if (homeResearch) {
    fetch('research.html', { cache: 'no-cache' })
        .then(function(response) { return response.text(); })
        .then(function(html) {
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const source = doc.querySelector('.page-content');
            if (!source) {
                return;
            }
            homeResearch.replaceChildren.apply(homeResearch, Array.from(source.children).map(function(el) {
                return document.importNode(el, true);
            }));
            enhanceSections(homeResearch);
            openLinksInSameTab(homeResearch);
            if (location.hash) {
                const target = document.getElementById(location.hash.slice(1));
                if (target) {
                    target.scrollIntoView();
                }
            }
        })
        .catch(function() {});
}