from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from polls.models import Poll, Choice, Vote
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class PollTests(TestCase):
    """Tests for Poll functionality including creation, voting, and expiration."""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases to improve performance."""
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.other_user = User.objects.create_user(username='otheruser', password='password')
        
        cls.poll = Poll.objects.create(
            author=cls.user,
            question="What is your favorite programming language?",
            category="Technology"
        )
        cls.choice1 = Choice.objects.create(poll=cls.poll, choice_text="Python", votes_count=0)
        cls.choice2 = Choice.objects.create(poll=cls.poll, choice_text="JavaScript", votes_count=0)

    def setUp(self):
        """Ensure a fresh client session before each test."""
        self.client.logout()

    def test_poll_creation(self):
        """Test that a poll is created successfully with valid data."""
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(self.poll.author, self.user)
        self.assertEqual(self.poll.question, "What is your favorite programming language?")
        self.assertFalse(self.poll.has_expired())

    def test_poll_expiration(self):
        """Test poll expiration logic."""
        self.poll.expires_at = timezone.now() - timedelta(days=1)  # Set expiration date in the past
        self.poll.save()
        self.assertTrue(self.poll.has_expired())

    def test_choice_creation(self):
        """Test that poll choices are created correctly."""
        self.assertEqual(self.poll.choices.count(), 2)
        self.assertEqual(self.choice1.choice_text, "Python")
        self.assertEqual(self.choice2.choice_text, "JavaScript")

    def test_vote_creation(self):
        """Test voting functionality and ensure the vote count increases."""
        self.client.login(username='testuser', password='password')
        vote = Vote.objects.create(poll=self.poll, choice=self.choice1, voter=self.user)
        
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(vote.poll, self.poll)
        self.assertEqual(vote.choice, self.choice1)
        self.assertEqual(vote.voter, self.user)

    def test_prevent_double_voting(self):
        """Ensure that a user cannot vote twice on the same poll."""
        self.client.login(username='testuser', password='password')
        Vote.objects.create(poll=self.poll, choice=self.choice1, voter=self.user)

        response = self.client.post(reverse('vote_poll', kwargs={'pk': self.poll.pk}), {
            'choice': self.choice2.id
        })

        # Expect a redirect due to error message
        self.assertEqual(response.status_code, 302)

        # Ensure no second vote was created
        self.assertEqual(Vote.objects.count(), 1)

    def test_vote_poll_view(self):
        """Test the vote_poll view and ensure correct voting behavior."""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('vote_poll', kwargs={'pk': self.poll.pk}), {
            'choice': self.choice1.id
        })

        self.assertEqual(response.status_code, 302)  # Redirect after successful vote
        self.choice1.refresh_from_db()
        self.assertEqual(self.choice1.votes_count, 1)

    def test_poll_str_representation(self):
        """Test the string representation of a poll."""
        self.assertEqual(str(self.poll), "What is your favorite programming language?")

    def test_choice_str_representation(self):
        """Test the string representation of a choice."""
        self.assertEqual(str(self.choice1), "Python")

    def test_poll_edit_by_author(self):
        """Ensure a poll's author can edit the poll."""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('poll_edit', kwargs={'pk': self.poll.pk}), {
            'description': "Updated description",
            'expires_at': timezone.now() + timedelta(days=5)
        })

        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.description, "Updated description")

    def test_poll_edit_by_non_author(self):
        """Ensure a non-author cannot edit the poll."""
        self.client.login(username='otheruser', password='password')
        response = self.client.post(reverse('poll_edit', kwargs={'pk': self.poll.pk}), {
            'description': "Unauthorized update"
        })

        # Expect a 403 Forbidden response since only authors can edit their polls
        self.assertEqual(response.status_code, 403)

    def test_poll_delete_by_author(self):
        """Ensure a poll's author can delete their poll."""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('poll_delete', kwargs={'pk': self.poll.pk}))

        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertFalse(Poll.objects.filter(pk=self.poll.pk).exists())

    def test_poll_delete_by_non_author(self):
        """Ensure a non-author cannot delete the poll."""
        self.client.login(username='otheruser', password='password')
        response = self.client.post(reverse('poll_delete', kwargs={'pk': self.poll.pk}))

        # Ensure the response now correctly returns 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Ensure the poll still exists
        self.assertTrue(Poll.objects.filter(pk=self.poll.pk).exists())

    def test_toggle_follow_author(self):
        """Test the follow/unfollow functionality for poll authors."""
        self.client.login(username='otheruser', password='password')
        
        # Follow request
        response = self.client.post(reverse('toggle_follow', kwargs={'user_id': self.user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'follow')

        # Unfollow request
        response = self.client.post(reverse('toggle_follow', kwargs={'user_id': self.user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'unfollow')

    def test_home_view(self):
        """Test that the home view loads correctly and contains recent polls."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is your favorite programming language?")