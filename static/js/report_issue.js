// Example security improvements:
function previewImage(event) {
  const file = event.target.files[0];
  if (file && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = function () {
      const output = document.getElementById("preview");
      output.src = reader.result;
      output.style.display = "block";
      document.getElementById("viewImageBtn").style.display = "inline";
    };
    reader.readAsDataURL(file);
  } else {
    alert("Please upload a valid image file.");
  }
}

// function clearImagePreview() {
//   const output = document.getElementById("preview");
//   output.src = "";
//   output.style.display = "none";
//   document.getElementById("viewImageBtn").style.display = "none";
//   document.getElementById("issueImage").value = ""; // Clear the file input
// }

// function viewImage() {
//   const imgSrc = document.getElementById("preview").src;
//   if (imgSrc) {
//     window.open(imgSrc, "_blank");
//   }
// }

// Map and Location Autocomplete
let map, marker, autocomplete;

function initMap() {
  const defaultLocation = { lat: -34.397, lng: 150.644 };
  map = new google.maps.Map(document.getElementById("map"), {
    center: defaultLocation,
    zoom: 15,
  });

  marker = new google.maps.Marker({
    position: defaultLocation,
    map: map,
    title: "Selected Location",
  });

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        map.setCenter(userLocation);
        marker.setPosition(userLocation);
        getPlaceName(userLocation.lat, userLocation.lng);
      },
      () => {
        alert(
          "Geolocation permission denied or not supported. Using default location."
        );
        map.setCenter(defaultLocation);
        marker.setPosition(defaultLocation);
        getPlaceName(defaultLocation.lat, defaultLocation.lng);
      }
    );
  }

  autocomplete = new google.maps.places.Autocomplete(
    document.getElementById("issueLocation")
  );
  autocomplete.addListener("place_changed", function () {
    let place = autocomplete.getPlace();
    if (!place.geometry) {
      alert("No details available for the selected location.");
      return;
    }
    map.setCenter(place.geometry.location);
    marker.setPosition(place.geometry.location);
  });
}

function getPlaceName(lat, lng) {
  let geocoder = new google.maps.Geocoder();
  let latlng = { lat: parseFloat(lat), lng: parseFloat(lng) };

  geocoder.geocode({ location: latlng }, function (results, status) {
    if (status === "OK") {
      if (results[0]) {
        document.getElementById("issueLocation").value =
          results[0].formatted_address;
      } else {
        alert("No address found for this location.");
      }
    } else {
      alert("Geocoder failed due to: " + status);
    }
  });
}

// Handle form submission with AJAX
document.getElementById("issueForm").addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", document.getElementById("issueTitle").value);
    formData.append("description", document.getElementById("issueDescription").value);
    formData.append("location", document.getElementById("issueLocation").value);
    
    const imageFile = document.getElementById("issueImage").files[0];
    if (imageFile) {
        formData.append("image", imageFile);
    }

    fetch("/submit_issue", {
        method: "POST",
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 400) {
                // Handle 400 response (e.g., no detection in image)
                return response.json().then(data => {
                    throw new Error(data.message || "Image not detected. Please upload a valid image.");
                });
            }
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(data.message); // Show success message
            document.getElementById('issueForm').reset(); // Reset the form
            // clearImagePreview(); // Clear the image preview
            loadIssues(); // Refresh the issues list
            window.location.reload();
        } else {
            alert("Error: " + data.message); // Show error message
        }
    })
    .catch(error => {
        console.error("Error submitting issue:", error);
        alert(error.message); // Show clean notification for no detection or other errors
    });
});

// Load issues for tracking and feedback
function loadIssues() {
  fetch("/get_issues")
    .then((response) => response.json())
    .then((issues) => {
      const table = document.getElementById("issuesTable");
      table.innerHTML = "";
      issues.forEach((issue) => {
        const badgeColor =
          issue.status === "Resolved"
            ? "bg-success"
            : issue.status === "In Progress"
            ? "bg-warning"
            : "bg-danger";
        table.innerHTML += `
          <tr>
            <td>${issue.title}</td>
            <td><span class="badge ${badgeColor}">${issue.status}</span></td>
            <td>
              <button class="btn btn-sm btn-info" onclick="showFeedbackForm(${issue.id})">
                <i class="fas fa-comment"></i> Feedback
              </button>
            </td>
          </tr>
        `;
      });
    });
}

// Initialize issues on page load
document.addEventListener("DOMContentLoaded", loadIssues);

document.addEventListener('DOMContentLoaded', function () {
    fetchIssues();
});

function fetchIssues() {
    fetch('/get_issues')
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    // Redirect to login page if user is not logged in
                    window.location.href = '/login';
                    return;
                }
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const issuesTable = document.getElementById('issuesTable');
                issuesTable.innerHTML = ''; // Clear existing rows

                data.issues.forEach(issue => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${issue.title}</td>
                        <td>${issue.status}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="openFeedbackModal(${issue.complaintID})">
                                <i class="fas fa-comment"></i> Feedback
                            </button>
                        </td>
                    `;
                    issuesTable.appendChild(row);
                });
            } else {
                alert('Failed to fetch issues: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching issues:', error);
            alert('An error occurred while fetching issues.');
        });
}

// Function to open the feedback modal
function openFeedbackModal(complaintId) {
    console.log("Feedback button clicked for complaint ID:", complaintId); // Debugging
    if (!complaintId) {
        console.error("No complaint ID provided.");
        return;
    }
    document.getElementById('complaintID').value = complaintId;

    // Attach star rating event listeners when the modal is opened
    setupStarRating();

    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    feedbackModal.show();
}

// Function to handle star rating
function setupStarRating() {
    document.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', function () {
            const rating = parseInt(this.getAttribute('data-value')); // Ensure rating is a number
            document.getElementById('rating').value = rating;

            // Highlight selected stars (left to right)
            document.querySelectorAll('.star').forEach(s => {
                const starValue = parseInt(s.getAttribute('data-value')); // Ensure starValue is a number
                if (starValue <= rating) {
                    s.style.color = '#ffc107'; // Highlighted color (yellow)
                } else {
                    s.style.color = '#e4e5e9'; // Default color (gray)
                }
            });
        });
    });
}

// Function to submit feedback
function submitFeedback() {
    const complaintID = document.getElementById('complaintID').value;
    const comments = document.getElementById('comments').value;
    const rating = document.getElementById('rating').value;

    if (!rating || !comments) {
        alert('Please provide both a rating and comments.');
        return;
    }

    fetch('/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            complaintID: complaintID,
            rating: rating,
            comments: comments
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Feedback submitted successfully!');
            window.location.reload(); // Refresh the page
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error submitting feedback:', error);
        alert('Error submitting feedback: ' + error.message);
    });
}

window.history.pushState(null, "", window.location.href);  
window.onpopstate = function () {  
  window.history.pushState(null, "", window.location.href);  
};
