document.addEventListener("DOMContentLoaded", function () {
  const sendOtpBtn = document.getElementById("sendOtpBtn");
  const verifyOtpBtn = document.getElementById("verifyOtpBtn");
  const otpRequestForm = document.getElementById("otpRequestForm");
  const otpVerifyForm = document.getElementById("otpVerifyForm");
  const emailInput = document.getElementById("email");
  const otpInput = document.getElementById("otp");
  const otpError = document.getElementById("otpError");

  // Backend API Base URL
  const API_BASE_URL = "http://127.0.0.1:5000";

  // Add these validation functions
  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isValidOTP = (otp) => /^\d{6}$/.test(otp);

  // Modified Send OTP handler
  sendOtpBtn.addEventListener("click", async function () {
    const email = emailInput.value.trim();
  
    if (!isValidEmail(email)) {
      alert("Please enter a valid email address (e.g., user@example.com)");
      return;
    }
  
    // Show loading spinner
    sendOtpBtn.classList.add("loading");
  
    try {
      const response = await fetch(`/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
  
      const data = await response.json();
  
      if (!response.ok) {
        throw new Error(data.error || "Failed to send OTP");
      }
  
      // Your existing UI updates
      showToast(data.message, "success");
      otpRequestForm.style.display = "none";
      otpVerifyForm.style.display = "block";
      otpInput.focus();
    } catch (error) {
      showToast("Something went wrong!", "danger");
      console.error("Error:", error);
      alert(error.message);
    } finally {
      // Remove loading spinner no matter what happens
      sendOtpBtn.classList.remove("loading");
    }
  });
  
  // Modified Verify OTP handler
  verifyOtpBtn.addEventListener("click", async function () {
    const email = emailInput.value.trim();
    const otp = otpInput.value.trim();

    // Validate OTP
    if (!/^\d{6}$/.test(otp)) {
        otpError.textContent = "Please enter a 6-digit numeric OTP";
        otpError.style.display = "block";
        return;
    }

    try {
        const response = await fetch("/verify_otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp }),
        });

        // Check if the response is JSON
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error("Invalid response from server");
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "OTP verification failed");
        }

        // Redirect to report issue page with userID and email as query parameters
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            throw new Error(data.message || "Verification failed");
        }

    } catch (error) {
        console.error("Error verifying OTP:", error);
        otpError.textContent = error.message;
        otpError.style.display = "block";
        otpInput.value = ""; // Clear OTP input field
        otpInput.focus(); // Focus on OTP input field
    }
  });
});


// Toast message function

function showToast(message, type = "success") {
  const toastEl = document.getElementById("toastMessage");
  const toastBody = document.getElementById("toastBody");

  toastBody.textContent = message;
  toastEl.className = `toast align-items-center text-white bg-${type} border-0`;

  const toast = new bootstrap.Toast(toastEl,{delay:3000});
  toast.show();
}


window.history.pushState(null, "", window.location.href);  
window.onpopstate = function () {  
  window.history.pushState(null, "", window.location.href);  
};