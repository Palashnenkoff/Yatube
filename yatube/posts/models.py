from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст', help_text='Введите текст')
    # #verbose_name='Текст' меняет на странице лейбл text на Текст
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey('Group', on_delete=models.SET_NULL,
                              blank=True, null=True,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Выберите группу')
# on_delete=models.CASCADE удаляет все посты автора при его удалении группы
# on_delete=models.SET_NULL посты остаются без группы
    image = models.ImageField(
        upload_to='posts/',
        blank=True, null=True,
        verbose_name='Картинка')

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey('Post',
                             on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Введите текст')
    created = models.DateTimeField('date published', auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following')
