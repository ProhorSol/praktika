// Функция для воспроизведения звука уведомления
function playNotification() {
    const audio = document.getElementById('notificationSound');
    if (audio) {
        audio.play();
    }
}

// Функция для предварительного просмотра изображений
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
}

// Валидация формы регистрации
function validateRegistrationForm(form) {
    const username = form.username.value;
    const email = form.email.value;
    const password = form.password.value;
    const confirmPassword = form.confirmPassword.value;
    
    if (username.length < 3) {
        alert('Имя пользователя должно содержать не менее 3 символов');
        return false;
    }
    
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        alert('Введите корректный email адрес');
        return false;
    }
    
    if (password.length < 6) {
        alert('Пароль должен содержать не менее 6 символов');
        return false;
    }
    
    if (password !== confirmPassword) {
        alert('Пароли не совпадают');
        return false;
    }
    
    return true;
}

// Подтверждение удаления
function confirmDelete(message) {
    return confirm(message || 'Вы уверены, что хотите удалить этот элемент?');
}

// Анимация слайдера на главной странице
function initializeSlider() {
    const slides = document.querySelectorAll('.slide');
    let currentSlide = 0;
    
    function showSlide(index) {
        slides.forEach(slide => slide.classList.remove('active'));
        slides[index].classList.add('active');
    }
    
    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }
    
    if (slides.length > 0) {
        showSlide(0);
        setInterval(nextSlide, 5000);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeSlider();
    
    // Обработчики событий для форм
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(e) {
            if (!validateRegistrationForm(this)) {
                e.preventDefault();
            }
        });
    }
    
    // Обработчики для предпросмотра изображений
    const imageInputs = document.querySelectorAll('.image-input');
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            previewImage(this, this.dataset.previewId);
        });
    });
});
