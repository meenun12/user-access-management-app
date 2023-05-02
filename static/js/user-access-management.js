$(document).ready(function() {
  // Autocomplete feature for email input box
  $('#email-input').on('input', function() {
    var search_term = $(this).val();
    if (search_term.length >= 2) {
      $.ajax({
        url: '/autocomplete',
        method: 'POST',
        data: { search_term: search_term },
        success: function(data) {
          var email_list = '<ul>';
          $.each(data, function(index, obj) {
            email_list += '<li id=' + obj.id + '>' + obj.email + '</li>';
          });
          email_list += '</ul>';
          $('#email-results').html(email_list);
          $('#email-results li').on('click', function() {
            var emp_id = $(this).attr('id');
            $('#email-input').val($(this).text())
            get_existing_team_ids(emp_id);
            $('#email-results').empty();
          });

        }
      });
    } else {
      $('#email-results').empty();
    }
  });

  $('#teams-field').on('change', function() {

            var team_id = $(this).val();
            $.ajax({
                url: '/get_assigned_employees',
                method: 'POST',
                data: { team_id: team_id },
                success: function(employees) {
                   emps_list = '';
                   $.each(employees, function(index, emp) {
                        emps_list += '<li>';
                        emps_list += '<input class="form-check-input" id="emps-field-' + emp.id + '" name="employees" type="checkbox" value="' + emp.id + '" checked>';
                        emps_list += '<label for="emps-field-' +  emp.id + '">' + emp.email + '</label>';
                        emps_list += '</li>';
                      });

                   $("#emps-field").html(emps_list);
                  }

                  });
              });


});

function get_existing_team_ids(emp_id) {
  $.ajax({
    url: '/get_existing_team_ids',
    method: 'POST',
    data: { emp_id: emp_id },
    success: function(team_ids) {
      $.each(team_ids, function(index, value) {
        $("#teams-field").val(value);
      });
    }
  });
  $('#email-results').empty();
}