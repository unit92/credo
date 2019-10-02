document.addEventListener(
  "DOMContentLoaded",
  () => {
    const validatePassword = () => {
      if (password.value !== confirm_password.value) {
        confirm_password.classList.remove("valid");
        confirm_password.classList.add("invalid");
        password.classList.remove("valid");
        password.classList.add("invalid");

      } else {
        confirm_password.classList.remove("invalid");
        confirm_password.classList.add("valid");
        password.classList.remove("invalid");
        password.classList.add("valid");
      }
    };

    const password = document.getElementById("password");
    const confirm_password = document.getElementById("confirm-password");

    password.onkeyup = validatePassword;
    confirm_password.onkeyup = validatePassword;
  },
  false
);
