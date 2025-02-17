from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from notifications.models import Notification
from polls.models import Poll

User = get_user_model()

class NotificationTests(TestCase):
    """Tests for Notification functionality, including creation, marking as read, and access control."""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases to improve performance."""
        cls.actor = User.objects.create_user(username='actor', password='password')
        cls.recipient = User.objects.create_user(username='recipient', password='password')
        cls.other_user = User.objects.create_user(username='other_user', password='password')
        cls.poll = Poll.objects.create(author=cls.actor, question="Sample Poll")

    def setUp(self):
        """Ensure a fresh client session before each test."""
        self.client.logout()

    def test_notification_creation_with_target_poll(self):
        """Test that a notification with a target poll is correctly created."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='created a poll',
            target_poll=self.poll
        )

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(notification.recipient, self.recipient)
        self.assertEqual(notification.verb, 'created a poll')
        self.assertEqual(notification.target_poll, self.poll)
        self.assertFalse(notification.is_read)

    def test_notification_creation_without_target_poll(self):
        """Test that a notification without a target poll is correctly created."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='liked a post'
        )

        self.assertEqual(Notification.objects.count(), 1)
        self.assertIsNone(notification.target_poll)

    def test_mark_notification_as_read(self):
        """Test marking a notification as read."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='followed you'
        )

        # Ensure default is unread
        self.assertFalse(notification.is_read)

        # Mark as read
        notification.is_read = True
        notification.save()

        # Check if the notification is updated
        self.assertTrue(Notification.objects.get(id=notification.id).is_read)

    def test_notification_str_representation(self):
        """Test the string representation of a notification."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='voted on a poll',
            target_poll=self.poll
        )

        expected_str = f"{self.actor} voted on a poll for {self.recipient}"
        self.assertEqual(str(notification), expected_str)

    def test_notification_access_by_recipient(self):
        """Ensure that only the recipient can access their notifications."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='commented on a poll'
        )

        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('notification_detail', kwargs={'notification_id': notification.id}))
        self.assertEqual(response.status_code, 200)

    def test_notification_access_by_non_recipient(self):
        """Ensure that a user who is not the recipient cannot access the notification."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='shared a poll'
        )

        self.client.login(username='other_user', password='password')
        response = self.client.get(reverse('notification_detail', kwargs={'notification_id': notification.id}))

        # Expecting a 403 Forbidden instead of 404
        self.assertEqual(response.status_code, 403)  # Unauthorized access should be denied

    def test_mark_notification_as_read_view(self):
        """Test marking a notification as read through the view."""
        notification = Notification.objects.create(
            actor=self.actor,
            recipient=self.recipient,
            verb='liked a comment'
        )

        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('mark_notification_as_read', kwargs={'notification_id': notification.id}))

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)  # Ensure the notification is now read
        self.assertEqual(response.status_code, 302)

    def test_mark_all_notifications_as_read_view(self):
        """Test marking all notifications as read."""
        Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='liked your poll', is_read=False)
        Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='voted on your poll', is_read=False)

        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('mark_all_notifications_as_read'))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notification.objects.filter(recipient=self.recipient, is_read=False).exists())

    def test_notifications_list_pagination(self):
        """Test notification list pagination."""
        for _ in range(15):  # Create 15 notifications
            Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='posted a comment')

        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('notifications_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pagination")  # Check if pagination controls appear

    def test_unread_notifications_count(self):
        """Test unread notifications count in the view."""
        Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='posted a comment', is_read=False)
        Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='liked your poll', is_read=False)
        Notification.objects.create(actor=self.actor, recipient=self.recipient, verb='shared your post', is_read=True)

        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('notifications_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")