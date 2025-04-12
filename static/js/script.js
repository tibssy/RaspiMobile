document.addEventListener('DOMContentLoaded', () => {
    const slideContainer = document.querySelector('#slideContainer');
    const pageContainer = document.querySelector('#pageContainer');
    const sidebar = document.querySelector('#sidebar');
    const sidebarContent = document.querySelector('#sidebar .carousel-inner');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, a.navbar-brand, header .icon-button[href], #pageContainer a[href]');
    const sidebarControls = {
        user: document.querySelectorAll('.user-button'),
        assistant: document.querySelectorAll('.assistant-button'),
        cart: document.querySelectorAll('.cart-button')
    };
    const sidebarControlButtons = document.querySelectorAll('.sidebar-control');
    const sidebarCarousel = bootstrap.Carousel.getOrCreateInstance(sidebar);
    const sidebarCarouselItems = document.querySelectorAll('#sidebar .carousel-item');
    const chatContainer = document.querySelector('#chatContainer');
    const animationDuration = 300;
    let isSidebarOpen = false;
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');

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
                sidebar.classList.add('sidebar-open');
            } else {
                slideContainer.classList.add('slide-left');
            }
        } else {
            sidebar.classList.remove('sidebar-open');
            slideContainer.classList.remove('slide-left');
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
    sidebarControls.assistant.forEach(button => button.addEventListener('click', () => {
        toggleSection('assistant', 1);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }));
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

    addToCartForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            const productId = this.dataset.productId;
            const formData = new FormData(this);
            sendAddToCartRequest(productId, formData);
        });
    });

    function sendAddToCartRequest(productId, formData) {
        fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
            .then(response => {
                if (response.ok) {
                    return response.text();
                } else {
                    throw new Error('Network response was not ok.');
                }
            })
            .then(cartSidebarHtml => {
                const cartCarouselItem = document.querySelector('#sidebar .carousel-item:nth-child(3)');
                cartCarouselItem.innerHTML = cartSidebarHtml;
            })
            .catch(error => {
                console.error('There was a problem adding to the cart:', error);
            });
    }

    window.addEventListener('resize', () => toggleSidebar(false));
});
