document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent form submission

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email: email, password: password }),
        });

        const text = await response.text();
        if (!text) {
            throw new Error("Empty response from server");
        }

        const result = JSON.parse(text);

        if (response.ok) {
            alert(result.message); // Show success message
            window.location.href = "/dashboard"; // Redirect on success
        } else {
            alert(result.error); // Show error message
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
});