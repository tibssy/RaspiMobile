document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header');
    const main = document.querySelector('main');
    const cartButton = document.querySelector('#cartButton');

    console.log(main);
    console.log(cartButton);
    console.log(window.innerWidth);

    cartButton.addEventListener('click', () => {
        console.log('cart toggled')
        if (window.innerWidth >= 768) {
            main.classList.toggle('sidebar-open');
            header.classList.toggle('sidebar-open');
        } else {
            console.log('small screen')
        }
    });
});