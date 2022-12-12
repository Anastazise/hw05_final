from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel

User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(max_length=500, verbose_name='Текст')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts', verbose_name='Автор')
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True, on_delete=models.SET_NULL,
        verbose_name='Сообщество',
        related_name='posts')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True)

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self) -> str:
        return self.text


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название группы')
    slug = models.SlugField(max_length=50, unique=True,
                            verbose_name='URL')
    description = models.TextField(max_length=500,
                                   verbose_name='Описание сообщества')

    def __str__(self) -> str:
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария",
    )
    text = models.TextField('Текст', 
    help_text='Текст нового комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост')


    class Meta:
        ordering = ("-created",)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
