from django import forms
from django.utils.translation import gettext_lazy as _

from . models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {'text': _('Текст'), }
        help_texts = {'text': _('Введите текст'),
                      'image': _('Вставьте картинку'), }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
