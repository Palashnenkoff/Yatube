from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from . models import Post, Group, Follow
from . forms import PostForm, CommentForm

User = get_user_model()

# source venv/Scripts/activate
# python manage.py runserver
# python manage.py shell
# python manage.py test


def index(request):
    post_list = Post.objects.all()
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    # # раньше была запись posts = Post.objects.filter(group=group)[:12]
    return render(request, "group.html", {
        "group": group,
        "page": page,
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")

    return render(request, "new_post.html", {"form": form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    # # двойное подчеркивание означает,
    # что обращение идет к полю связанной модели
    if request.user == post.author:
        form = PostForm(
            instance=post,
            files=request.FILES or None,
            data=request.POST or None
        )
        if form.is_valid():
            post.save()
            return redirect('post', username=username, post_id=post_id)
        return render(
            request,
            'new_post.html',
            {"form": form, "post": post, "is_edit": True},
        )
    return redirect('post', username=post.author.username, post_id=post_id)


def profile(request, username):
    """Отображает страницу пользователя с его постами и информацией"""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    # Подписан ли пользователь
    is_following = False
    if request.user.is_authenticated:
        if author.following.filter(user=request.user).exists():
            is_following = True
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'following': is_following,
    })


def post_view(request, username, post_id):
    """Отображает страницу с отдельным постом и комментариями"""
    # # Количество постов есть в author через related_name.
    # Смотри 'author.posts.count()' в шаблоне post.html
    # author__username=username - это обращение к полю связанной модели(__)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    author = post.author
    form = CommentForm()
    return render(request, 'post.html', {
        'author': author,
        'post': post,
        'comments': comments,
        'form': form,
    })


@login_required
def add_comment(request, username, post_id):
    """Создание комментария к посту (просто сохраняется в базу)"""
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    """Отображает страницу с ошибкой 404"""
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    """Отображает страницу с ошибкой 500"""
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    """Выводит посты авторов на которых подписан пользователь"""
    posts_follow = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_follow, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page})


@login_required
def profile_follow(request, username):
    """Подписка на автора"""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if request.user != author and follow is False:
        Follow.objects.create(user=request.user, author=author)
        return redirect('profile', username=username)
    return redirect('profile', username=username)
    # КАК МОЖНО СДЕЛАТЬ БЕЗ ПОСЛЕДНЕГО РЕДИРЕКТА, ЧТОБЫ ЛИШНИЙ РАЗ
    # НЕ РЕНДЕРИТЬ СТРАНИЦУ???
    # КАКОЙ-НИБУДЬ АНАЛОГ break, только для if.
    # Я кончено убрал в шаблоне кнопку подписки автора в своем профайле,


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=request.user, author=author)
    subscription.delete()
    return redirect('profile', username=username)
