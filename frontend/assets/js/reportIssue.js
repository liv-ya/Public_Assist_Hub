let map, marker, autocomplete;
// Geo Location integrating
        function initMap() {
            const defaultLocation = { lat: -34.397, lng: 150.644 }; 

            map = new google.maps.Map(document.getElementById("map"), {
                center: defaultLocation,
                zoom: 15
            });

            marker = new google.maps.Marker({
                position: defaultLocation,
                map: map,
                title: "Selected Location"
            });

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        const userLocation = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude
                        };
                        map.setCenter(userLocation);
                        marker.setPosition(userLocation);
                        getPlaceName(userLocation.lat, userLocation.lng);
                    },
                    () => alert("Geolocation permission denied.")
                );
            }

            autocomplete = new google.maps.places.Autocomplete(document.getElementById("issueLocation"));
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
                        document.getElementById("issueLocation").value = results[0].formatted_address;
                    } else {
                        alert("No address found for this location.");
                    }
                } else {
                    alert("Geocoder failed due to: " + status);
                }
            });
        }

        document.getElementById("issueForm").addEventListener("submit", function(event) {
            event.preventDefault();
            
            let title = document.getElementById("issueTitle").value;
            let description = document.getElementById("issueDescription").value;
            let location = document.getElementById("issueLocation").value;

            fetch('/submit_issue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description, location })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadIssues();
            });
        });

        function loadIssues() {
            fetch('/get_issues')
            .then(response => response.json())
            .then(issues => {
                let table = document.getElementById("issuesTable");
                table.innerHTML = "";
                issues.forEach(issue => {
                    let badgeColor = issue.status === "Resolved" ? "bg-success" : issue.status === "In Progress" ? "bg-warning" : "bg-danger";
                    table.innerHTML += `
                        <tr>
                            <td>${issue.title}</td>
                            <td><span class="badge ${badgeColor}">${issue.status}</span></td>
                            <td>
                                <button class="btn btn-sm btn-info" onclick="showFeedbackForm(${issue.id})"><i class="fas fa-comment"></i> Feedback</button>
                            </td>
                        </tr>`;
                });
            });
        }

        function showFeedbackForm(issueId) {
            document.querySelector(".feedback-section").style.display = "block";
            document.getElementById("feedbackIssueId").value = issueId;
        }

        document.getElementById("feedbackForm").addEventListener("submit", function(event) {
            event.preventDefault();

            let issueId = document.getElementById("feedbackIssueId").value;
            let feedback = document.getElementById("feedback").value;
            let rating = document.getElementById("rating").value;

            fetch('/submit_feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ issue_id: issueId, feedback, rating })
            })
            .then(response => response.json())
            .then(data => alert(data.message));
        });

        document.addEventListener("DOMContentLoaded", loadIssues);