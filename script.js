// Keep the mobile menu and its accessible state in sync.
function setMenuOpen(open) {
    const navLinks = document.getElementById('navLinks');
    const menuToggle = document.querySelector('.menu-toggle');
    if (navLinks && menuToggle) {
        navLinks.classList.toggle('active', open);
        menuToggle.setAttribute('aria-expanded', String(open));
    }
}

function toggleMenu() {
    const navLinks = document.getElementById('navLinks');
    if (navLinks) {
        setMenuOpen(!navLinks.classList.contains('active'));
    }
}

// Toggle abstract visibility
function toggleAbstract(button) {
    const abstractContent = button.closest('.paper-item')?.querySelector('.abstract-content') || button.nextElementSibling;
    const open = abstractContent.classList.toggle('show');
    button.textContent = open ? 'Hide Abstract' : 'Abstract';
    button.setAttribute('aria-expanded', String(open));
}

// Close the menu after choosing a link, clicking outside, or pressing Escape.
document.addEventListener('click', function(e) {
    const header = document.querySelector('.nav-container');
    if (header && (!header.contains(e.target) || e.target.closest('#navLinks a'))) {
        setMenuOpen(false);
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const navLinks = document.getElementById('navLinks');
        if (navLinks && navLinks.classList.contains('active')) {
            setMenuOpen(false);
            document.querySelector('.menu-toggle').focus();
        }
    }
});

// Small screens and touch-capable browsers use normal same-tab navigation.
// Some in-app browsers ignore new-tab requests, and hybrid devices can report
// a mouse as their primary pointer even when the visitor is tapping the screen.
const mobileLinks = window.matchMedia('(max-width: 1040px), (any-pointer: coarse)');
const originalLinkTargets = new WeakMap();

function openLinksInSameTab(root) {
    root.querySelectorAll('a').forEach(function(a) {
        if (a.getAttribute('target') === '_blank') {
            originalLinkTargets.set(a, '_blank');
        }
        if (originalLinkTargets.has(a)) {
            if (mobileLinks.matches) {
                a.removeAttribute('target');
            } else {
                a.setAttribute('target', originalLinkTargets.get(a));
            }
        }
    });
}

openLinksInSameTab(document);
function syncMobileLinks() {
    openLinksInSameTab(document);
    setMenuOpen(false);
}
if (mobileLinks.addEventListener) {
    mobileLinks.addEventListener('change', syncMobileLinks);
} else {
    mobileLinks.addListener(syncMobileLinks);
}

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

function addCitations(root = document) {
const papers = [
{match:'Technology_Bottlenecks',key:'shukla2026bottlenecks',authors:'Shukla, Soumitra',year:'2026',title:'Technology Bottlenecks: Measuring Where AI Could Raise the Value of Work It Cannot Yet Do',url:'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7605598'},
{match:'Pyramids_Diamonds',key:'friebel2026pyramids',authors:'Friebel, Guido and Huang, Yao and Li, Jin and Shukla, Soumitra and Zhang, Andrew',display:'Friebel, Guido, Yao Huang, Jin Li, Soumitra Shukla, and Andrew Zhang',year:'2026',title:'Pyramids, Diamonds, and Oscillations: AI and the Structure of Internal Labor Markets',url:'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6570519'},
{match:'5681703',key:'ash2025interviews',authors:'Ash, Elliott and Shukla, Soumitra and Sockin, Jason',display:'Ash, Elliott, Soumitra Shukla, and Jason Sockin',year:'2025',title:'Interviews',url:'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5681703'},
{match:'making_the_elite',key:'shukla2025elite',authors:'Shukla, Soumitra',year:'2025',title:'Making the Elite: Caste, Class, and Cultural Capital at Multinationals',url:'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4497449'}
];
for(const [i,p] of papers.entries()) {
const item=Array.from(root.querySelectorAll('.paper-item')).find(el=>el.querySelector('.paper-title a')?.getAttribute('href').includes(p.match));
if(!item || item.dataset.citationReady)continue;
item.dataset.citationReady = "true";
const abstract=item.querySelector('.abstract-toggle');
abstract.setAttribute('aria-expanded', 'false');
const actions=document.createElement('div');actions.className='paper-actions';abstract.before(actions);actions.append(abstract);
const toggle=document.createElement('button');toggle.className='cite-toggle';toggle.type='button';toggle.textContent='Cite as +';toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-controls',`citation-${i}`);actions.append(toggle);
const panel=document.createElement('div');panel.className='citation-panel';panel.id=`citation-${i}`;panel.hidden=true;
const toolbar=document.createElement('div');toolbar.className='citation-toolbar';toolbar.setAttribute('role','tablist');toolbar.setAttribute('aria-label',`Citation format for ${p.title}`);
const content=document.createElement('pre');content.className='citation-content';content.id=`citation-content-${p.key}`;content.setAttribute('role','tabpanel');
const plain=`${p.display||p.authors}. ${p.year}. “${p.title}.” Working paper. ${p.url}`;
const bib=`@unpublished{${p.key},\n  author = {${p.authors}},\n  title = {{${p.title}}},\n  year = {${p.year}},\n  note = {Working paper},\n  url = {${p.url}}\n}`;
let selected=plain;content.setAttribute('aria-labelledby',`${p.key}-citation`);
for(const [label,value] of [['Citation',plain],['BibTeX',bib]]) {
const b=document.createElement('button');b.type='button';b.className='citation-tab';b.textContent=label;b.setAttribute('role','tab');b.id=`${p.key}-${label.toLowerCase()}`;b.setAttribute('aria-controls',content.id);b.setAttribute('aria-selected',String(value===plain));
b.onclick=()=>{selected=value;content.setAttribute('aria-labelledby',b.id);content.textContent=value;content.classList.toggle('bibtex',label==='BibTeX');toolbar.querySelectorAll('[role=tab]').forEach(x=>x.setAttribute('aria-selected',String(x===b)));copy.textContent='Copy';};toolbar.append(b);
}
toolbar.addEventListener('keydown',event=>{
if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
event.preventDefault();
const tabs=Array.from(toolbar.querySelectorAll('[role=tab]'));const current=tabs.indexOf(document.activeElement);
const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(current+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].focus();tabs[next].click();
});
const copy=document.createElement('button');copy.type='button';copy.className='citation-copy';copy.textContent='Copy';copy.setAttribute('aria-live','polite');copy.onclick=async()=>{try{await navigator.clipboard.writeText(selected);copy.textContent='Copied';}catch{copy.textContent='Select text to copy';}};toolbar.append(copy);
content.textContent=plain;panel.append(toolbar,content);item.querySelector('.abstract-content').after(panel);
toggle.onclick=()=>{panel.hidden=!panel.hidden;toggle.textContent=panel.hidden?'Cite as +':'Cite as −';toggle.setAttribute('aria-expanded',String(!panel.hidden));};
}
}

document.querySelectorAll('.page-content').forEach(enhanceSections);
addCitations();

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
            addCitations(homeResearch);
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