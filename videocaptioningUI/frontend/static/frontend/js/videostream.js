$(document).ready(function () {
    var videoElement = $('#videoElement');
    var fileUpload = $("#file-upload");
    var imageUploaded = $('#imageUploaded');
    var videoUploaded = $('#videoUploaded');
    var csrftoken = getCookie('csrftoken');
    var caption_text = $("#caption_text");

    var mediaRecorder;
    var recordedChunks = [];
    var startTime;
    var sendInterval = 5000;  // Set the interval for sending chunks (in milliseconds)

    $("#startCapture").on("click", function () {
        startVideoCapture();
    });

    function startVideoCapture() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                videoElement.prop('srcObject', stream);
                videoElement.removeClass("d-none");
                fileUpload.addClass("d-none");
                imageUploaded.addClass("d-none");
                videoUploaded.addClass("d-none");

                // Create a MediaRecorder
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = function (event) {
                    if (event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = function () {
                    var combinedVideoBlob = new Blob(recordedChunks, { type: 'video/webm' });
                    var combinedVideoFile = new File([combinedVideoBlob], 'combined_video.webm', { type: 'video/webm' });

                    // Send combined video file to the server
                    var formData = new FormData();
                    formData.append('stream', combinedVideoFile);
                    
                    caption_text.html('Processing caption...');
                    $.ajax({
                        type: "POST",
                        url: "/",
                        data: formData,
                        processData: false,
                        contentType: false,
                        headers: {
                            'X-CSRFToken': csrftoken,
                        },
                        success: function (data) {
                            console.log("Combined video sent successfully:", data);
                            caption_text.html(data.caption);
                        },
                        error: function (error) {
                            console.error("Error sending combined video:", error);
                        }
                    });

                    // Clear the recorded chunks array for the next interval
                    recordedChunks = [];

                    // Check if 10 seconds have elapsed, and stop capturing
                    if (Date.now() - startTime < 10000) {
                        mediaRecorder.start();
                        scheduleSendChunks();
                    } else {
                        stopVideoCapture(stream);
                        videoElement.addClass("d-none");
                        fileUpload.removeClass("d-none");
                    }
                };

                // Start recording
                mediaRecorder.start();

                // Record the start time
                startTime = Date.now();

                // Schedule sending video chunks
                scheduleSendChunks();
            })
            .catch(function (error) {
                console.error('Error accessing camera:', error);
            });
    }

    function scheduleSendChunks() {
        setTimeout(function () {
            // Stop recording after the specified interval
            mediaRecorder.stop();
        }, sendInterval);
    }

    function stopVideoCapture(stream) {
        // Stop the video stream
        var tracks = stream.getTracks();
        tracks.forEach(function (track) {
            track.stop();
        });

        // Clear the srcObject to stop the video
        videoElement.prop('srcObject', null);
    }
});
