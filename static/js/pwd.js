document.addEventListener("DOMContentLoaded", function () {
    fetchIssues();
    refreshCounts();
    document.getElementById("view-feedback-btn").addEventListener("click", viewFeedback);
});

function fetchIssues() {
    fetch("/api/issues/pwd")
        .then(response => response.json())
        .then(data => {
            displayIssues(data);
        })
        .catch(error => console.error("Error fetching PWD issues:", error));
}

function displayIssues(issues) {
    const issueList = document.getElementById("issue-list");
    issueList.innerHTML = "";

    issues.forEach(issue => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${issue.id}</td>
            <td>${issue.category}</td>
            <td>${issue.description}</td>
            <td>
                <select class="form-control" onchange="updateStatus(${issue.id}, this.value)">
                    <option value="Pending" ${issue.status === "Pending" ? "selected" : ""}>Pending</option>
                    <option value="In Progress" ${issue.status === "In Progress" ? "selected" : ""}>In Progress</option>
                    <option value="Resolved" ${issue.status === "Resolved" ? "selected" : ""}>Resolved</option>
                </select>
            </td>
            <td>
                <button class="btn btn-success" onclick="resolveIssue(${issue.id})">Resolve</button>
            </td>
        `;
        issueList.appendChild(row);
    });
}

function updateStatus(issueId, newStatus) {
    fetch(`/api/issues/${issueId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(() => window.location.reload())
    .catch(error => console.error("Error updating status:", error));
}

function deleteIssue(issueId) {
    if (confirm("Are you sure you want to delete this issue?")) {
        fetch(`/api/issues/${issueId}`, {
            method: "DELETE"
        })
        .then(response => response.json())
        .then(() => fetchIssues())
        .catch(error => console.error("Error deleting issue:", error));
    }
}

function resolveIssue(issueId) {
    if (confirm("Are you sure you want to mark this issue as resolved?")) {
        fetch(`/api/issues/${issueId}/resolve`, {
            method: "PUT"
        })
        .then(response => response.json())
        .then(() => window.location.reload())
        .catch(error => console.error("Error resolving issue:", error));
    }
}

function checkIssue(issueId) {
    fetch(`/api/issues/${issueId}/check`, {
        method: "PUT"
    })
    .then(response => response.json())
    .then(() => window.location.reload())
    .catch(error => console.error("Error checking issue:", error));
}

function refreshCounts() {
    fetch("/api/issues/counts/pwd")
        .then(response => response.json())
        .then(data => {
            document.getElementById("pending-count").textContent = data.pending_count;
            document.getElementById("resolved-count").textContent = data.resolved_count;
        })
        .catch(error => console.error("Error refreshing counts:", error));
}

function viewFeedback() {
    fetch("/api/feedback/pwd")
        .then(response => response.json())
        .then(data => {
            const feedbackList = document.getElementById("feedback-list");
            feedbackList.innerHTML = "";

            if (data.length === 0) {
                // Display a message if no feedback is found
                feedbackList.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center">No feedback found for PWD issues.</td>
                    </tr>
                `;
            } else {
                // Populate the table with feedback data
                data.forEach(feedback => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${feedback.complaintID}</td>
                        <td>${feedback.email}</td>
                        <td>${feedback.rating}</td>
                        <td>${feedback.comments}</td>
                    `;
                    feedbackList.appendChild(row);
                });
            }

            // Show the modal
            const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));
            feedbackModal.show();
        })
        .catch(error => console.error("Error fetching feedback:", error));
}

window.history.pushState(null, "", window.location.href);  
window.onpopstate = function () {  
  window.history.pushState(null, "", window.location.href);  
};