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

// Add smooth scrolling to top when navigating between pages
document.addEventListener('DOMContentLoaded', function() {
    // Optional: Add any additional initialization code here
});