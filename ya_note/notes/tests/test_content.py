from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.users_notes = (
            (cls.author, True),
            (cls.reader, False),
        )

    def test_notes_list_for_different_users(self):
        url = reverse('notes:list')
        for user, note_in_list in self.users_notes:
            with self.subTest(user=user.username, note_in_list=note_in_list):
                response = (self.author_client.get(url) if user == self.author
                            else self.reader_client.get(url))
                note_in_object_list = self.note in response.context[
                    'object_list'
                ]
                self.assertEqual(note_in_object_list, note_in_list)

    def test_pages_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for page, args in urls:
            with self.subTest(page=page):
                url = reverse(page, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
