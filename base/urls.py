from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import chess.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/


urlpatterns = [
    path("<int:game>", chess.views.index, name="index"),
    path("", chess.views.index, name="index"),
    path("db/", chess.views.db, name="db"),
    path("admin/", admin.site.urls),
    path("test/",chess.views.test),
    path("img/chesspieces/wikipedia/<str:piece>.png",chess.views.chesspng),
    path("about/",chess.views.about, name="about"),
    #path("websockets/", include('chess.urls')),
]
