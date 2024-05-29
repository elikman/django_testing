import pytest
from http import HTTPStatus

from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from news.models import Comment
from news.forms import BAD_WORDS, WARNING

pytestmark = pytest.mark.django_db


def test_user_can_create_comment(author_client, author, news, form_data):
    """Авторизованный пользователь может отправить комментарий."""
    comments_count_before = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.count() == comments_count_before + 1
    new_comment = Comment.objects.filter(
        author=author, text=form_data['text'], news=news).latest('created')
    assert new_comment.author == author
    assert new_comment.text == form_data['text']
    assert new_comment.news == news


def test_anonymous_user_cant_create_comment(client, news, form_data):
    """Анонимный пользователь не может отправить комментарий."""
    comments_count_before = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    assert Comment.objects.count() == comments_count_before


def test_user_cant_use_bad_words(author_client, news,):
    """Проверка содержания запрещенных слов."""
    comments_count_before = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    assert Comment.objects.count() == comments_count_before


def test_author_can_edit_comment(author_client, author, news, form_data,
                                 comment):
    """Автор может редактировать свой комментарий."""
    original_author = comment.author
    original_news = comment.news

    edit_url = reverse('news:edit', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)

    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.author == original_author
    assert comment.news == original_news


def test_user_cant_edit_comment_of_another_user(
        admin_client, form_data, comment
):
    """Пользователь не может редактировать чужой комментарий."""
    original_author = comment.author
    original_news = comment.news
    original_text = comment.text

    edit_url = reverse('news:edit', args=(comment.id,))
    response = admin_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment.refresh_from_db()
    assert comment.text == original_text
    assert comment.author == original_author
    assert comment.news == original_news


def test_author_can_delete_comment(author_client, news, comment):
    """Автор может удалять свой комментарий."""
    comments_count_before = Comment.objects.count()
    comment_id = comment.id
    delete_url = reverse('news:delete', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)

    assert Comment.objects.count() == comments_count_before - 1
    with pytest.raises(Comment.DoesNotExist):
        Comment.objects.get(id=comment_id)


def test_other_user_cant_delete_news(admin_client, comment):
    """Пользователь не может удалять чужой комментарий."""
    comments_count_before = Comment.objects.count()
    delete_url = reverse('news:delete', args=(comment.id,))
    response = admin_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == comments_count_before
