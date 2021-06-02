
from django.conf.urls import handler404, handler500
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# переменные содержащие  адреса view-функций страниц с ошибками
handler404 = "posts.views.page_not_found"  # noqa
handler500 = "posts.views.server_error"  # noqa

urlpatterns = [
    #  регистрация и авторизация
    path('auth/', include('users.urls')),

    #  если нужного шаблона для /auth не нашлось в файле users.urls —
    #  ищем совпадения в файле django.contrib.auth.urls
    path('auth/', include('django.contrib.auth.urls')),

    #  раздел администратора
    path('admin/', admin.site.urls),

    #  обработчик для главной страницы ищем в urls.py приложения posts
    path('', include('posts.urls')),

    path('about/', include('about.urls', namespace='about')),
]
# # Доступность файлов загруженных пользователями в режиме отладки:
# Этот код будет работать, когда ваш сайт в режиме отладки. Он позволяет
# обращаться файлам в директории, указанной в MEDIA_ROOT
# по имени, через префикс MEDIA_URL.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
