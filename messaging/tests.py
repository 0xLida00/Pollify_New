from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from messaging.models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessagingTests(TestCase):
    """Tests for messaging functionality, including inbox, outbox, sending, and reading messages."""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases (improves performance)."""
        cls.client = Client()
        cls.sender = User.objects.create_user(username='sender', password='password')
        cls.recipient = User.objects.create_user(username='recipient', password='password')

        # Create a test message
        cls.message = Message.objects.create(
            sender=cls.sender,
            subject='Test Message',
            body='This is a test message body.'
        )
        cls.message.recipients.add(cls.recipient)

    def setUp(self):
        """Ensure a fresh client session before each test."""
        self.client.logout()

    def test_inbox_view_status_code(self):
        """Test that the inbox view returns a 200 status code for the recipient."""
        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('messaging:inbox'))
        self.assertEqual(response.status_code, 200)

    def test_outbox_view_status_code(self):
        """Test that the outbox view returns a 200 status code for the sender."""
        self.client.login(username='sender', password='password')
        response = self.client.get(reverse('messaging:outbox'))
        self.assertEqual(response.status_code, 200)

    def test_inbox_message_display(self):
        """Test that the inbox view displays the correct message."""
        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('messaging:inbox'))
        self.assertContains(response, 'Test Message')

    def test_outbox_message_display(self):
        """Test that the outbox view displays the correct message."""
        self.client.login(username='sender', password='password')
        response = self.client.get(reverse('messaging:outbox'))
        self.assertContains(response, 'Test Message')

    def test_message_detail_view(self):
        """Test that the message detail view displays the correct message content."""
        self.client.login(username='sender', password='password')

        response = self.client.get(reverse('messaging:message_detail', kwargs={'message_id': self.message.id}))

        # Ensure message is found
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is a test message body.')

    def test_read_message_view(self):
        """Test that the read message view marks a message as read."""
        self.client.login(username='recipient', password='password')
        response = self.client.get(reverse('messaging:read_message', kwargs={'message_id': self.message.id}))

        # Refresh the message instance from the database
        self.message.refresh_from_db()

        # Ensure the message is marked as read
        self.assertTrue(self.message.is_read)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is a test message body.')

    def test_send_message(self):
        """Test that a message can be sent through the compose view."""
        self.client.login(username='sender', password='password')
        response = self.client.post(reverse('messaging:compose_message'), {
            'recipients': [self.recipient.id],
            'subject': 'New Test Message',
            'body': 'This is a new message.'
        })

        # Ensure redirection after successful send
        self.assertEqual(response.status_code, 302)

        # Verify the message was created
        new_message = Message.objects.get(subject='New Test Message')
        self.assertEqual(new_message.sender, self.sender)
        self.assertTrue(new_message.recipients.filter(id=self.recipient.id).exists())

    def test_empty_outbox_message(self):
        """Test that the outbox displays a message when there are no sent messages."""
        Message.objects.filter(sender=self.sender).delete()
        self.assertFalse(Message.objects.filter(sender=self.sender).exists())

        self.client.login(username='sender', password='password')
        response = self.client.get(reverse('messaging:outbox'))
        self.assertEqual(response.status_code, 200)

        # Adjusted expected message based on actual output
        expected_message = "No messages in your outbox."
        self.assertContains(response, expected_message)

    def test_only_recipient_can_read_message(self):
        """Ensure only the recipient can read the message, not others."""
        other_user = User.objects.create_user(username='otheruser', password='password')
        self.client.login(username='otheruser', password='password')
        response = self.client.get(reverse('messaging:message_detail', kwargs={'message_id': self.message.id}))

        # Expecting either 403 Forbidden or 302 Redirect
        self.assertEqual(response.status_code, 403)