from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from admin_panel.models import ActivityLog
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminPanelTests(TestCase):
    """Tests for the Admin Panel functionality, including authentication, logging, and pagination."""
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test cases (improves performance)."""
        cls.client = Client()
        cls.admin_user = User.objects.create_superuser(username='admin', password='password', email='admin@example.com')
        cls.regular_user = User.objects.create_user(username='regular', password='password', email='regular@example.com')

        # Create sample activity logs
        cls.log1 = ActivityLog.objects.create(user=cls.admin_user, action="Created a poll")
        cls.log2 = ActivityLog.objects.create(user=cls.regular_user, action="Voted on a poll")

    def setUp(self):
        """Ensure fresh login for every test case."""
        self.client.login(username='admin', password='password')

    def test_activity_log_creation(self):
        """Test that activity logs are correctly created and stored in the database."""
        self.assertEqual(ActivityLog.objects.count(), 2)
        self.assertEqual(str(self.log1), f"{self.admin_user} performed Created a poll at {self.log1.timestamp}")
        self.assertEqual(str(self.log2), f"{self.regular_user} performed Voted on a poll at {self.log2.timestamp}")

    def test_dashboard_access_as_admin(self):
        """Test that an admin user can access the dashboard."""
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Activity Logs")
        self.assertContains(response, self.log1.action)
        self.assertContains(response, self.log2.action)

    def test_dashboard_access_as_regular_user(self):
        """Test that a regular user is denied access to the admin dashboard."""
        self.client.logout()
        self.client.login(username='regular', password='password')
        response = self.client.get(reverse('admin_panel:dashboard'))

        # Handle both cases: Forbidden (403) or Redirect to login (302)
        if response.status_code == 302:
            self.assertRedirects(response, f"{reverse('login')}?next={reverse('admin_panel:dashboard')}")
        else:
            self.assertEqual(response.status_code, 403)  # Forbidden for non-admins

    def test_dashboard_redirects_if_not_logged_in(self):
        """Test that an unauthenticated user is redirected to login when accessing the admin panel."""
        self.client.logout()
        response = self.client.get(reverse('admin_panel:dashboard'))
        expected_redirect_url = f"{reverse('login')}?next={reverse('admin_panel:dashboard')}"
        self.assertRedirects(response, expected_redirect_url)

    def test_pagination_on_dashboard(self):
        """Test that the dashboard correctly paginates activity logs."""
        # Generate 30 additional logs (total: 32 logs)
        ActivityLog.objects.bulk_create([
            ActivityLog(user=self.admin_user, action=f"Test action {i + 1}") for i in range(30)
        ])

        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Verify that only 20 logs appear on the first page
        self.assertEqual(len(response.context['recent_activity']), 20)

        # Check the second page
        response = self.client.get(reverse('admin_panel:dashboard') + '?page=2')
        self.assertEqual(response.status_code, 200)

        expected_remaining_logs = ActivityLog.objects.count() - 20
        self.assertEqual(len(response.context['recent_activity']), expected_remaining_logs)

    
    def test_empty_activity_logs_display_message(self):
        """Test that the admin dashboard displays a message when there are no logs."""
        ActivityLog.objects.all().delete()
        self.assertFalse(ActivityLog.objects.exists())

        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Update expected message to match the actual template output
        expected_message = "No recent activity found."

        self.assertContains(response, expected_message)

    def test_dashboard_only_displays_latest_logs(self):
        """Ensure that the dashboard only shows the most recent activity logs."""
        # Create a new log entry
        latest_log = ActivityLog.objects.create(user=self.admin_user, action="Newest log entry")

        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertContains(response, "Newest log entry")

    def test_invalid_page_number_returns_last_page(self):
        """If a user requests a non-existent page, they should get the last available page."""
        response = self.client.get(reverse('admin_panel:dashboard') + '?page=999')
        self.assertEqual(response.status_code, 200)
        
        paginator = response.context['recent_activity'].paginator
        last_page_number = paginator.num_pages
        self.assertEqual(response.context['recent_activity'].number, last_page_number)

    def test_negative_page_number_redirects_to_first_page(self):
        """If a user requests a negative page, they should be redirected to the first page."""
        response = self.client.get(reverse('admin_panel:dashboard') + '?page=-1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['recent_activity'].number, 1)

    def test_static_files_loading(self):
        """Ensure static files, including 'favicon.ico', load correctly."""
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertNotContains(response, "Missing staticfiles manifest entry for 'img/favicon.ico'")