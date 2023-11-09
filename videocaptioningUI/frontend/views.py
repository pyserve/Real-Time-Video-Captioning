from django.shortcuts import render
from django.views import View

class VideoCaptionView(View):
    def get(self, request):
        return render(request, "index.html", {})

    def post(self, request):
        print(request.FILES)
        return self.get(request)
