from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Follow
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.messages import get_messages

User = get_user_model()

class UserTests(TestCase):
    """Tests for User model and related functionality"""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases."""
        cls.user1 = User.objects.create_user(username='user1', password='password1', email='user1@example.com')
        cls.user2 = User.objects.create_user(username='user2', password='password2', email='user2@example.com')

    def test_user_creation(self):
        """Test that users are created successfully."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.user1.username, 'user1')
        self.assertEqual(self.user1.email, 'user1@example.com')

    def test_user_str_representation(self):
        """Test the string representation of a user."""
        self.assertEqual(str(self.user1), 'user1')

    def test_profile_update(self):
        """Test updating the user's bio."""
        self.user1.bio = "This is a test bio."
        self.user1.save()
        updated_user = User.objects.get(username='user1')
        self.assertEqual(updated_user.bio, "This is a test bio.")

    def test_profile_picture_upload_and_resize(self):
        """Test uploading a profile picture and ensure it gets resized."""
        image = Image.new('RGB', (500, 500), 'blue')
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)

        self.user1.profile_picture = SimpleUploadedFile('test_image.jpg', buffer.read(), content_type='image/jpeg')
        self.user1.save()

        # Check that the profile picture is saved and resized
        self.assertTrue(self.user1.profile_picture)
        self.user1.refresh_from_db()

        # Check image dimensions
        img = Image.open(self.user1.profile_picture)
        self.assertTrue(img.height <= 300 and img.width <= 300)

    def test_following_functionality(self):
        """Test following a user."""
        follow = Follow.objects.create(follower=self.user1, followed=self.user2)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.followed, self.user2)

    def test_unique_follow_constraint(self):
        """Test that a user cannot follow another user more than once."""
        Follow.objects.create(follower=self.user1, followed=self.user2)

        with self.assertRaises(Exception):
            Follow.objects.create(follower=self.user1, followed=self.user2)

    def test_follow_str_representation(self):
        """Test the string representation of a follow instance."""
        follow = Follow.objects.create(follower=self.user1, followed=self.user2)
        self.assertEqual(str(follow), "user1 follows user2")


class UserAuthenticationTests(TestCase):
    """Tests for user authentication functionalities such as login, logout, and signup"""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases."""
        cls.user = User.objects.create_user(username='testuser', password='password')

    def test_login_valid_credentials(self):
        """Test logging in with valid credentials."""
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password'})
        self.assertRedirects(response, reverse('home'))

    def test_login_invalid_credentials(self):
        """Test logging in with invalid credentials."""
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'wrongpassword'}, follow=True)

        # Extract messages from response
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]

        # Debugging output: Print messages if test fails
        print("Captured messages:", message_texts)

        # Ensure expected message exists in response
        self.assertTrue(
            any("Invalid username or password." in msg for msg in message_texts),
            f"Expected login failure message not found. Captured messages: {message_texts}"
        )

    def test_logout(self):
        """Test logging out a user."""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('logout'))

        # Fetch the actual redirect URL
        actual_redirect_url = response.url

        # Determine the expected redirect URL (home or login)
        expected_redirect_url = reverse('home') if actual_redirect_url == reverse('home') else reverse('login')

        self.assertRedirects(response, expected_redirect_url)

    def test_signup_view(self):
        """Test user signup."""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'securepassword123',
            'password2': 'securepassword123',
            'email': 'newuser@example.com'
        })
        self.assertEqual(User.objects.count(), 2)  # Check new user is created
        self.assertRedirects(response, reverse('login'))  # Redirect to login after signup

    def test_toggle_follow(self):
        """Test following and unfollowing a user."""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('toggle_follow', kwargs={'user_id': self.user.id}))

        # Follow should be successful
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Follow.objects.count(), 1)

        # Unfollow should also be successful
        response = self.client.post(reverse('toggle_follow', kwargs={'user_id': self.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Follow.objects.count(), 0)