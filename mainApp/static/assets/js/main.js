document.addEventListener("DOMContentLoaded", (event) => {
    // preloader
    const preloader = document.getElementById('preloader');
    preloader.style.display = 'none';
    document.body.style.position = 'static';

    // HEADER NAV IN MOBILE
    if (document.querySelector(".ul-header-nav")) {
        const ulSidebar = document.querySelector(".ul-sidebar");
        const ulSidebarOpener = document.querySelector(".ul-header-sidebar-opener");
        const ulSidebarCloser = document.querySelector(".ul-sidebar-closer");
        const ulMobileMenuContent = document.querySelector(".to-go-to-sidebar-in-mobile");
        const ulHeaderNavMobileWrapper = document.querySelector(".ul-sidebar-header-nav-wrapper");
        const ulHeaderNavOgWrapper = document.querySelector(".ul-header-nav-wrapper");

        function updateMenuPosition() {
            if (window.innerWidth < 992) {
                ulHeaderNavMobileWrapper.appendChild(ulMobileMenuContent);
            }

            if (window.innerWidth >= 992) {
                ulHeaderNavOgWrapper.appendChild(ulMobileMenuContent);
            }
        }

        updateMenuPosition();

        window.addEventListener("resize", () => {
            updateMenuPosition();
        });

        ulSidebarOpener.addEventListener("click", () => {
            ulSidebar.classList.add("active");
        });

        ulSidebarCloser.addEventListener("click", () => {
            ulSidebar.classList.remove("active");
        });


        // menu dropdown/submenu in mobile
        const ulHeaderNavMobile = document.querySelector(".ul-header-nav");
        const ulHeaderNavMobileItems = ulHeaderNavMobile.querySelectorAll(".has-sub-menu");
        ulHeaderNavMobileItems.forEach((item) => {
            if (window.innerWidth < 992) {
                item.addEventListener("click", () => {
                    item.classList.toggle("active");
                });
            }
        });
    }

    // header search in mobile start
    const ulHeaderSearchOpener = document.querySelector(".ul-header-mobile-search-opener");
    const ulHeaderSearchCloser = document.querySelector(".ul-header-mobile-search-closer");
    if (ulHeaderSearchOpener) {
        ulHeaderSearchOpener.addEventListener("click", () => {
            document.querySelector(".ul-header-search-form-wrapper").classList.add("active");
        });
    }

    if (ulHeaderSearchCloser) {
        ulHeaderSearchCloser.addEventListener("click", () => {
            document.querySelector(".ul-header-search-form-wrapper").classList.remove("active");
        });
    }
    // header search in mobile end

    if (document.querySelector(".ul-header-top-slider")) {
        new Splide('.ul-header-top-slider', {
            arrows: false,
            pagination: false,
            type: 'loop',
            drag: 'free',
            focus: 'center',
            perPage: 9,
            autoWidth: true,
            gap: 15,
            autoScroll: {
                speed: 1.5,
            },
        }).mount(window.splide.Extensions);
    }

    // search category
    if (document.querySelector("#ul-header-search-category")) {
        new SlimSelect({
            select: '#ul-header-search-category',
            settings: {
                showSearch: false,
            }
        })
    }

    // Banner sliders (.ul-banner-slider and .ul-banner-img-slider) are controlled by the % circular queue conveyor in index.html


    // products filtering 
    if (document.querySelector(".ul-filter-products-wrapper")) {
        mixitup('.ul-filter-products-wrapper');
    }


    // product slider
    new Swiper(".ul-products-slider-1", {
        slidesPerView: 3,
        loop: true,
        autoplay: true,
        spaceBetween: 15,
        navigation: {
            nextEl: ".ul-products-slider-1-nav .next",
            prevEl: ".ul-products-slider-1-nav .prev",
        },
        breakpoints: {
            0: {
                slidesPerView: 1,
            },
            480: {
                slidesPerView: 2,
            },
            992: {
                slidesPerView: 3,
            },
            1200: {
                spaceBetween: 20,
            },
            1400: {
                spaceBetween: 22,
            },
            1600: {
                spaceBetween: 26,
            },
            1700: {
                spaceBetween: 30,
            }
        }
    });

    // product slider
    new Swiper(".ul-products-slider-2", {
        slidesPerView: 3,
        loop: true,
        autoplay: true,
        spaceBetween: 15,
        navigation: {
            nextEl: ".ul-products-slider-2-nav .next",
            prevEl: ".ul-products-slider-2-nav .prev",
        },
        breakpoints: {
            0: {
                slidesPerView: 1,
            },
            480: {
                slidesPerView: 2,
            },
            992: {
                slidesPerView: 3,
            },
            1200: {
                spaceBetween: 20,
            },
            1400: {
                spaceBetween: 22,
            },
            1600: {
                spaceBetween: 26,
            },
            1700: {
                spaceBetween: 30,
            }
        }
    });

    // flash sale slider\
    new Swiper(".ul-flash-sale-slider", {
        slidesPerView: 1,
        loop: true,
        autoplay: true,
        spaceBetween: 15,
        breakpoints: {
            480: {
                slidesPerView: 2,
            },
            768: {
                slidesPerView: 3,
            },
            992: {
                slidesPerView: 4,
            },
            1200: {
                spaceBetween: 20,
                slidesPerView: 4,
            },
            1680: {
                spaceBetween: 26,
                slidesPerView: 4,
            },
            1700: {
                spaceBetween: 30,
                slidesPerView: 4,
            }
        }
    })

    // reviews slider
    new Swiper(".ul-reviews-slider", {
        slidesPerView: 1,
        loop: true,
        autoplay: true,
        spaceBetween: 15,
        breakpoints: {
            768: {
                slidesPerView: 2,
            },
            992: {
                spaceBetween: 20,
                slidesPerView: 3,
            },
            1200: {
                spaceBetween: 20,
                slidesPerView: 4,
            },
            1680: {
                slidesPerView: 4,
                spaceBetween: 26,
            },
            1700: {
                slidesPerView: 4,
                spaceBetween: 30,
            }
        }
    });

    // gallery slider
    new Swiper(".ul-gallery-slider", {
        slidesPerView: 2.2,
        loop: true,
        autoplay: true,
        centeredSlides: true,
        spaceBetween: 15,
        breakpoints: {
            480: {
                slidesPerView: 3.4,
            },
            576: {
                slidesPerView: 4,
            },
            768: {
                slidesPerView: 5,
            },
            992: {
                spaceBetween: 20,
                slidesPerView: 5.5,
            },
            1680: {
                spaceBetween: 26,
                slidesPerView: 5.5,
            },
            1700: {
                spaceBetween: 30,
                slidesPerView: 5.5,
            }
        }
    });

    // product page price filter
    var priceFilterSlider = document.getElementById('ul-products-price-filter-slider');

    if (priceFilterSlider) {
        noUiSlider.create(priceFilterSlider, {
            start: [20, 80],
            connect: true,
            range: {
                'min': 0,
                'max': 100
            }
        });
    }

    // product details slider
    new Swiper(".ul-product-details-img-slider", {
        slidesPerView: 1,
        loop: true,
        autoplay: true,
        spaceBetween: 0,
        navigation: {
            nextEl: "#ul-product-details-img-slider-nav .next",
            prevEl: "#ul-product-details-img-slider-nav .prev",
        },
    });

    // search category
    if (document.querySelector("#ul-checkout-country")) {
        new SlimSelect({
            select: '#ul-checkout-country',
            settings: {
                showSearch: false,
                contentLocation: document.querySelector('.ul-checkout-country-wrapper')
            }
        })
    }

    // sidebar products slider
    new Swiper(".ul-sidebar-products-slider", {
        slidesPerView: 1,
        loop: true,
        autoplay: true,
        spaceBetween: 30,
        navigation: {
            nextEl: ".ul-sidebar-products-slider-nav .next",
            prevEl: ".ul-sidebar-products-slider-nav .prev",
        },
        breakpoints: {
            1400: {
                slidesPerView: 2,
            }
        }
    });


    // quantity field
    if (document.querySelector(".ul-product-quantity-wrapper")) {
        const quantityWrapper = document.querySelectorAll(".ul-product-quantity-wrapper");

        quantityWrapper.forEach((item) => {
            const quantityInput = item.querySelector(".ul-product-quantity");
            const quantityIncreaseButton = item.querySelector(".quantityIncreaseButton");
            const quantityDecreaseButton = item.querySelector(".quantityDecreaseButton");

            quantityIncreaseButton.addEventListener("click", function () {
                quantityInput.value = parseInt(quantityInput.value) + 1;
            });
            quantityDecreaseButton.addEventListener("click", function () {
                if (quantityInput.value > 1) {
                    quantityInput.value = parseInt(quantityInput.value) - 1;
                }
            });
        })
    }

    // parallax effect
    const parallaxImage = document.querySelector(".ul-video-cover");

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                window.addEventListener("scroll", parallaxEffect);
                parallaxEffect(); // Initialize position
            } else {
                window.removeEventListener("scroll", parallaxEffect);
            }
        });
    });

    if (parallaxImage) {
        observer.observe(parallaxImage);
    }

    function getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        if (!cookieValue) {
            const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (tokenInput) cookieValue = tokenInput.value;
        }
        return cookieValue || '';
    }

    function updateBadges(cartCount, wishlistCount) {
        if (cartCount !== undefined) {
            document.querySelectorAll('.cart-badge').forEach(b => {
                b.textContent = cartCount;
                b.style.display = cartCount > 0 ? 'inline-block' : 'none';
            });
        }
        if (wishlistCount !== undefined) {
            document.querySelectorAll('.wishlist-badge').forEach(b => {
                b.textContent = wishlistCount;
                b.style.display = wishlistCount > 0 ? 'inline-block' : 'none';
            });
        }
    }

    // Global delegation for product card buttons
    document.addEventListener('click', function (e) {
        // Find add to cart button
        let cartBtn = e.target.closest('.btn-card-add-cart');
        if (!cartBtn && e.target.closest('.ul-product-actions')) {
            const btn = e.target.closest('button');
            if (btn && btn.querySelector('.flaticon-shopping-bag')) {
                cartBtn = btn;
            }
        }

        if (cartBtn) {
            e.preventDefault();
            e.stopPropagation();
            const pid = cartBtn.getAttribute('data-id') || cartBtn.closest('.ul-product')?.querySelector('[data-id]')?.getAttribute('data-id');
            if (!pid) return;

            const originalHtml = cartBtn.innerHTML;
            cartBtn.disabled = true;
            cartBtn.innerHTML = '<i class="flaticon-sparkle"></i>';

            const formData = new FormData();
            formData.append('productId', pid);
            formData.append('quantity', 1);

            const token = getCsrfToken();
            const headers = {};
            if (token) headers['X-CSRFToken'] = token;

            fetch('/add-to-cart/', {
                method: 'POST',
                headers: headers,
                body: formData
            })
            .then(async r => {
                const data = await r.json().catch(() => null);
                if (r.ok && data && data.status === 'success') {
                    updateBadges(data.cart_count, undefined);
                    const cleanTitle = (data.message || '').replace(/ added to cart successfully!/i, '').replace(/\"/g, '');
                    if (typeof showCartToast === 'function') {
                        showCartToast(cleanTitle || 'Product');
                    }
                    cartBtn.style.background = '#28a745';
                    cartBtn.style.color = '#ffffff';
                    setTimeout(() => {
                        cartBtn.disabled = false;
                        cartBtn.innerHTML = originalHtml;
                        cartBtn.style.background = '';
                        cartBtn.style.color = '';
                    }, 1500);
                } else {
                    cartBtn.disabled = false;
                    cartBtn.innerHTML = originalHtml;
                }
            })
            .catch(() => {
                cartBtn.disabled = false;
                cartBtn.innerHTML = originalHtml;
            });
            return;
        }

        // Find wishlist button
        let wishBtn = e.target.closest('.btn-card-add-wishlist');
        if (!wishBtn && e.target.closest('.ul-product-actions')) {
            const btn = e.target.closest('button');
            if (btn && btn.querySelector('.flaticon-heart')) {
                wishBtn = btn;
            }
        }

        if (wishBtn) {
            e.preventDefault();
            e.stopPropagation();
            const pid = wishBtn.getAttribute('data-id') || wishBtn.closest('.ul-product')?.querySelector('[data-id]')?.getAttribute('data-id');
            if (!pid) return;

            const originalHtml = wishBtn.innerHTML;
            wishBtn.disabled = true;

            const formData = new FormData();
            formData.append('productId', pid);

            const token = getCsrfToken();
            const headers = {};
            if (token) headers['X-CSRFToken'] = token;

            fetch('/add-to-wishlist/', {
                method: 'POST',
                headers: headers,
                body: formData
            })
            .then(async r => {
                const data = await r.json().catch(() => null);
                if (r.ok && data && data.status === 'success') {
                    updateBadges(undefined, data.wishlist_count);
                    wishBtn.style.background = '#e91e63';
                    wishBtn.style.color = '#ffffff';
                    setTimeout(() => {
                        wishBtn.disabled = false;
                        wishBtn.innerHTML = originalHtml;
                        wishBtn.style.background = '';
                        wishBtn.style.color = '';
                    }, 1500);
                } else {
                    wishBtn.disabled = false;
                    wishBtn.innerHTML = originalHtml;
                }
            })
            .catch(() => {
                wishBtn.disabled = false;
                wishBtn.innerHTML = originalHtml;
            });
            return;
        }
    });

});