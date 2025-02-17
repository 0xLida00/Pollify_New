from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from polls.models import Poll, Vote, Choice
from comments.models import Comment
from django.contrib.auth import get_user_model

User = get_user_model()

class FrontendTests(TestCase):
    """Tests for the frontend functionality, including polls, votes, and comments."""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases (improves performance)."""
        cls.client = Client()
        cls.author = User.objects.create_user(username='pollauthor', password='password')
        cls.user = User.objects.create_user(username='testuser', password='password')

        # Create sample polls
        cls.poll1 = Poll.objects.create(author=cls.author, question='Sample Poll 1', category='Technology')
        cls.poll2 = Poll.objects.create(author=cls.author, question='Sample Poll 2', category='Sports')

        # Add choices for voting
        choice_yes = Choice.objects.create(poll=cls.poll1, choice_text="Yes")
        choice_no = Choice.objects.create(poll=cls.poll1, choice_text="No")

        # Add votes to polls to simulate trending
        Vote.objects.create(poll=cls.poll1, choice=choice_yes, voter=cls.user)
        Vote.objects.create(poll=cls.poll1, choice=choice_no, voter=cls.author)

        # Create comments
        cls.comment1 = Comment.objects.create(poll=cls.poll1, author=cls.user, content="This is a comment on Poll 1.")
        cls.comment2 = Comment.objects.create(poll=cls.poll2, author=cls.user, content="Another comment on Poll 2.")

    def setUp(self):
        """Ensure a fresh client session before each test."""
        self.client.logout()

    def test_home_view_status_code(self):
        """Test that the home view returns a 200 status code."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_trending_polls_display(self):
        """Test that trending polls are displayed correctly on the home page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Poll 1")
        self.assertContains(response, "2 Votes")

    def test_recent_polls_display(self):
        """Test that recent polls are displayed correctly."""
        response = self.client.get(reverse('home'))
        self.assertContains(response, "Sample Poll 1")
        self.assertContains(response, "Sample Poll 2")

    def test_recent_comments_display(self):
        """Test that recent comments are displayed correctly."""
        response = self.client.get(reverse('home'))
        self.assertContains(response, "This is a comment on Poll 1.")
        self.assertContains(response, "Another comment on Poll 2.")

    def test_empty_trending_polls(self):
        """Test that a message is displayed when there are no trending polls."""
        Poll.objects.all().delete()
        self.assertFalse(Poll.objects.exists())

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No trending polls at the moment.")

    def test_empty_recent_polls(self):
        """Test that a message is displayed when there are no recent polls."""
        Poll.objects.all().delete()
        self.assertFalse(Poll.objects.exists())

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls available yet.")

    def test_empty_recent_comments(self):
        """Test that a message is displayed when there are no recent comments."""
        Comment.objects.all().delete()
        self.assertFalse(Comment.objects.exists())

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        # Ensure the exact expected message matches the template
        expected_message = "No comments yet. Join the conversation!"
        self.assertContains(response, expected_message)