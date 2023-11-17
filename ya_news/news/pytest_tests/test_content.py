import pytest
from django.urls import reverse
from django.conf import settings

from news.forms import CommentForm

pytestmark = pytest.mark.django_db

HOME_PAGE_ROUTE = reverse('news:home')


@pytest.mark.usefixtures('make_bulk_of_news')
def test_news_count(client):
    url = HOME_PAGE_ROUTE
    res = client.get(url)
    news = res.context['object_list']
    comments_count = len(news)
    msg = ('На главной странице должно находиться не больше '
           f'{settings.NEWS_COUNT_ON_HOME_PAGE} новостей,'
           f' выведено {comments_count}')
    assert comments_count == settings.NEWS_COUNT_ON_HOME_PAGE, msg


@pytest.mark.parametrize(
    'username, is_permitted', ((pytest.lazy_fixture('admin_client'), True),
                               (pytest.lazy_fixture('client'), False))
)
def test_comment_form_availability_for_different_users(
        pk_from_news, username, is_permitted, news_detail_route):
    url = news_detail_route
    res = username.get(url)
    assert (('form' in res.context == is_permitted)
            and isinstance(res.context['form'], CommentForm))


@pytest.mark.usefixtures('make_bulk_of_news')
def test_news_order(client):
    url = HOME_PAGE_ROUTE
    res = client.get(url)
    object_list = res.context['object_list']
    sorted_list_of_news = sorted(object_list,
                                 key=lambda news: news.date,
                                 reverse=True)
    for as_is, to_be in zip(object_list, sorted_list_of_news):
        assert as_is.date == to_be.date, ('Должна быть первой в списке'
                                          f' новость "{to_be.title}" с датой'
                                          f' {to_be.date}, получена'
                                          f' "{as_is.title}" {as_is.date}')


@pytest.mark.usefixtures('make_bulk_of_comments')
def test_comments_order(client, pk_from_news, news_detail_route):
    url = news_detail_route
    res = client.get(url)
    object_list = res.context['news'].comment_set.all()
    sorted_list_of_comments = sorted(object_list,
                                     key=lambda comment: comment.created)
    for as_is, to_be in zip(object_list, sorted_list_of_comments):
        msg = (
            f'Первым в списке должен быть комментарий "{to_be.text}" с датой'
            f' {to_be.created}, получен "{as_is.text}" {as_is.created}')
        assert as_is.created == to_be.created, msg
