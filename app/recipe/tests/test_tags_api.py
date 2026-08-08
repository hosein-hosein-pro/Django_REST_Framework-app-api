"""
Tests for Tag APIs.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Return detail URL for given tag."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password,
    )


class PublicTagsApiTests(TestCase):
    """Test unauthenticated tag API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated tag API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags."""

        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test tags are returned for the authenticated user."""

        other_user = create_user(
            email="other@example.com",
            password="password123",
        )

        Tag.objects.create(user=other_user, name="Fruit")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating tag with PUT."""
        tag = Tag.objects.create(user=self.user, name="Vegan")

        payload = {
            "name": "New name",
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag with DELETE."""
        tag = Tag.objects.create(user=self.user, name="breakfast")
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test filtering tags by tags."""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            title="Apple Orange",
            time_minutes=10,
            price=Decimal(2.50),
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """test filtering tags by tags"""
        tag = Tag.objects.create(user=self.user, name="Eggs")
        Tag.objects.create(user=self.user, name="Lentils")
        recipe1 = Recipe.objects.create(
            title="Eggs benedict",
            time_minutes=60,
            price=Decimal(7.00),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="herb eggs",
            time_minutes=20,
            price=Decimal(4.00),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})
        self.assertEqual(len(res.data), 1)