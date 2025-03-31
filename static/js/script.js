document.addEventListener('DOMContentLoaded', () => {
    const main = document.querySelector('main');
    const sidebar = document.querySelector('#sidebar');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, a.navbar-brand, header .icon-button[href]');
    const userButtons = document.querySelectorAll('.user-button');
    const assistantButtons = document.querySelectorAll('.assistant-button');
    const cartButtons = document.querySelectorAll('.cart-button');
    const sidebarControls = document.querySelectorAll('.sidebar-control');
    const sidebarCarousel = bootstrap.Carousel.getOrCreateInstance(sidebar);
    const sidebarCarouselItems = document.querySelectorAll('#sidebar .carousel-item');
    const animationDuration = 300;
    let isSidebarOpen = false;


    function setCarouselItemActive(index) {
        sidebarCarouselItems.forEach(item => {
            item.classList.remove('active');
        });
        sidebarCarouselItems[index].classList.add('active');
    }

    function setSidebarControlActive(control) {
        resetSidebarControls();
        control.forEach(item => {
            item.classList.add('active');
        });
    }

    function resetSidebarControls() {
        sidebarControls.forEach(button => {
            button.classList.remove('active');
        });
    }

    function openSidebar() {
        if (window.innerWidth >= 768) {
            main.classList.add('sidebar-open');
        } else {
            main.classList.add('move-left');
            sidebar.classList.add('align-left');
        }
        isSidebarOpen = true;
    }

    function closeSidebar() {
        main.classList.remove('sidebar-open');
        main.classList.remove('move-left');
        sidebar.classList.remove('align-left');
        resetSidebarControls();
        isSidebarOpen = false;
    }

    function openUser() {
        if (isSidebarOpen) {
            sidebarCarousel.to(0);
        } else {
            setCarouselItemActive(0);
            openSidebar();
        }

        setSidebarControlActive(userButtons);
    }

    function openAssistant() {
        if (isSidebarOpen) {
            sidebarCarousel.to(1);
        } else {
            setCarouselItemActive(1);
            openSidebar();
        }

        setSidebarControlActive(assistantButtons);
    }

    function openCart() {
        if (isSidebarOpen) {
            sidebarCarousel.to(2);
        } else {
            setCarouselItemActive(2);
            openSidebar();
        }

        setSidebarControlActive(cartButtons);
    }

//    Carousel Control Buttons
    userButtons.forEach(button => {
        button.addEventListener('click', openUser);
    });

    assistantButtons.forEach(button => {
        button.addEventListener('click', openAssistant);
    });

    cartButtons.forEach(button => {
        button.addEventListener('click', openCart);
    });

//    Close Sidebar on Redirect
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            const destinationUrl = event.currentTarget.href;

            if (isSidebarOpen && destinationUrl && destinationUrl !== '#') {
                event.preventDefault();
                closeSidebar();

                setTimeout(() => {
                    window.location.href = destinationUrl;
                }, animationDuration);
            }
        });
    });

//    Close Sidebar on Resize
    window.addEventListener('resize', closeSidebar);
});