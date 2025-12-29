// ===== Smooth Scrolling & Navigation =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== Active Navigation State =====
const sections = document.querySelectorAll('section');
const navLinks = document.querySelectorAll('.nav-links a');

const observerOptions = {
    root: null,
    rootMargin: '-50% 0px -50% 0px',
    threshold: 0
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            navLinks.forEach(link => {
                link.style.color = '';
                if (link.getAttribute('href') === `#${id}`) {
                    link.style.color = '#0071e3';
                }
            });
        }
    });
}, observerOptions);

sections.forEach(section => {
    observer.observe(section);
});

// ===== Scroll Animations =====
const animateOnScroll = () => {
    const elements = document.querySelectorAll('.bento-card, .project-card, .timeline-item, .skill-tag');

    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;

        if (elementTop < window.innerHeight - elementVisible) {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }
    });
};

// Initial check
animateOnScroll();
window.addEventListener('scroll', animateOnScroll);

// ===== Form Handling =====
const contactForm = document.getElementById('contactForm');

if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const name = formData.get('name');
        const email = formData.get('email');
        const message = formData.get('message');

        // Create mailto link
        const mailtoLink = `mailto:rithwiknavanandula@gmail.com?subject=Portfolio Contact from ${encodeURIComponent(name)}&body=${encodeURIComponent(`From: ${name}\nEmail: ${email}\n\nMessage:\n${message}`)}`;

        window.location.href = mailtoLink;

        // Show success feedback
        const btn = this.querySelector('.submit-btn');
        const originalText = btn.textContent;
        btn.textContent = 'Opening Email Client...';
        btn.style.background = '#34c759';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
            this.reset();
        }, 2000);
    });
}

// ===== Nav background on scroll =====
const topNav = document.querySelector('.top-nav');

window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        topNav.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.08)';
    } else {
        topNav.style.boxShadow = 'none';
    }
});

// ===== Console Easter Egg =====
console.log('%c🚀 Welcome to my portfolio!', 'font-size: 24px; font-weight: bold; color: #0071e3;');
console.log('%cBuilt with ❤️ by Rithwik Navanandula', 'font-size: 14px; color: #6e6e73;');
console.log('%cCheck out my GitHub: https://github.com/RithwikNavanandula', 'font-size: 12px; color: #5856d6;');
