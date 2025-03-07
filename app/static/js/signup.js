document.addEventListener("DOMContentLoaded", function () {
    const signupForm = document.getElementById("signup-form");
    const errorMessage = document.getElementById("error-message");
    const usernameInput = document.getElementById("username");
    const usernameCheck = document.getElementById("username-check");
    const passwordInput = document.getElementById("password");
    const submitButton = signupForm.querySelector("button[type='submit']");

    const lengthCheck = document.getElementById("length");
    const uppercaseCheck = document.getElementById("uppercase");
    const numberCheck = document.getElementById("number");
    const specialCheck = document.getElementById("special");
    const spaceCheck = document.getElementById("space");

    signupForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(signupForm);

        try {
            const response = await fetch("/signup", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                errorMessage.textContent = data.error || "Signup failed.";
                errorMessage.style.display = "block";
                return;
            }

            window.location.href = data.redirect;
        } catch (error) {
            console.error("Signup request failed", error);
            errorMessage.textContent = "Something went wrong. Please try again.";
            errorMessage.style.display = "block";
        }
    });

    usernameInput.addEventListener("input", async function () {
        const username = usernameInput.value.trim();

        if (username.length < 3) {
            usernameCheck.innerHTML = "❌ Username must be at least 3 characters.";
            usernameCheck.classList.add("invalid");
            usernameCheck.classList.remove("valid");
            submitButton.disabled = true;
            return;
        }

        try {
            const response = await fetch(`/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json();

            if (data.exists) {
                usernameCheck.innerHTML = "❌ Username already taken.";
                usernameCheck.classList.add("invalid");
                usernameCheck.classList.remove("valid");
                submitButton.disabled = true;
            } else {
                usernameCheck.innerHTML = "✅ Username is available!";
                usernameCheck.classList.add("valid");
                usernameCheck.classList.remove("invalid");
                submitButton.disabled = false;
            }
        } catch (error) {
            console.error("Error checking username availability:", error);
            usernameCheck.innerHTML = "⚠️ Error checking username.";
            usernameCheck.classList.add("invalid");
            usernameCheck.classList.remove("valid");
            submitButton.disabled = true;
        }
    });

    passwordInput.addEventListener("input", function () {
        const password = passwordInput.value;
        updatePasswordValidation(password);
    });

    function updatePasswordValidation(password) {
        let isValid = true;

        if (password.length >= 6) {
            lengthCheck.innerHTML = "✅ At least 6 characters";
            lengthCheck.classList.add("valid");
            lengthCheck.classList.remove("invalid");
        } else {
            lengthCheck.innerHTML = "❌ At least 6 characters";
            lengthCheck.classList.add("invalid");
            lengthCheck.classList.remove("valid");
            isValid = false;
        }

        if (/[A-Z]/.test(password)) {
            uppercaseCheck.innerHTML = "✅ At least 1 capital letter";
            uppercaseCheck.classList.add("valid");
            uppercaseCheck.classList.remove("invalid");
        } else {
            uppercaseCheck.innerHTML = "❌ At least 1 capital letter";
            uppercaseCheck.classList.add("invalid");
            uppercaseCheck.classList.remove("valid");
            isValid = false;
        }

        if (/\d/.test(password)) {
            numberCheck.innerHTML = "✅ At least 1 number";
            numberCheck.classList.add("valid");
            numberCheck.classList.remove("invalid");
        } else {
            numberCheck.innerHTML = "❌ At least 1 number";
            numberCheck.classList.add("invalid");
            numberCheck.classList.remove("valid");
            isValid = false;
        }

        if (!/[!@#$%^&*]/.test(password)) {
            specialCheck.innerHTML = "✅ No special characters (!@#$%^&*)";
            specialCheck.classList.add("valid");
            specialCheck.classList.remove("invalid");
        } else {
            specialCheck.innerHTML = "❌ No special characters (!@#$%^&*)";
            specialCheck.classList.add("invalid");
            specialCheck.classList.remove("valid");
            isValid = false;
        }

        if (/ /.test(password)) { 
            spaceCheck.innerHTML = "❌ No spaces allowed";
            spaceCheck.classList.add("invalid");
            spaceCheck.classList.remove("valid");
            isValid = false;
        } else {
            spaceCheck.innerHTML = "✅ No spaces";
            spaceCheck.classList.add("valid");
            spaceCheck.classList.remove("invalid");
        }

        submitButton.disabled = !isValid;
    }
});
