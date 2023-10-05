document.addEventListener("DOMContentLoaded", () => {
const passwordInputs = document.querySelectorAll(".password");
const showHideButtons = document.querySelectorAll(".showHidePw");

// Show or hide password
showHideButtons.forEach(button => {
    button.addEventListener("click", () => {
    const inputField = button.parentElement.querySelector(".password");
    if (inputField.type === "password") {
        inputField.type = "text";
        button.classList.replace("uil-eye-slash", "uil-eye");
    } else {
        inputField.type = "password";
        button.classList.replace("uil-eye", "uil-eye-slash");
    }
    });
});
});

document.addEventListener("DOMContentLoaded", function () {
    var errorMessage = document.getElementById("error-message");

    if (errorMessage) {
        errorMessage.style.display = "block";
        setTimeout(function () {
            errorMessage.style.display = "none"; 
        }, 5000); 
    }
});