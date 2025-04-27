/**
 * @file script.js
 * @description Core client-side script for the E-commerce project.
 * Handles interactive elements like the sidebar (user, assistant, cart),
 * asynchronous cart operations (add/remove), dynamic UI updates based on AJAX responses,
 * automatic dismissal of messages, and smooth page transitions when navigating
 * from the open sidebar. Requires Bootstrap 5 JS and potentially jQuery (though mostly vanilla JS used).
 */

document.addEventListener("DOMContentLoaded", () => {
    const slideContainer = document.querySelector("#slideContainer");
    const sidebar = document.querySelector("#sidebar");
    const sidebarContent = document.querySelector("#sidebar .carousel-inner");
    const messagesContainer = document.querySelector("#messages");
    const navLinks = document.querySelectorAll(
        ".navbar-nav .nav-link, a.navbar-brand, header .icon-button[href], #pageContainer a[href]"
    );
    const sidebarControls = {
        user: document.querySelectorAll(".user-button"),
        assistant: document.querySelectorAll(".assistant-button"),
        cart: document.querySelectorAll(".cart-button"),
    };
    const sidebarControlButtons = document.querySelectorAll(".sidebar-control");
    const sidebarCarousel = bootstrap.Carousel.getOrCreateInstance(sidebar);
    const sidebarCarouselItems = document.querySelectorAll(
        "#sidebar .carousel-item"
    );
    const chatContainer = document.querySelector("#chatContainer");
    const addToCartForms = document.querySelectorAll(".add-to-cart-form");
    const animationDuration = 300;
    const messageDelay = 3000;
    let isSidebarOpen = false;

    function autoCloseAlerts(
        containerSelector = "#messages",
        delay = messageDelay
    ) {
        const messageContainer = document.querySelector(containerSelector);
        if (!messageContainer) {
            console.warn(
                "Message container not found for auto-closing:",
                containerSelector
            );
            return;
        }

        const alerts = messageContainer.querySelectorAll(".alert");

        alerts.forEach((alert) => {
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

    /**
     * Updates relevant parts of the UI based on data received from an AJAX response,
     * typically after cart operations. Updates the cart sidebar content and displays
     * any messages returned from the server.
     *
     * @param {object} data - The JSON data received from the AJAX response. Expected properties:
     *                        `cart_sidebar_html` (optional): HTML content for the cart sidebar.
     *                        `messages_html` (optional): HTML content for new messages/alerts.
     */
    function updateUIFromAjax(data) {
        const cartCarouselItem = document.querySelector(
            "#sidebar .carousel-item:nth-child(3)"
        );
        if (cartCarouselItem && data.cart_sidebar_html !== undefined) {
            cartCarouselItem.innerHTML = data.cart_sidebar_html;
        } else if (data.cart_sidebar_html !== undefined) {
            console.error("Cart carousel item not found for updating.");
        }

        if (
            messagesContainer &&
            data.messages_html &&
            data.messages_html.trim() !== ""
        ) {
            messagesContainer.insertAdjacentHTML(
                "beforeend",
                data.messages_html
            );
            setTimeout(() => {
                const alertElements =
                    messagesContainer.querySelectorAll(".alert");
                if (alertElements.length > 0) {
                    alertElements.forEach((alert) =>
                        bootstrap.Alert.getOrCreateInstance(alert)
                    );
                    autoCloseAlerts("#messages", messageDelay);
                }
            }, 0);
        }
    }

    /**
     * Manually sets the active item within the Bootstrap sidebar carousel.
     * @param {number} index - The zero-based index of the carousel item to activate.
     */
    function setCarouselItemActive(index) {
        sidebarCarouselItems.forEach((item, i) => {
            item.classList.toggle("active", i === index);
        });
    }

    /**
     * Sets the 'active' class on the specified sidebar control buttons and removes it from others.
     * @param {NodeListOf<Element>} buttons - A NodeList of button elements to mark as active.
     */
    function setSidebarControlActive(buttons) {
        resetSidebarControls();
        buttons.forEach((button) => button.classList.add("active"));
    }

    /**
     * Removes the 'active' class from all sidebar control buttons.
     */
    function resetSidebarControls() {
        sidebarControlButtons.forEach((button) =>
            button.classList.remove("active")
        );
    }

    /**
     * Opens or closes the sidebar with appropriate animations based on screen size.
     * Adds/removes classes to slide/push content.
     * @param {boolean} open - True to open the sidebar, false to close it.
     */
    function toggleSidebar(open) {
        if (open) {
            if (window.innerWidth >= 768) {
                sidebar.classList.add("sidebar-open");
                if (messagesContainer)
                    messagesContainer.classList.add("sidebar-push");
            } else {
                slideContainer.classList.add("slide-left");
                if (messagesContainer)
                    messagesContainer.classList.add("slide-left");
            }
        } else {
            sidebar.classList.remove("sidebar-open");
            slideContainer.classList.remove("slide-left");
            if (messagesContainer) {
                messagesContainer.classList.remove("sidebar-push");
                messagesContainer.classList.remove("slide-left");
            }
            resetSidebarControls();
        }
        isSidebarOpen = open;
    }

    /**
     * Toggles a specific section (carousel item) in the sidebar.
     * If the section's button is already active, it closes the sidebar.
     * If the sidebar is open, it navigates the carousel.
     * If the sidebar is closed, it activates the correct carousel item and opens the sidebar.
     * Updates the active state of the control buttons.
     *
     * @param {string} section - The key ('user', 'assistant', 'cart') corresponding to the section.
     * @param {number} index - The zero-based index of the carousel item for this section.
     */
    function toggleSection(section, index) {
        if (sidebarControls[section][0].classList.contains("active")) {
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

    // Add click listeners for the main sidebar control buttons
    sidebarControls.user.forEach((button) =>
        button.addEventListener("click", () => toggleSection("user", 0))
    );

    sidebarControls.assistant.forEach((button) =>
        button.addEventListener("click", () => {
            toggleSection("assistant", 1);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
    );

    sidebarControls.cart.forEach((button) =>
        button.addEventListener("click", () => toggleSection("cart", 2))
    );

    // Add listeners to navigation links for smooth page transitions when sidebar is open
    navLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            const destinationUrl = event.currentTarget.href;
            if (
                isSidebarOpen &&
                destinationUrl &&
                !destinationUrl.endsWith("#") &&
                !destinationUrl.includes(window.location.pathname + "#")
            ) {
                const isInsideSidebar = sidebar.contains(event.target);
                const isHeaderLink = event.currentTarget.closest("header");
                const isOrderHistoryLink = event.target.closest(
                    ".order-history-link"
                );

                if (
                    !isOrderHistoryLink &&
                    (isInsideSidebar ||
                        isHeaderLink ||
                        event.currentTarget.closest("#pageContainer"))
                ) {
                    event.preventDefault();
                    toggleSidebar(false);
                    setTimeout(
                        () => (window.location.href = destinationUrl),
                        animationDuration
                    );
                }
            }
        });
    });

    // Add submit listeners to all 'Add to Cart' forms for AJAX submission
    addToCartForms.forEach((form) => {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            const productId = this.dataset.productId;
            const formData = new FormData(this);
            sendAddToCartRequest(productId, formData);
        });
    });

    /**
     * Sends an asynchronous request to add a product to the cart.
     * Handles the response to update the UI (cart sidebar, messages).
     * Optionally opens the cart sidebar on success if specific conditions are met.
     *
     * @param {string} productId - The ID of the product to add.
     * @param {FormData} formData - The form data (containing quantity, CSRF token, etc.).
     */
    function sendAddToCartRequest(productId, formData) {
        fetch(`/cart/add/${productId}/`, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
            },
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.text().then((text) => {
                        throw new Error(
                            text ||
                                `Network error ${response.status} adding item.`
                        );
                    });
                }
            })
            .then((data) => {
                updateUIFromAjax(data);
                if (
                    data.status === "success" &&
                    data.cart_sidebar_html !== undefined &&
                    !isSidebarOpen &&
                    window.innerWidth >= 768 &&
                    data.messages_html &&
                    data.messages_html.includes("alert-success")
                ) {
                    toggleSection("cart", 2);
                }
            })
            .catch((error) => {
                console.error("There was a problem adding to the cart:", error);
                if (messagesContainer) {
                    const errorHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Failed to add item to cart. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                    messagesContainer.insertAdjacentHTML(
                        "beforeend",
                        errorHtml
                    );
                    setTimeout(() => {
                        const errorAlert = messagesContainer.lastElementChild;
                        if (
                            errorAlert &&
                            errorAlert.classList.contains("alert")
                        ) {
                            bootstrap.Alert.getOrCreateInstance(errorAlert);
                            autoCloseAlerts("#messages", messageDelay);
                        }
                    }, 0);
                }
            });
    }

    /**
     * Sends an asynchronous request to remove a product from the cart.
     * Handles the response to update the UI (cart sidebar, messages).
     *
     * @param {string} productId - The ID of the product to remove.
     * @param {string} csrfToken - The CSRF token value.
     */
    function sendRemoveFromCartRequest(productId, csrfToken) {
        fetch(`/cart/remove/${productId}/`, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken,
            },
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.text().then((text) => {
                        throw new Error(
                            text || "Network response was not ok removing item."
                        );
                    });
                }
            })
            .then((data) => {
                updateUIFromAjax(data);
            })
            .catch((error) => {
                console.error(
                    "There was a problem removing the item from the cart:",
                    error
                );
                if (messagesContainer) {
                    const errorHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Failed to remove item from cart. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                    messagesContainer.insertAdjacentHTML(
                        "beforeend",
                        errorHtml
                    );
                    setTimeout(() => {
                        const errorAlert = messagesContainer.lastElementChild;
                        if (
                            errorAlert &&
                            errorAlert.classList.contains("alert")
                        ) {
                            bootstrap.Alert.getOrCreateInstance(errorAlert);
                            autoCloseAlerts("#messages", messageDelay);
                        }
                    }, 0);
                }
            });
    }

    // Add a single click listener to the sidebar's content area for dynamic elements
    if (sidebarContent) {
        sidebarContent.addEventListener("click", function (event) {
            const removeButton = event.target.closest(
                ".remove-from-cart-button"
            );
            const productLink = event.target.closest('a[href*="/product/"]');
            const checkoutButtonTarget =
                event.target.closest("#checkout-button");
            const orderListItemLink = event.target.closest(
                ".order-history-item-link"
            );
            const manageAddressLink = event.target.closest(
                ".profile-action-link"
            );

            if (removeButton) {
                event.preventDefault();
                const productId = removeButton.dataset.productId;
                const csrfTokenMeta = document.querySelector(
                    'meta[name="csrf-token"]'
                );
                const csrfToken = csrfTokenMeta ? csrfTokenMeta.content : null;

                if (productId && csrfToken) {
                    sendRemoveFromCartRequest(productId, csrfToken);
                } else {
                    console.error(
                        "Could not find product ID or CSRF token for removal."
                    );
                    if (!productId)
                        console.error(
                            "Product ID missing from button data attribute."
                        );
                    if (!csrfToken)
                        console.error(
                            "CSRF token meta tag not found or empty."
                        );
                    if (messagesContainer) {
                        messagesContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">Error removing item: Missing required data.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                        const alertElement =
                            messagesContainer.querySelector(".alert");
                        if (alertElement)
                            bootstrap.Alert.getOrCreateInstance(alertElement);
                    }
                }
            } else if (
                checkoutButtonTarget ||
                productLink ||
                orderListItemLink ||
                manageAddressLink
            ) {
                event.preventDefault();
                const targetUrl = (
                    checkoutButtonTarget ||
                    productLink ||
                    orderListItemLink ||
                    manageAddressLink
                ).href;

                if (targetUrl && targetUrl !== "#") {
                    if (isSidebarOpen) {
                        toggleSidebar(false);
                        setTimeout(() => {
                            window.location.href = targetUrl;
                        }, animationDuration);
                    } else {
                        window.location.href = targetUrl;
                    }
                } else {
                    console.warn(
                        "Clicked sidebar link/button has no valid href:",
                        event.target
                    );
                }
            }
        });
    } else {
        console.error(
            "Sidebar content container not found for event delegation."
        );
    }

    // Close sidebar on window resize to prevent layout issues
    window.addEventListener("resize", () => {
        if (isSidebarOpen) {
            toggleSidebar(false);
        }
    });

    // Initialize auto-closing for any messages present on initial page load
    autoCloseAlerts("#messages", messageDelay);
});
