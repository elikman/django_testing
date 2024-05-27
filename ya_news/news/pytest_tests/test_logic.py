import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


@pytest.mark.django_db
class TestCommentCreation:
    COMMENT_TEXT = 'Текст комментария'

    @pytest.fixture
    def news(self):
        return News.objects.create(title='Заголовок', text='Текст')

    @pytest.fixture
    def url(self, news):
        return reverse('news:detail', args=(news.id,))

    @pytest.fixture
    def user(self):
        return User.objects.create(username='Мимо Крокодил')

    @pytest.fixture
    def auth_client(self, client, user):
        client.force_login(user)
        return client

    @pytest.fixture
    def form_data(self):
        return {'text': self.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self, client, url, form_data):
        client.post(url, data=form_data)
        comments_count = Comment.objects.count()
        assert comments_count == 0

    def test_user_can_create_comment(self, auth_client, url, form_data, news,
                                     user):
        response = auth_client.post(url, data=form_data)
        assert response.status_code == 302
        assert response.url == f'{url}#comments'
        comments_count = Comment.objects.count()
        assert comments_count == 1
        comment = Comment.objects.get()
        assert comment.text == self.COMMENT_TEXT
        assert comment.news == news
        assert comment.author == user

    def test_user_cant_use_bad_words(self, auth_client, url):
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        response = auth_client.post(url, data=bad_words_data)
        assert response.context['form'].errors['text'] == [WARNING]
        comments_count = Comment.objects.count()
        assert comments_count == 0
