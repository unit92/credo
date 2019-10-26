"""credo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from . import views

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

handler404 = views.page_not_found
handler500 = views.server_error

urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),
    path('jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    path('admin/docs/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('favicon.ico', favicon_view),
    path('', views.index, name='index'),
    path('songs/', views.song_list),
    path('songs/<song_id>', views.song),
    path('songs/<song_id>/compare', views.song_compare_picker),
    path('songs/<song_id>/editions/<edition_id>', views.edition),
    path('songs/<song_id>/revisions/<revision_id>',
         views.RevisionView.as_view()),
    path('revisions/<revision_id>/comments', views.revision_comments),
    path('revisions/<revision_id>/comment', views.add_revision_comment),
    path('compare', views.compare),
    path('mei/<mei_id>', views.mei),
    path('diff', views.diff),
    path('signup', views.signup, name='signup'),
    path('revise', views.make_revision),
    path('login', views.login),
    path('merge', views.merge_measure_layers_json)
]
