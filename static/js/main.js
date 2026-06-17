document.addEventListener("DOMContentLoaded", function () {
    if (typeof gsap !== "undefined") {
        gsap.from(".hero-title", {
            y: 60,
            opacity: 0,
            duration: 1,
            ease: "power3.out"
        });

        gsap.from(".hero p", {
            y: 40,
            opacity: 0,
            duration: 1,
            delay: 0.3,
            ease: "power3.out"
        });

        gsap.from(".hero-buttons", {
            y: 30,
            opacity: 0,
            duration: 0.8,
            delay: 0.6,
            ease: "power3.out"
        });

        gsap.from(".hero-info-card", {
            x: 60,
            opacity: 0,
            duration: 1,
            delay: 0.4,
            ease: "power3.out"
        });

        gsap.from(".stat-card", {
            scale: 0.9,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: "back.out(1.7)"
        });

        gsap.from(".bike-card", {
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: "power3.out"
        });
    }

    const tabButtons = document.querySelectorAll(".bike-tab-btn");
    const tabContents = document.querySelectorAll(".bike-tab-content");

    tabButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const targetTab = button.getAttribute("data-tab");

            tabButtons.forEach(function (btn) {
                btn.classList.remove("active");
            });

            tabContents.forEach(function (content) {
                content.classList.remove("active");
            });

            button.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            if (typeof gsap !== "undefined") {
                gsap.from("#" + targetTab + " .bike-card", {
                    y: 35,
                    opacity: 0,
                    duration: 0.5,
                    stagger: 0.1,
                    ease: "power3.out"
                });
            }
        });
    });

    const modal = document.getElementById("testimonialModal");
    const openModalBtn = document.getElementById("openTestimonialModal");
    const closeModalBtn = document.getElementById("closeTestimonialModal");

    if (openModalBtn && modal) {
        openModalBtn.addEventListener("click", function () {
            modal.classList.add("active");

            if (typeof gsap !== "undefined") {
                gsap.from(".testimonial-modal-card", {
                    scale: 0.8,
                    opacity: 0,
                    duration: 0.4,
                    ease: "back.out(1.7)"
                });
            }
        });
    }

    if (closeModalBtn && modal) {
        closeModalBtn.addEventListener("click", function () {
            modal.classList.remove("active");
        });
    }

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                modal.classList.remove("active");
            }
        });
    }

    const testimonialSlides = document.querySelectorAll(".testimonial-slide");
    const prevBtn = document.getElementById("prevTestimonial");
    const nextBtn = document.getElementById("nextTestimonial");

    let currentSlide = 0;

    function showSlide(index) {
        if (testimonialSlides.length === 0) {
            return;
        }

        testimonialSlides.forEach(function (slide) {
            slide.classList.remove("active");
        });

        if (index >= testimonialSlides.length) {
            currentSlide = 0;
        } else if (index < 0) {
            currentSlide = testimonialSlides.length - 1;
        } else {
            currentSlide = index;
        }

        testimonialSlides[currentSlide].classList.add("active");

        if (typeof gsap !== "undefined") {
            gsap.from(testimonialSlides[currentSlide], {
                x: 40,
                opacity: 0,
                duration: 0.5,
                ease: "power3.out"
            });
        }
    }

    if (testimonialSlides.length > 0) {
        showSlide(currentSlide);

        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                showSlide(currentSlide + 1);
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                showSlide(currentSlide - 1);
            });
        }

        setInterval(function () {
            showSlide(currentSlide + 1);
        }, 5000);
    }
});