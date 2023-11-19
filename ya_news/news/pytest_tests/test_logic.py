from http import HTTPStatus
from random import choice

import pytest
from pytest_django.asserts import assertFormError, assertRedirects
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(
    client, form_data, news_detail_route
):
    initial_comments_count = Comment.objects.count()
    response = client.post(news_detail_route, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={news_detail_route}'
    assertRedirects(response, expected_url)

    final_comments_count = Comment.objects.count()

    assert initial_comments_count == final_comments_count, (
        f'Создано {initial_comments_count} комментариев,'
        f' ожидалось {final_comments_count}')


def test_user_can_create_comment(
        admin_user, admin_client, news, form_data, news_detail_route
):
    initial_comments_count = Comment.objects.count()
    response = admin_client.post(news_detail_route, data=form_data)
    expected_url = news_detail_route + '#comments'
    assertRedirects(response, expected_url)

    comments_count = Comment.objects.count()
    final_comments_count = Comment.objects.count()
    assert initial_comments_count + 1 == final_comments_count, (
        f'Создано {comments_count} комментариев,'
        f' ожидалось {final_comments_count}')

    new_comment = Comment.objects.last()
    assert new_comment.text == form_data['text']
    assert new_comment.news == news
    assert new_comment.author == admin_user


def test_user_cant_use_bad_words(admin_client, news_detail_route):
    initial_comments_count = Comment.objects.count()
    bad_words_data = {'text': f'Какой-то text, {choice(BAD_WORDS)}, еще text'}
    url = news_detail_route
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    final_comments_count = Comment.objects.count()
    assert initial_comments_count == final_comments_count


def test_author_can_edit_comment(
        author_client, comment, form_data, news_edit_route, news_detail_route
):
    original_author = comment.author
    original_news = comment.news
    response = author_client.post(news_edit_route, data=form_data)
    assert response.status_code == HTTPStatus.FOUND

    comment.refresh_from_db()

    assert comment.text == form_data['text'], (
        f'Комментарий "{comment.text}" не был обновлен ,'
        f' ожидалось {form_data["text"]}')

    assert comment.author == original_author, (
        f'Автор комментария "{comment.author}" был обновлен, '
        f'ожидался {original_author}'
    )

    assert comment.news == original_news, (
        f'Новость комментария "{comment.news}" была обновлена, '
        f'ожидалась {original_news}'
    )


def test_author_can_delete_comment(
        author_client, news_delete_route, news_detail_route
):
    initial_comments_count = Comment.objects.count()
    response = author_client.post(news_delete_route)
    expected_url = news_detail_route + '#comments'
    assertRedirects(response, expected_url)
    final_comments_count = Comment.objects.count()
    assert initial_comments_count == final_comments_count + 1, (
        f'Создано {initial_comments_count} комментариев,'
        f' ожидалось {final_comments_count}')


def test_other_user_cant_edit_comment(
        admin_client, comment, form_data, news_edit_route
):
    old_comment = comment.text
    old_comment_author = comment.author
    old_comment_news = comment.news
    response = admin_client.post(news_edit_route, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_comment, (
        f'Текст комментария "{comment.text}" был обновлен, '
        f'ожидался {old_comment}'
    )

    assert comment.author == old_comment_author, (
        f'Автор комментария "{comment.author}" был обновлен, '
        f'ожидался {old_comment_author}'
    )

    assert comment.news == old_comment_news, (
        f'Новость комментария "{comment.news}" была обновлена, '
        f'ожидалась {old_comment_news}'
    )


def test_other_user_cant_delete_comment(admin_client, news_delete_route):
    initial_comments_count = Comment.objects.count()
    response = admin_client.post(news_delete_route)
    assert response.status_code == HTTPStatus.NOT_FOUND
    final_comments_count = Comment.objects.count()
    assert initial_comments_count == final_comments_count, (
        f'Создано {initial_comments_count} комментариев,'
        f' ожидалось {final_comments_count}')
