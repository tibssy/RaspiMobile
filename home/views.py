"""
This module defines the view functions for the 'home' app.

It includes the 'home' view, which renders the home page.
"""

from django.shortcuts import render


def home(request):
    """
    Renders the 'Home' page.

    :param request: The HTTP request object.
    :type request: django.http.HttpRequest
    :return: An HTTP response rendering the 'home/index.html' template.
    :rtype: django.http.HttpResponse
    """

    return render(request, 'home/index.html')