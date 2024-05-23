document.addEventListener('DOMContentLoaded', function () {
  var deployEnvField = document.querySelector('input[name="deployenv"]');
  var sshPortDevField = document.querySelector('input[name="sshportdev"]');
  var pvtDeployServersDevField = document.querySelector('input[name="pvtdeployserversdev"]');
  var deployServersDevField = document.querySelector('input[name="deployserversdev"]');
  var deployEnvDevField = document.querySelector('input[name="deployenvdev"]');
  var sshPortProdField = document.querySelector('input[name="sshportprod"]');
  var pvtDeployServersProdField = document.querySelector('input[name="pvtdeployserversprod"]');
  var deployServersProdField = document.querySelector('input[name="deployserversprod"]');
  var deployEnvProdField = document.querySelector('input[name="deployenvprod"]');

  var allFields = document.querySelectorAll('.mandatory-fields');

  // Function to add the star mark (*) to required fields
  function addStarMarkToRequiredFields(fields) {
    fields.forEach(function (fieldName) {
      var field = document.querySelector(`input[name="${fieldName}"]`);
      if (field.classList.contains('mandatory-fields')) {
        var label = field.closest('.mb-3').querySelector('label');
        label.innerHTML = label.innerHTML + ' <span class="text-danger">*</span>';
      }
    });
  }

  // Event listener to update required fields based on the value of deployEnvField
  deployEnvField.addEventListener('input', function () {
    if ((!deployEnvField.value.includes('dev') && deployEnvField.value.includes('prod')) || (deployEnvField.value.includes('dev') && deployEnvField.value.includes('prod'))) {
      // Add star mark to required fields for dev and prod environment combination
      addStarMarkToRequiredFields(['sshportdev', 'pvtdeployserversdev', 'deployserversdev', 'deployenvdev', 'sshportprod', 'pvtdeployserversprod', 'deployserversprod', 'deployenvprod']);
      allFields.forEach(function (field) {
        field.required = true;
      });

    } else if (deployEnvField.value === 'dev') {
      // Add star mark to required fields for dev environment
      addStarMarkToRequiredFields(['sshportdev', 'pvtdeployserversdev', 'deployserversdev', 'deployenvdev']);
      allFields.forEach(function (field) {
        field.required = false;
      });
      sshPortDevField.required = true;
      pvtDeployServersDevField.required = true;
      deployServersDevField.required = true;
      deployEnvDevField.required = true;
    } else {
      // Remove required fields and star marks for other cases
      allFields.forEach(function (field) {
        field.required = false;
      });
    }
  });
});
$(document).ready(function () {
  // Get the initial value of the username and repo_url fields
  var initialUsername = $('#username').val();

  // Whenever the username or repo_url field changes
  $('#username').on('input', function () {
    // Get the new value of the username and repo_url fields
    var newUsername = $('#username').val();

    // Update the value of the hidden input field for old_username and old_repo_url
    $('#old_username').val(initialUsername);
    $('#new_username').val(newUsername);

    // Update the initialUsername and initialRepoUrl variables with the new values
    initialUsername = newUsername;
  });
});
$(document).ready(function () {
// Get the initial value of the repo_url field
var initialRepoUrl = $('#repourl').val();

// Whenever the repo_url field changes
$('#repourl').on('input', function () {
  // Get the new value of the repo_url field
  var newRepoUrl = $(this).val();

  // Update the value of the hidden input field for old_repo_url and new_repo_url
  $('#old_repourl').val(initialRepoUrl);
  $('#new_repourl').val(newRepoUrl);

  // Update the initialRepoUrl variable with the new value
  initialRepoUrl = newRepoUrl;
});
});

