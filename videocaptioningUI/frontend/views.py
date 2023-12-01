from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
import pickle
import cv2 as cv
from tempfile import NamedTemporaryFile
from django.core.files.uploadedfile import TemporaryUploadedFile
from keras.applications.vgg16 import VGG16, preprocess_input
from keras.preprocessing.image import load_img, img_to_array
from keras.models import Model
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
import numpy as np
import pandas as pd

class VideoCaptionView(View):
    def __init__(self):
        pass
        # with open('tokenizer.pkl', 'rb') as file:
        #     self.tokenizer = pickle.load(file)
        #     file.close()
        #
        # with open('caption_model.pkl', 'rb') as file:
        #     self.model = pickle.load(file)
        #     file.close()
        #
        # self.img_model = VGG16()
        # self.img_model = Model(inputs=self.img_model.inputs, outputs=self.img_model.layers[-2].output)
    def get(self, request):
        return render(request, "index.html", {'caption': None})

    def post(self, request):
        file_uploaded = request.FILES.get('file')

        gen_captions = []
        if file_uploaded:
            processed_frames = self.process_uploaded_video(file_uploaded)
            print(f'Video Frames Count: {len(processed_frames)}')

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

    def process_uploaded_video(self, file_uploaded):
        # Ensure the file is a TemporaryUploadedFile
        if not isinstance(file_uploaded, TemporaryUploadedFile):
            raise ValueError("Invalid file type. Expected TemporaryUploadedFile.")

        # Save the temporary file
        with NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file_uploaded.chunks():
                temp_file.write(chunk)

        # Open the temporary file with cv2.VideoCapture
        video_capture = cv.VideoCapture(temp_file.name)

        # Check if the video capture object is successfully opened
        if not video_capture.isOpened():
            print("Error: Could not open video file.")
            return

        frames = []

        while True:
            # Read a frame from the video
            ret, frame = video_capture.read()

            # If the video is over, break the loop
            if not ret:
                break

            # Process the frame (you can perform additional processing here)
            frames.append(frame)

        # Release the video capture object
        video_capture.release()

        # Do something with the processed frames, e.g., return or display them
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