(function($) {
  $.fn.serializeFiles = function() {
    var form = $(this);
    var formData = new FormData();
    var formParams = form.serializeArray();

    $.each(form.find('input[type="file"]'), function(i, tag) {
      $.each($(tag)[0].files, function(i, file) {
        formData.append(tag.name, file);
      });
    });

    $.each(formParams, function(i, val) {
      formData.append(val.name, val.value);
    });

    return formData;
  };
})(jQuery);


function initAppointmentForm() {
  var mountpoints = document.querySelectorAll('[data-appointment-form-mount-point]');

  for (var i = 0; i < mountpoints.length; i++) {
    var notaryId = mountpoints[i].getAttribute('data-appointment-form-mount-point');

    new Vue({
      render: function render(createElement) {
        return createElement(AppointmentForm.AppointmentForm, {
          props: {
            // federal number
            notaryId: notaryId,
            // build in during deploy
            // apiBaseUrl: 'http://127.0.0.1:8001/api/v1',
            privacyPolicyLink: `{% url 'fnc:personal' %}`,
            termsOfUseLink: `{% url 'fnc:terms-conditions' %}`,
          },
        });
      },
    }).$mount(mountpoints[i]);
  }
}


(function() {
  $('input[name="fio"]').on("change keyup paste", function(){
    if (this.value.length > 1 && /^([ A-zА-яЁё(),.-])+$/.test(this.value)) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });
  $('input[name="email"]').on("change keyup paste", function(){
    if (this.value.length > 1) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });

  // init appointment form widget
  initAppointmentForm();


  $.datepicker.setDefaults( $.datepicker.regional[ "ru" ] );
  $('.notary__form--datepicker').datepicker({
    showButtonPanel: true,
    minDate: 0
  });

/* Слегка измененный матчер: всегда показываем пункт Прочее */
function matcher (params, data) {
      // Always return the object if there is nothing to compare
      if ($.trim(params.term) === '' || data.text === 'Прочее') {
        return data;
      }

      // Do a recursive check for options with children
      if (data.children && data.children.length > 0) {
        // Clone the data object if there are children
        // This is required as we modify the object to remove any non-matches
        var match = $.extend(true, {}, data);

        // Check each child of the option
        for (var c = data.children.length - 1; c >= 0; c--) {
          var child = data.children[c];

          var matches = matcher(params, child);

          // If there wasn't a match, remove the object in the array
          if (matches == null) {
            match.children.splice(c, 1);
          }
        }

        // If any children matched, return the new object
        if (match.children.length > 0) {
          return match;
        }

        // If there were no matching children, check just the plain object
        return matcher(params, match);
      }

      var original = data.text.toUpperCase();
      var term = params.term.toUpperCase();

      // Check if the text contains the term
      if (original.indexOf(term) > -1) {
        return data;
      }

      // If it doesn't contain the term, don't return anything
      return null;
    }

  var select = $('select[data-model="service"]');
  select.select2({
    language: 'ru',
    // https://select2.org/placeholders
    placeholder: 'Цель обращения',
    allowClear: true, // hacked via css -- hide `x` button
    matcher: matcher,
  });

  select.on('change', function(){
    console.log('select', this.value);
    $('input[name="service"]').val(this.value);
    if (this.value.length > 1) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });

  $('input[name="date"]').on("change keyup paste", function(){
    if (this.value.length > 1) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });
  $('textarea[name="text"]').on("change keyup paste", function() {
    if (this.value.length > 1) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });
  $('input[name="phone"]').on("change keyup paste", function() {
    if (this.value && this.value.length > 1) {
      $(this).removeClass('error')
    } else {
      $(this).addClass('error')
    }
  });
  $('.notary__form-content input[name="terms_agreement"]').on("change keyup paste", function(){
    $('.notary__form--label-checkbox').removeClass('error')
  });
  $('.feedback-form input[name="terms_agreement"]').change(function() {
    $('.notary__form--label-checkbox').removeClass('error')
  });
})();

function removeError() {
  $('.notary__form-content input').removeClass('error')
  $('.feedback-form input').removeClass('error')
  $('.feedback-form textarea').removeClass('error')
  $('.notary__form--label-checkbox').removeClass('error')
}

/* Appointment form */

function appointmentSuccess(respData, textStatus){
  if (respData === "ok") {
    $('.notary__form-content').addClass('hide')
    $('.notary__form .notary__form-content-success').removeClass('hide')
    removeError()
  }
}

