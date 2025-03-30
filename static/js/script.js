document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('#sidebar');
    const main = document.querySelector('main');
    const cartButton = document.querySelector('#cartButton');
    const cartButtonMobile = document.querySelector('#cartButtonMobile');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, a.navbar-brand, header .icon-button[href]');
    const animationDuration = 300;


    function openSidebarDesktop() {
        main.classList.add('sidebar-open');
        cartButton.classList.add('active');
    }

    function closeSidebarDesktop() {
        main.classList.remove('sidebar-open');
        cartButton.classList.remove('active');
    }

    function openSidebarMobile() {
        main.classList.add('move-left');
        sidebar.classList.add('align-left');
        cartButtonMobile.classList.add('active');
    }

    function closeSidebarMobile() {
        main.classList.remove('move-left');
        sidebar.classList.remove('align-left');
        cartButtonMobile.classList.remove('active');
    }

    cartButton.addEventListener('click', () => {
        if (window.innerWidth >= 768) {
            if (main.classList.contains('sidebar-open')) {
                closeSidebarDesktop();
            } else {
                openSidebarDesktop();
            }
        } else {
             console.log('cart button clicked on small screen');
        }
    });

    cartButtonMobile.addEventListener('click', () => {
         if (window.innerWidth < 768) {
            if (main.classList.contains('move-left')) {
                closeSidebarMobile();
            } else {
                openSidebarMobile();
            }
        } else {
             if (main.classList.contains('sidebar-open')) {
                closeSidebarDesktop();
            } else {
                openSidebarDesktop();
            }
        }
    });

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            const destinationUrl = event.currentTarget.href;

            const isSidebarOpenDesktop = main.classList.contains('sidebar-open');
            const isSidebarOpenMobile = main.classList.contains('move-left');
            const isSidebarOpen = isSidebarOpenDesktop || isSidebarOpenMobile;

            if (isSidebarOpen && destinationUrl && destinationUrl !== '#') {
                event.preventDefault();

                if (isSidebarOpenDesktop) {
                    closeSidebarDesktop();
                }
                if (isSidebarOpenMobile) {
                    closeSidebarMobile();
                }

                setTimeout(() => {
                    window.location.href = destinationUrl;
                }, animationDuration);

            } else {
                console.log('Sidebar closed or or not nav link');
            }
        });
    });

     window.addEventListener('resize', () => {
         if (window.innerWidth >= 768) {
             if (main.classList.contains('move-left')) {
                 closeSidebarMobile();
             }
         } else {
             if (main.classList.contains('sidebar-open')) {
                 closeSidebarDesktop();
             }
         }
     });
});