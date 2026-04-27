from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Topic(models.Model):
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        ),
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'тема'
        verbose_name_plural = 'Темы'
        db_table = 'blog_category'

    def __str__(self):
        return self.title


class Venue(models.Model):
    name = models.CharField('Название места', max_length=256)
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'Места'
        db_table = 'blog_location'

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        ),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name='Категория',
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images',
        blank=True,
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        db_table = 'blog_post'

    def __str__(self):
        return self.title


class Discussion(models.Model):
    post = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
    )
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'обсуждение'
        verbose_name_plural = 'Обсуждения'
        db_table = 'blog_comment'

    def __str__(self):
        return self.text[:50]