function appointmentError(xhr, status, error){
  var container = $('.notary__form')
  $('.notary__form-content').addClass('hide')
  if (xhr.status == 429) {
    container.find('.notary__form-content-error .notary__form-content-before--title').text('Слишком много запровов')
    container.find('.notary__form-content-error .notary__form-content-before--label').text('Подождите 5 минут')
  }
  else {
    container.find('.notary__form-content-error .notary__form-content-before--title').text('Что-то пошло не так')
    container.find('.notary__form-content-error .notary__form-content-before--label').text('Попробуйте отправить заявку еще раз')
  }
  container.find('.notary__form-content-error').removeClass('hide')

  console.log(xhr)
  console.log(error)
  console.log(status)
}

function appointmentValidation(data) {

  var isValid = true
  if (!data.get('phone') || data.get('phone').length < 10) {
    $('.notary__form-content input[name="phone"]').addClass('error')
    isValid = false
  }

  var date = data.get('date');
  var timeslot = data.get('timeslot');
  if (!date && !timeslot) {
    $('.notary__form-content input[name="date"]').addClass('error');
    $('.notary__form-content .slot-picker').addClass('error');
    isValid = false;
  }
  if (date){
    data['date'] = data['date'] + 'T23:59';
  }

  if (!data.get('fio') || !/^([ A-zА-яЁё(),.-])+$/.test(data.get('fio'))) {
    $('.notary__form-content input[name="fio"]').addClass('error')
    isValid = false
  }
  if (!data.get('email')) {
    $('.notary__form-content input[name="email"]').addClass('error')
    isValid = false
  }
  if (!data.get('terms_agreement')) {
    $('.notary__form--label-checkbox').addClass('error')
    isValid = false
  }
  if (!data.get('service')) {
    $('.notary__form--field-actions').addClass('error')
    isValid = false
  }

  if (isValid) {
    $.ajax({
      type: "POST",
      url: $('form.appointment-form').attr('action'),
      data: data,
      cache: false,
      processData: false,
      contentType: false,
      success: appointmentSuccess,
      error: appointmentError
    });
  }
}

$('form.appointment-form').submit(function (e) {
  e.preventDefault();
  var data = $(this).serializeFiles();

  appointmentValidation(data);
});

/* Feedback form */

function feedbackSuccess(respData, textStatus){
  console.log(textStatus)
  console.log(respData)
  if (respData === "ok") {
    removeError()
    $('.feedback-form').addClass('hide')
    $('.feedback-form .notary__form-content-success').removeClass('hide')
  }
}

function feedbackError(xhr, status, error){
  var form = $('.feedback-form')
  form.addClass('hide')
  if (xhr.status == 429) {
    form.find('.notary__form-content-error .notary__form-content-before--title').text('Слишком много запровов')
    form.find('.notary__form-content-error .notary__form-content-before--label').text('Подождите 5 минут')
  }
  else {
    form.find('.notary__form-content-error .notary__form-content-before--title').text('Что-то пошло не так')
    form.find('.notary__form-content-error .notary__form-content-before--label').text('Попробуйте отправить заявку еще раз')
  }
  $('.notary__form-content-error').removeClass('hide')
  console.log(xhr)
  console.log(error)
  console.log(status)
}

function feedbackValidation(data) {
  var isValid = true
  if (!data.get('phone')) {
    $('.feedback-form input[name="phone"]').addClass('error')
    isValid = false
  }
  if (!data.get('fio')) {
    $('.feedback-form input[name="fio"]').addClass('error')
    isValid = false
  }
  if (!data.get('email')) {
    $('.feedback-form input[name="email"]').addClass('error')
    isValid = false
  }
  if (!data.get('text')) {
    $('.feedback-form textarea[name="text"]').addClass('error')
    isValid = false
  }
  if (!data.get('terms_agreement')) {
    $('.notary__form--label-checkbox').addClass('error')
    isValid = false
  }

  if (isValid) {
    $.ajax({
      type: "POST",
      url: $('form.feedback-form').attr('action'),
      data: data,
      cache: false,
      processData: false,
      contentType: false,
      success: feedbackSuccess,
      error: feedbackError
    });
  }
}


$('form.feedback-form').submit(function (e) {
  e.preventDefault();
  var formData = $(this).serializeFiles();
  feedbackValidation(formData);
});
