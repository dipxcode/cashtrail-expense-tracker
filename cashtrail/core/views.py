from django.shortcuts import render

def landing(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard')
    return render(request, 'core/landing.html')

def about(request):
    return render(request, 'core/about.html')

def privacy(request):
    return render(request, 'core/privacy.html')
