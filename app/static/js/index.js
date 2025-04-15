/**
 * Index page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Testimonial slider functionality
    const slider = document.querySelector('.testimonial-slider');
    const dots = document.querySelectorAll('.dot');
    
    // Set active dot based on current slide
    function setActiveDot(index) {
        dots.forEach(dot => dot.classList.remove('active'));
        dots[index].classList.add('active');
    }
    
    // Initialize slider position
    let currentSlide = 0;
    
    // Add click event to dots
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            currentSlide = index;
            slider.scrollTo({
                left: index * slider.offsetWidth,
                behavior: 'smooth'
            });
            setActiveDot(index);
        });
    });
    
    // Auto-slide functionality
    setInterval(() => {
        currentSlide = (currentSlide + 1) % dots.length;
        slider.scrollTo({
            left: currentSlide * slider.offsetWidth,
            behavior: 'smooth'
        });
        setActiveDot(currentSlide);
    }, 5000);
}); 