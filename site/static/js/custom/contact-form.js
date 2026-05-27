(function () {
    'use strict';

    // ============================================================
    // Конфиг Google Form
    // ============================================================
    // 1. Создай Google Form с полями: Имя, Телефон, Email, Цель обращения, Сообщение.
    // 2. Открой форму в режиме редактирования, нажми ⋮ (три точки сверху) → "Получить ссылку для предзаполнения".
    // 3. Заполни все поля любыми тестовыми значениями, нажми "Получить ссылку".
    // 4. В полученной ссылке найди ID формы (формат: 1FAIpQLSe...) и ID каждого поля (формат: entry.123456789).
    // 5. Подставь значения ниже.
    // ============================================================
    var GOOGLE_FORM_ID = 'PASTE_FORM_ID_HERE';
    var FIELDS = {
        name: 'entry.PASTE_NAME_ID',
        phone: 'entry.PASTE_PHONE_ID',
        email: 'entry.PASTE_EMAIL_ID',
        purpose: 'entry.PASTE_PURPOSE_ID',
        message: 'entry.PASTE_MESSAGE_ID'
    };

    function getFormUrl() {
        return 'https://docs.google.com/forms/d/e/' + GOOGLE_FORM_ID + '/formResponse';
    }

    function isConfigured() {
        if (GOOGLE_FORM_ID.indexOf('PASTE_') !== -1) return false;
        for (var key in FIELDS) {
            if (FIELDS[key].indexOf('PASTE_') !== -1) return false;
        }
        return true;
    }

    function showStatus(form, kind, text) {
        var statusEl = form.querySelector('.contact-form__status');
        statusEl.className = 'contact-form__status contact-form__status--' + kind;
        statusEl.textContent = text;
    }

    function setSubmitting(form, submitting) {
        var btn = form.querySelector('.contact-form__submit');
        btn.disabled = submitting;
        btn.textContent = submitting ? 'Отправка...' : 'Отправить';
    }

    function validate(values) {
        if (!values.name || values.name.length < 2) return 'Укажите имя';
        if (!values.phone || values.phone.replace(/\D/g, '').length < 10) return 'Укажите корректный телефон';
        if (!values.purpose) return 'Выберите цель обращения';
        if (!values.message || values.message.length < 3) return 'Опишите ваш вопрос';
        if (values.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) return 'Некорректный email';
        return null;
    }

    function submitToGoogleForm(values) {
        var formData = new FormData();
        formData.append(FIELDS.name, values.name);
        formData.append(FIELDS.phone, values.phone);
        formData.append(FIELDS.email, values.email || '');
        formData.append(FIELDS.purpose, values.purpose);
        formData.append(FIELDS.message, values.message);

        return fetch(getFormUrl(), {
            method: 'POST',
            mode: 'no-cors',
            body: formData
        });
    }

    function handleSubmit(event) {
        event.preventDefault();
        var form = event.target;

        var values = {
            name: form.querySelector('[name="name"]').value.trim(),
            phone: form.querySelector('[name="phone"]').value.trim(),
            email: form.querySelector('[name="email"]').value.trim(),
            purpose: form.querySelector('[name="purpose"]').value,
            message: form.querySelector('[name="message"]').value.trim()
        };

        var error = validate(values);
        if (error) {
            showStatus(form, 'error', error);
            return;
        }

        if (!isConfigured()) {
            showStatus(form, 'error', 'Форма ещё не настроена: укажите GOOGLE_FORM_ID и entry.XXX в static/js/custom/contact-form.js');
            console.warn('Contact form is not configured. See static/js/custom/contact-form.js');
            return;
        }

        setSubmitting(form, true);

        submitToGoogleForm(values)
            .then(function () {
                showStatus(form, 'success', 'Спасибо! Ваш запрос отправлен. Мы свяжемся с вами в ближайшее время.');
                form.reset();
            })
            .catch(function () {
                // mode: 'no-cors' возвращает opaque response — реальную ошибку видно только в Network.
                // Сообщаем мягко.
                showStatus(form, 'error', 'Не удалось отправить. Попробуйте ещё раз или позвоните по телефону.');
            })
            .finally(function () {
                setSubmitting(form, false);
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var form = document.querySelector('.contact-form');
        if (!form) return;
        form.addEventListener('submit', handleSubmit);
    });
})();
