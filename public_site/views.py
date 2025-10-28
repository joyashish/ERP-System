from django.shortcuts import render

def home_page(request):
    return render(request, 'public_site/home.html')

def pricing_page(request):
    # We will add plans here later
    return render(request, 'public_site/pricing.html')

def about_page(request):
    return render(request, 'public_site/about.html')