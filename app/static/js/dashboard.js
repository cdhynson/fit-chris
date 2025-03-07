document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.getElementById("logout-btn");

    logoutButton.addEventListener("click", async function (event) {
        event.preventDefault();

        try {
            const response = await fetch("/logout", { method: "POST" });

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                console.error("Logout failed");
            }
        } catch (error) {
            console.error("Error logging out:", error);
        }
    });
});

document.addEventListener("DOMContentLoaded", async function () {
    const greetingElement = document.getElementById("user-greeting");

    try {
        const response = await fetch("/user-info");
        if (response.ok) {
            const data = await response.json();
            greetingElement.innerHTML = `Hello <strong>${data.fullname}</strong>!`;
        } else {
            greetingElement.innerHTML = `Hello <strong>Guest</strong>!`;
        }
    } catch (error) {
        console.error("Error fetching user info:", error);
        greetingElement.innerHTML = `Hello <strong>Guest</strong>!`;
    }
});
