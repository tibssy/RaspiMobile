document.addEventListener('DOMContentLoaded', () => {
    const main = document.querySelector('main');
    const sidebar = document.querySelector('#sidebar');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, a.navbar-brand, header .icon-button[href], main a[href]');
    const sidebarControls = {
        user: document.querySelectorAll('.user-button'),
        assistant: document.querySelectorAll('.assistant-button'),
        cart: document.querySelectorAll('.cart-button')
    };
    const sidebarControlButtons = document.querySelectorAll('.sidebar-control');
    const sidebarCarousel = bootstrap.Carousel.getOrCreateInstance(sidebar);
    const sidebarCarouselItems = document.querySelectorAll('#sidebar .carousel-item');
    const animationDuration = 300;
    let isSidebarOpen = false;

    function setCarouselItemActive(index) {
        sidebarCarouselItems.forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
    }

    function setSidebarControlActive(buttons) {
        resetSidebarControls();
        buttons.forEach(button => button.classList.add('active'));
    }

    function resetSidebarControls() {
        sidebarControlButtons.forEach(button => button.classList.remove('active'));
    }

    function toggleSidebar(open) {
        if (open) {
            if (window.innerWidth >= 768) {
                main.classList.add('sidebar-open');
            } else {
                main.classList.add('move-left');
                sidebar.classList.add('align-left');
            }
        } else {
            main.classList.remove('sidebar-open', 'move-left');
            sidebar.classList.remove('align-left');
            resetSidebarControls();
        }
        isSidebarOpen = open;
    }

    function toggleSection(section, index) {
        if (sidebarControls[section][0].classList.contains('active')) {
            toggleSidebar(false);
            return;
        }

        if (isSidebarOpen) {
            sidebarCarousel.to(index);
        } else {
            setCarouselItemActive(index);
            toggleSidebar(true);
        }

        setSidebarControlActive(sidebarControls[section]);
    }

    sidebarControls.user.forEach(button => button.addEventListener('click', () => toggleSection('user', 0)));
    sidebarControls.assistant.forEach(button => button.addEventListener('click', () => toggleSection('assistant', 1)));
    sidebarControls.cart.forEach(button => button.addEventListener('click', () => toggleSection('cart', 2)));

    navLinks.forEach(link => {
        link.addEventListener('click', event => {
            const destinationUrl = event.currentTarget.href;
            if (isSidebarOpen && destinationUrl && destinationUrl !== '#') {
                event.preventDefault();
                toggleSidebar(false);
                setTimeout(() => (window.location.href = destinationUrl), animationDuration);
            }
        });
    });

    window.addEventListener('resize', () => toggleSidebar(false));
});
