from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()
MAX_LENGTH = 256
NAME_MAX_LENGTH = 15


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено')

    class Meta:
        abstract = True
        ordering = ('created_at', )
        default_related_name = '%(class)ss'


class Category(PublishedModel):
    title = models.CharField(max_length=MAX_LENGTH, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=('Идентификатор страницы для URL; разрешены символы '
                   'латиницы, цифры, дефис и подчёркивание.')
    )

    class Meta(PublishedModel.Meta):
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:NAME_MAX_LENGTH]


class Location(PublishedModel):
    name = models.CharField(max_length=MAX_LENGTH,
                            verbose_name='Название места')

    class Meta(PublishedModel.Meta):
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:NAME_MAX_LENGTH]


class Post(PublishedModel):
    title = models.CharField(max_length=MAX_LENGTH, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=('Если установить дату и время в будущем —'
                   ' можно делать отложенные публикации.')
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор публикации',
        related_name='posts')
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория')

    class Meta(PublishedModel.Meta):
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date', )

    def is_visible_to_user(self, user):
        if self.author == user:
            return True
        if not self.is_published:
            return False
        if self.pub_date > timezone.now():
            return False
        return True

    def __str__(self):
        return self.title[:NAME_MAX_LENGTH]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, verbose_name="Пост",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User, verbose_name="Автор",
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        "Комментарий",
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        author = self.author.username
        title = self.post.title
        text = self.text[:NAME_MAX_LENGTH]
        return ('Комментарий от '
                f'{author} к посту {title}. '
                f'Текст комментария: {text}')
