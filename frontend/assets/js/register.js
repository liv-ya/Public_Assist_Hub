document.getElementById("registrationForm").addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent default form submission

    const formData = {
        username: document.getElementById("username").value.trim(),
        email: document.getElementById("email").value.trim(),
        number: document.getElementById("number").value.trim(),
        password: document.getElementById("password").value.trim()
    };

    console.log("Sending data:", formData); // Log the data being sent

    try {
        const response = await fetch("/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        console.log("Response status:", response.status); // Log response status
        const result = await response.json();
        console.log("Server Response:", result); // Log JSON response

        document.getElementById("responseMessage").innerText = result.message;

        if (response.ok) {
            document.getElementById("registrationForm").reset(); // Reset form on success
            setTimeout(() => {
                window.location.href = "/"; // Redirect after successful signup
            }, 2000);
        }
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("responseMessage").innerText = "Registration failed! Please try again.";
    }
});
