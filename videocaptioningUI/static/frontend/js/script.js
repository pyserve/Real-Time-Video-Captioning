// Function to get CSRF token from cookie
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function handleFileSelect(event) {
    var input = event.target;
    var progressBar = $('.progress');
    var submitButton = $('#submitBtn');
    var selectInfo = $("#selectInfo")
    var selectFile = $("#selectFile")
    selectFile.addClass("disabled");
    selectInfo.html("File is uploading...")

    if (input.files && input.files[0]) {
        progressBar.show();

        var formData = new FormData();
        formData.append('file', input.files[0]);

        // Get the CSRF token from the cookie
        var csrftoken = getCookie('csrftoken');

        // Send the file data to the Django URL using AJAX
        $.ajax({
            url: '/',  // Replace this with your Django URL
            type: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': csrftoken
            },
            processData: false,
            contentType: false,
            xhr: function () {
                var xhr = new XMLHttpRequest();
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        var percentLoaded = Math.round((e.loaded / e.total) * 100);
                        $('.progress-bar').css('width', percentLoaded + '%');
                        $('.progress-bar').attr('aria-valuenow', percentLoaded);
                        $('.progress-bar').text(percentLoaded + '%');
                    }
                }, false);
                return xhr;
            },
            success: function (data) {
                // Handle success response here (if needed)
                console.log('File uploaded successfully:');
                selectFile.removeClass("disabled")
                selectInfo.addClass("text-success")
                selectInfo.html("File is loaded successfully!!")
            },
            error: function (xhr, status, error) {
                // Handle error response here (if needed)
                console.error('Error uploading file:', xhr.responseText);
            },
            complete: function () {
                // Hide the progress bar after the upload is complete
                progressBar.hide();
                // Optionally, you can reset the file input to allow selecting a new file
                $('#file').val('');
            }
        });
    }
}
