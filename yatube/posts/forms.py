from django import forms
from .models import Post, Comment
from yatube.settings import MIN_POST_LEN
from yatube.settings import COMMENT_MIN_LEN


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        help_texts = {
            'text': ('Текст поста'),
            'group': ('К какой группе принадлежит'),
            'image': ('Картинка')
        }

    def clean_text(self):
        data = self.cleaned_data["text"]

        if len(data) < MIN_POST_LEN:
            raise forms.ValidationError(
                f"Длинна поста должна быть не менее {MIN_POST_LEN} символов!"
            )

        return data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ["text"]

    def clean_text(self):
        data = self.cleaned_data["text"]

        if len(data) < COMMENT_MIN_LEN:
            raise forms.ValidationError(
                "Длинна комментария должна быть не менее"
                f" {COMMENT_MIN_LEN} символов!"
            )
        return data