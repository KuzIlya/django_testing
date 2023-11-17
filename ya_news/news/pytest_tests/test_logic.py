from http import HTTPStatus
from random import choice

import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(
    client, pk_from_news, form_data, news_detail_route
):
    url = news_detail_route

    initial_comments_count = Comment.objects.count()

    response = client.post(url, data=form_data)

    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)

    final_comments_count = Comment.objects.count()

    assert initial_comments_count == final_comments_count, (
        f'Создано {initial_comments_count} комментариев,'
        f' ожидалось {final_comments_count}')


def test_user_can_create_comment(
        admin_user, admin_client, news, form_data, news_detail_route
):
    url = news_detail_route

    response = admin_client.post(url, data=form_data)
    expected_url = url + '#comments'
    assertRedirects(response, expected_url)

    comments_count = Comment.objects.count()
    expected_comments = 1
    assert comments_count == expected_comments, (
        f'Создано {comments_count} комментариев,'
        f' ожидалось {expected_comments}')

    new_comment = Comment.objects.last()
    assert new_comment.text == form_data['text']
    assert new_comment.news == news
    assert new_comment.author == admin_user


def test_user_cant_use_bad_words(
    admin_client, pk_from_news, news_detail_route
):
    bad_words_data = {'text': f'Какой-то text, {choice(BAD_WORDS)}, еще text'}
    url = news_detail_route
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    comments_count = Comment.objects.count()
    expected_comments = 0
    assert comments_count == expected_comments


def test_author_can_edit_comment(
        author_client, pk_from_news, comment, form_data, news_detail_route
):
    original_author = comment.author
    original_news = comment.news

    url = news_detail_route
    response = author_client.post(url, data=form_data)
    expected_url = reverse('news:detail', args=pk_from_news) + '#comments'
    assertRedirects(response, expected_url)

    comment.refresh_from_db()

    assert comment.text != form_data['text'], (
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
        author_client, pk_from_news, pk_from_comment):
    url = reverse('news:delete', args=pk_from_comment)
    response = author_client.post(url)
    expected_url = reverse('news:detail', args=pk_from_news) + '#comments'
    assertRedirects(response, expected_url)
    comments_count = Comment.objects.count()
    expected_comments = 0
    assert comments_count == expected_comments, (
        f'Создано {comments_count} комментариев,'
        f' ожидалось {expected_comments}')


def test_other_user_cant_edit_comment(
        admin_client, pk_from_news, comment, form_data
):
    url = reverse('news:edit', args=[comment.pk])

    old_comment = comment.text
    old_comment_author = comment.author
    old_comment_news = comment.news

    response = admin_client.post(url, data=form_data)

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


def test_other_user_cant_delete_comment(
        admin_client, pk_from_news, pk_from_comment):
    url = reverse('news:delete', args=pk_from_comment)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    expected_comments = 1
    assert comments_count == expected_comments, (
        f'Создано {comments_count} комментариев,'
        f' ожидалось {expected_comments}')
