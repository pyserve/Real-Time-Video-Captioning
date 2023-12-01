$(document).ready(function () {
    var videoElement = $('#videoElement');
    var fileUpload = $("#file-upload");

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
                    // Draw the current frame of the video onto the canvas
                    context.drawImage(videoElement[0], 0, 0, canvas[0].width, canvas[0].height);
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