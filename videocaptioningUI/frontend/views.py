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
from tensorflow.keras.models import Model, load_model
from keras.preprocessing.sequence import pad_sequences
import numpy as np

class VideoCaptionView(View):
    def __init__(self):
        self.tokenizer = pickle.load(open(r'tokenizers.pkl', 'rb'))
        self.model = load_model(r'best_model.h5')
        self.img_model = VGG16()
        self.img_model = Model(inputs=self.img_model.inputs, outputs=self.img_model.layers[-2].output)
        self.max_length = 35

    def get(self, request):
        return render(request, "index.html", {'caption': None})

    def post(self, request):
        gen_captions = []
        processed_frames = []

        if request.FILES.get('stream'):
            frames_data = request.FILES['stream']
            processed_frames = self.process_uploaded_file(frames_data)

        if request.FILES.get('file'):
            file_uploaded = request.FILES['file']
            processed_frames = self.process_uploaded_file(file_uploaded)

        print(f'Frames Count: {len(processed_frames)}')

        for frame in processed_frames:
            image = cv.resize(frame, (224, 224))
            image = img_to_array(image)
            image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
            image = preprocess_input(image)
            feature = self.img_model.predict(image, verbose=1)
            generated_caption = self.predict_caption(self.model, feature, self.tokenizer, self.max_length)
            gen_captions.append(generated_caption)

        captions = '. '.join(set(gen_captions)).replace("startseq", "").replace("endseq", "")
        print(f"Generated Caption: {captions}")
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
        elif file_extension in {'.mp4', '.avi', '.mkv', '.gif', '.webm'}:
            # Process video file
            frames = VideoCaptionView.process_video_frames(temp_file.name)
        else:
            raise ValueError("Unsupported file type.")

        return frames

    def process_video_frames(video_path, max_frames=10):
        video_capture = cv.VideoCapture(video_path)

        if not video_capture.isOpened():
            print("Error: Could not open video file.")
            return []

        frames = []
        frame_counter = 0
        while frame_counter < 1000:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            frames.append(frame)
            frame_counter += 1

        video_capture.release()

        selected_frame_indices = np.random.choice(len(frames), max_frames, replace=False)
        random_frames = [frames[i] for i in selected_frame_indices]
        return random_frames

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