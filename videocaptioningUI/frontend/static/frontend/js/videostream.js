$(document).ready(function () {
    var videoElement = $('#videoElement');
    var fileUpload = $("#file-upload");
    var imageUploaded = $('#imageUploaded');
    var videoUploaded = $('#videoUploaded');
    var csrftoken = getCookie('csrftoken');
    var caption_text = $("#caption_text");

    $("#startCapture").on("click", function () {
        startVideoCapture();
    });

    function startVideoCapture() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                // Display the video stream in the video element
                videoElement.prop('srcObject', stream);
                videoElement.removeClass("d-none");
                fileUpload.addClass("d-none");
                imageUploaded.addClass("d-none");
                videoUploaded.addClass("d-none");

                var canvas = $('<canvas>', {
                    id: 'myCanvas',
                    width: 400,
                    height: 200,
                    style: 'border:1px solid #000;'
                });
                var context = canvas[0].getContext('2d');
                canvas[0].width = 400;
                canvas[0].height = 200;

                videoElement.on('playing', function() {
                    context.drawImage(videoElement[0], 0, 0, canvas[0].width, canvas[0].height);

                    // Draw the current frame of the video onto the canvas
                    var imageData = context.getImageData(0, 0, canvas[0].width, canvas[0].height);
                    var pixelData = imageData.data;

                    var image = canvas[0].toDataURL("image/png");
                    $.ajax({
                        type: "POST",
                        url: "/",
                        data: {
                            'stream': image,
                        },
                        headers: {
                            'X-CSRFToken': csrftoken,
                        },
                        success: function(data) {
                            console.log("Data sent successfully:", data);
                            caption_text.html(data.caption);
                        },
                        error: function(error) {
                            console.error("Error sending data:", error);
                        }
                    });
                });

                // Stop capturing after a certain time (adjust as needed)
                setTimeout(function () {
                    stopVideoCapture(stream);
                    videoElement.addClass("d-none");
                    fileUpload.removeClass("d-none");
                }, 10000);
            })
            .catch(function (error) {
                console.error('Error accessing camera:', error);
            });
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