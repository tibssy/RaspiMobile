document.addEventListener('DOMContentLoaded', () => {
    const slideContainer = document.querySelector('#slideContainer');
    const pageContainer = document.querySelector('#pageContainer');
    const sidebar = document.querySelector('#sidebar');
    const sidebarContent = document.querySelector('#sidebar .carousel-inner');
    const messagesContainer = document.querySelector('#messages');
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
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
//    const checkoutButton = document.querySelector('#checkout-button');
    const animationDuration = 300;
    const messageDelay = 3000;
    let isSidebarOpen = false;


    function autoCloseAlerts(containerSelector = '#messages', delay = messageDelay) {
        const messageContainer = document.querySelector(containerSelector);
        if (!messageContainer) {
            console.warn("Message container not found for auto-closing:", containerSelector);
            return;
        }

        const alerts = messageContainer.querySelectorAll('.alert');

        alerts.forEach(alert => {
            if (!alert.dataset.autoCloseTimeoutId) {
                const timeoutId = setTimeout(() => {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    if (bsAlert) {
                        bsAlert.close();
                    } else {
                        alert.remove();
                    }
                    if (alert.dataset.autoCloseTimeoutId) {
                       delete alert.dataset.autoCloseTimeoutId;
                    }
                }, delay);
                alert.dataset.autoCloseTimeoutId = timeoutId;
            }
        });
    }

    function updateUIFromAjax(data) {
        const cartCarouselItem = document.querySelector('#sidebar .carousel-item:nth-child(3)');
        if (cartCarouselItem && data.cart_sidebar_html !== undefined) {
            cartCarouselItem.innerHTML = data.cart_sidebar_html;
        } else if (data.cart_sidebar_html !== undefined) {
            console.error("Cart carousel item not found for updating.");
        }

        if (messagesContainer && data.messages_html && data.messages_html.trim() !== '') {
            messagesContainer.insertAdjacentHTML('beforeend', data.messages_html);
            setTimeout(() => {
                const alertElements = messagesContainer.querySelectorAll('.alert');
                if (alertElements.length > 0) {
                    alertElements.forEach(alert => bootstrap.Alert.getOrCreateInstance(alert));
                    autoCloseAlerts('#messages', messageDelay);
                }
            }, 0);
        }
    }

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
                if (messagesContainer) messagesContainer.classList.add('sidebar-push');
            } else {
                slideContainer.classList.add('slide-left');
                if (messagesContainer) messagesContainer.classList.add('slide-left');
            }
        } else {
            sidebar.classList.remove('sidebar-open');
            slideContainer.classList.remove('slide-left');
            if (messagesContainer) {
                messagesContainer.classList.remove('sidebar-push');
                messagesContainer.classList.remove('slide-left')
            }
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
                return response.json();
            } else {
                return response.text().then(text => { throw new Error(text || 'Network response was not ok adding item.') });
            }
        })
        .then(data => {
            updateUIFromAjax(data);
            if (!isSidebarOpen && window.innerWidth >= 768 && data.messages_html && data.messages_html.includes('alert-success')) {
                 toggleSection('cart', 2);
            }
        })
        .catch(error => {
            console.error('There was a problem adding to the cart:', error);
            if (messagesContainer) {
                const errorHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Failed to add item to cart. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                messagesContainer.insertAdjacentHTML('beforeend', errorHtml);
                setTimeout(() => {
                    const errorAlert = messagesContainer.lastElementChild;
                    if (errorAlert && errorAlert.classList.contains('alert')) {
                        bootstrap.Alert.getOrCreateInstance(errorAlert);
                        autoCloseAlerts('#messages', messageDelay);
                    }
                }, 0);
            }
        });
    }

    function sendRemoveFromCartRequest(productId, csrfToken) {
        fetch(`/cart/remove/${productId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.text().then(text => { throw new Error(text || 'Network response was not ok removing item.') });
            }
        })
        .then(data => {
            updateUIFromAjax(data);
        })
        .catch(error => {
            console.error('There was a problem removing the item from the cart:', error);
            if (messagesContainer) {
                const errorHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Failed to remove item from cart. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                messagesContainer.insertAdjacentHTML('beforeend', errorHtml);
                setTimeout(() => {
                    const errorAlert = messagesContainer.lastElementChild;
                    if (errorAlert && errorAlert.classList.contains('alert')) {
                        bootstrap.Alert.getOrCreateInstance(errorAlert);
                        autoCloseAlerts('#messages', messageDelay);
                    }
                }, 0);
            }
        });
    }

    if (sidebarContent) {
        sidebarContent.addEventListener('click', function(event) {
            const removeButton = event.target.closest('.remove-from-cart-button');
            const productLink = event.target.closest('a[href*="/product/"]');
            const checkoutButtonTarget = event.target.closest('#checkout-button');

            if (removeButton) {
                event.preventDefault();
                const productId = removeButton.dataset.productId;
                const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfToken = csrfTokenMeta ? csrfTokenMeta.content : null;

                if (productId && csrfToken) {
                    sendRemoveFromCartRequest(productId, csrfToken);
                } else {
                    console.error('Could not find product ID or CSRF token for removal.');
                    if (!productId) console.error('Product ID missing from button data attribute.');
                    if (!csrfToken) console.error('CSRF token meta tag not found or empty.');
                    if (messagesContainer) {
                        messagesContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Error removing item: Missing required data.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                        const alertElement = messagesContainer.querySelector('.alert');
                        if (alertElement) bootstrap.Alert.getOrCreateInstance(alertElement);
                    }
                }

            } else if (productLink) {
                event.preventDefault();
                const productUrl = productLink.href;
                if (isSidebarOpen) {
                    toggleSidebar(false);
                    setTimeout(() => {
                        window.location.href = productUrl;
                    }, animationDuration);
                } else {
                    window.location.href = productUrl;
                }

            } else if (checkoutButtonTarget) {
                console.log('Delegated checkout click detected.');
                event.preventDefault();
                const checkoutUrl = checkoutButtonTarget.href;

                if (isSidebarOpen) {
                    toggleSidebar(false);
                    setTimeout(() => {
                        window.location.href = checkoutUrl;
                    }, animationDuration);
                } else {
                    window.location.href = checkoutUrl;
                }
            }
        });
    } else {
        console.error("Sidebar content container not found for event delegation.");
    }

    window.addEventListener('resize', () => toggleSidebar(false));
    autoCloseAlerts('#messages', 3000);
});