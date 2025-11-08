from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from .forms import RegisterForm, PhotoForm
from .models import Photo
import os

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('gallery')
    else:
        form = RegisterForm()
    return render(request, 'gallery/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('gallery')
    return render(request, 'gallery/login.html', {'next': request.GET.get('next', '')})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def gallery_view(request):
    photos = Photo.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'gallery/gallery.html', {
        'photos': photos,
        'username': request.user.username
    })

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            for image in request.FILES.getlist('images'):
                Photo.objects.create(user=request.user, image=image)
            return redirect('gallery')
    else:
        form = PhotoForm()
    return render(request, 'gallery/upload.html', {'form': form})

@login_required
def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk, user=request.user)
    all_photos = list(Photo.objects.filter(user=request.user).order_by('-uploaded_at'))
    current_index = all_photos.index(photo)
    
    prev_photo = all_photos[current_index - 1] if current_index > 0 else None
    next_photo = all_photos[current_index + 1] if current_index < len(all_photos) - 1 else None
    
    return render(request, 'gallery/photo_detail.html', {
        'photo': photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo
    })

@login_required
def delete_photo(request, pk):
    if request.method == 'POST':  # Changed to POST for security
        photo = get_object_or_404(Photo, pk=pk, user=request.user)
        photo.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def download_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk, user=request.user)
    file_path = photo.image.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/jpeg')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    raise Http404("Photo not found")