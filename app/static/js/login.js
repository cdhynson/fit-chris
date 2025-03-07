document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const errorMessage = document.getElementById("error-message");

    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        const formData = new FormData(loginForm);
        try {
            const response = await fetch("/login", {
                method: "POST",
                body: formData,
            });

            const data = await response.json(); // Parse JSON response

            if (!response.ok) {
                // Display error popup message
                showPopup(data.error || "Invalid username or password.");
                return;
            }

            // Successful login: Redirect the user
            window.location.href = data.redirect;
        } catch (error) {
            console.error("Login request failed", error);
            showPopup("Something went wrong. Please try again.");
        }
    });

    // Function to show an error popup message
    function showPopup(message) {
        errorMessage.textContent = message; // Set message text
        errorMessage.style.display = "block"; // Show error message
        errorMessage.classList.add("error-popup"); // Add popup style class

        // Hide after 3 seconds
        setTimeout(() => {
            errorMessage.style.display = "none";
        }, 3000);
    }
});