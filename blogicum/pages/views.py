from django.shortcuts import render


def about_page(request):
    return render(request, 'pages/about.html')


def rules_page(request):
    return render(request, 'pages/rules.html')
