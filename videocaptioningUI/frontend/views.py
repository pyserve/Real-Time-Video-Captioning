from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
import pickle
import os
import cv2 as cv
from tempfile import NamedTemporaryFile
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Model
from keras.preprocessing.sequence import pad_sequences
import numpy as np
import base64

class VideoCaptionView(View):
    def __init__(self):
        with open('tokenizer.pkl', 'rb') as file:
            self.tokenizer = pickle.load(file)
            file.close()

        with open('caption_model.pkl', 'rb') as file:
            self.model = pickle.load(file)
            file.close()

        self.img_model = VGG16()
        self.img_model = Model(inputs=self.img_model.inputs, outputs=self.img_model.layers[-2].output)

    def get(self, request):
        return render(request, "index.html", {'caption': None})

    def post(self, request):
        file_uploaded = request.FILES.get('file')
        img_frame = None
        if request.POST.get('stream'):
            imageData = request.POST['stream']
            imageData = base64.b64decode(imageData.split(',')[1])

            nparr = np.frombuffer(imageData, np.uint8)
            img_frame = cv.imdecode(nparr, cv.IMREAD_COLOR)

        gen_captions = []
        processed_frames = []
        if file_uploaded:
            processed_frames = self.process_uploaded_file(file_uploaded)
        else:
            processed_frames = [img_frame]

        print(f'Frames Count: {len(processed_frames)}')

        if len(processed_frames) == 1:
            sel_frame_indices = [0]
        else:
            sel_frame_indices = np.random.randint(0, len(processed_frames), 10)

        for frame_idx in sel_frame_indices:
            image = cv.resize(processed_frames[frame_idx], (224, 224))
            image = img_to_array(image)
            image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
            image = preprocess_input(image)
            feature = self.img_model.predict(image, verbose=0)
            generated_caption = self.predict_caption(self.model, feature, self.tokenizer, 29)
            gen_captions.append(generated_caption)

        captions = []
        for cap in set(gen_captions):
            captions.append(' '. join(set(cap.split())))

        captions = '. '.join(captions)
        captions = captions.replace("startseq", "")
        captions = captions.replace("endseq", "")
        return JsonResponse({'caption': captions})

    def process_uploaded_file(self, file_uploaded):
        # Ensure the file is a TemporaryUploadedFile or InMemoryUploadedFile
        if not isinstance(file_uploaded, (TemporaryUploadedFile, InMemoryUploadedFile)):
            raise ValueError("Invalid file type. Expected TemporaryUploadedFile or InMemoryUploadedFile.")

        # Save the temporary file
        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            for chunk in file_uploaded.chunks():
                temp_file.write(chunk)

        # Determine file type (image or video)
        _, file_extension = os.path.splitext(file_uploaded.name)
        file_extension = file_extension.lower()

        if file_extension in {'.png', '.jpg', '.jpeg',}:
            # Process image file
            image = cv.imread(temp_file.name)
            frames = [image]
        elif file_extension in {'.mp4', '.avi', '.mkv', '.gif'}:
            # Process video file
            frames = VideoCaptionView.process_video_frames(temp_file.name)
        else:
            raise ValueError("Unsupported file type.")

        return frames

    def process_video_frames(video_path, max_frames=10):
        video_capture = cv.VideoCapture(video_path)

        # Check if the video capture object is successfully opened
        if not video_capture.isOpened():
            print("Error: Could not open video file.")
            return []

        frames = []
        frame_counter = 0

        while frame_counter < max_frames:
            # Read a frame from the video
            ret, frame = video_capture.read()

            # If the video is over, break the loop
            if not ret:
                break

            # Process the frame (you can perform additional processing here)
            frames.append(frame)
            frame_counter += 1

        # Release the video capture object
        video_capture.release()

        return frames

    def idx_to_word(self, integer, tokenizer):
        for word, index in tokenizer.word_index.items():
            if index == integer:
                return word
        return None

    def predict_caption(self, model, image, tokenizer, max_length):
        # add start tag for generation process
        in_text = 'startseq'

        for i in range(max_length):
            sequence = self.tokenizer.texts_to_sequences([in_text])[0]
            sequence = pad_sequences([sequence], max_length)
            yhat = self.model.predict([image, sequence], verbose=0)
            yhat = np.argmax(yhat)
            word = self.idx_to_word(yhat, self.tokenizer)

            if word is None:
                break

            in_text += " " + word
            if word == 'endseq':
                break

        return in_text