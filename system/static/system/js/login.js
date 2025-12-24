document.addEventListener('DOMContentLoaded', function(){
  var btn = document.getElementById('togglePwd');
  var input = document.getElementById('password');
  if (btn && input) {
    btn.addEventListener('click', function(){
      var isPwd = input.type === 'password';
      input.type = isPwd ? 'text' : 'password';
      btn.textContent = isPwd ? 'Hide' : 'Show';
    });
  }
});
