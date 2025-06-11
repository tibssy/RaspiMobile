from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Category,
    Product,
    SpecificationType,
    ProductSpecification,
    Review
)
from django.contrib.auth.models import User


class ProductListViewTests(TestCase):
    def setUp(self):
        """
        Set up the test environment with a client, URLs, categories,
        and products.
        """

        self.client = Client()
        self.product_list_url = reverse('product_list')
        self.cat1 = Category.objects.create(name='Category 1', slug='cat1')
        self.cat2 = Category.objects.create(name='Category 2', slug='cat2')

        self.product1 = Product.objects.create(
            name='Product 1',
            price=10.00,
            description='Description 1',
            is_active=True,
        )
        self.product1.categories.add(self.cat1)

        self.product2 = Product.objects.create(
            name='Product 2',
            price=20.00,
            description='Description 2',
            is_active=True,
        )
        self.product2.categories.add(self.cat2)

        self.product3 = Product.objects.create(
            name='Product 3',
            price=15.00,
            description='Description 3',
            is_active=False,
        )

    def test_product_list_view_loads_ok(self):
        """
        Test that the product list page loads with a 200 status code.
        """

        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, 200)

    def test_product_list_view_uses_correct_template(self):
        """
        Test that the product list view uses the
        'products/product_list.html' template.
        """

        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_list.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_product_list_view_displays_only_active_products(self):
        """
        Test that the product list view displays only active products.
        """

        response = self.client.get(self.product_list_url)
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 2)
        self.assertIn(self.product1, products)
        self.assertIn(self.product2, products)
        self.assertNotIn(self.product3, products)

    def test_product_list_view_filters_by_category(self):
        """
        Test that the product list view filters products by category.
        """

        url = self.product_list_url + '?category=cat1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 1)
        self.assertIn(self.product1, products)
        self.assertNotIn(self.product2, products)

    def test_product_list_view_search_products(self):
        """
        Test that the product list view search products
        """

        url = self.product_list_url + '?q=Product%201'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 1)
        self.assertIn(self.product1, products)
        self.assertNotIn(self.product2, products)

    def test_product_list_view_sort_by_newest(self):
        """
        Test that the product list view sort by newest
        """

        Product.objects.create(
            name='Product 4',
            price=15.00,
            description='Description 4',
            is_active=True,
        )
        url = self.product_list_url + '?sort=newest'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products[0].name, 'Product 4')

    def test_product_list_view_sort_by_price_asc(self):
        """
        Test that the product list view sort by price ascending
        """

        url = self.product_list_url + '?sort=price_asc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products[0].name, 'Product 1')

    def test_product_list_view_sort_by_price_desc(self):
        """
        Test that the product list view sort by price descending
        """

        url = self.product_list_url + '?sort=price_desc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products[0].name, 'Product 2')

    def test_product_list_view_sort_by_rating_desc(self):
        """
        Test that the product list view sort by rating descending
        """

        user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        Review.objects.create(
            product=self.product1,
            user=user,
            rating=5,
            comment="Great product!",
            is_approved=True
        )
        url = self.product_list_url + '?sort=rating_desc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products[0].name, 'Product 1')


class ProductDetailViewTests(TestCase):
    def setUp(self):
        """
        Set up test environment with a client, user, category, and product.
        """

        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        self.product.categories.add(self.category)
        self.product_detail_url = reverse(
            'product_detail',
            kwargs={'pk': self.product.pk}
        )

    def test_product_detail_view_loads_ok(self):
        """
        Test that the product detail page loads with a 200 status code.
        """

        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, 200)

    def test_product_detail_view_uses_correct_template(self):
        """
        Test that the product detail view uses the
        'products/product_detail.html' template.
        """

        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_detail.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_product_detail_view_displays_product_details(self):
        """
        Test that the product detail view displays product details.
        """

        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product)

    def test_product_detail_view_displays_related_products(self):
        """
        Test that the product detail view displays related products.
        """

        related_product = Product.objects.create(
            name='Related Product',
            price=25.00,
            description='Related Description',
            is_active=True,
        )
        related_product.categories.add(self.category)

        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            related_product,
            list(response.context['related_products'])
        )


class CategoryModelTests(TestCase):
    def test_category_creation(self):
        """
        Test category model creation
        """

        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.slug, 'test-category')
        self.assertEqual(str(category), 'Test Category')

    def test_category_verbose_name_plural(self):
        """
        Test category verbose name plural
        """

        self.assertEqual(str(Category._meta.verbose_name_plural), 'Categories')


class ProductModelTests(TestCase):
    def setUp(self):
        """
        Set up the category and product models
        """

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_product_creation(self):
        """
        Test product model creation
        """

        product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        product.categories.add(self.category)
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.price, 50.00)
        self.assertEqual(str(product), 'Test Product')

    def test_product_average_rating(self):
        """
        Test product average rating
        """

        product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        Review.objects.create(
            product=product,
            user=user,
            rating=5,
            comment='Great product!',
            is_approved=True
        )
        self.assertEqual(product.average_rating, 5.0)

    def test_product_average_rating_no_reviews(self):
        """
        Test product average rating with no reviews
        """

        product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        self.assertEqual(product.average_rating, 0)

    def test_product_average_rating_only_unapproved_reviews(self):
        """
        Test product average rating with only unapproved reviews
        """

        product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        Review.objects.create(
            product=product,
            user=user,
            rating=5,
            comment='Great product!',
            is_approved=False
        )
        self.assertEqual(product.average_rating, 0)


class SpecificationTypeModelTests(TestCase):
    def test_specification_type_creation(self):
        """
        Test specification type model creation
        """

        specification_type = SpecificationType.objects.create(name='Color')
        self.assertEqual(specification_type.name, 'Color')
        self.assertEqual(str(specification_type), 'Color')


class ProductSpecificationModelTests(TestCase):
    def setUp(self):
        """
        Set up the category, product, and specification type models
        """

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        self.specification_type = SpecificationType.objects.create(
            name='Color')

    def test_product_specification_creation(self):
        """
        Test product specification model creation
        """

        product_specification = ProductSpecification.objects.create(
            product=self.product,
            spec_type=self.specification_type,
            value='Red'
        )
        self.assertEqual(product_specification.product, self.product)
        self.assertEqual(
            product_specification.spec_type,
            self.specification_type
        )
        self.assertEqual(product_specification.value, 'Red')
        self.assertEqual(str(product_specification), 'Color: Red')


class ReviewModelTests(TestCase):
    def setUp(self):
        """
        Set up the category, product, and user models
        """

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test Description',
            is_active=True,
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )

    def test_review_creation(self):
        """
        Test review model creation
        """

        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product!',
            is_approved=True
        )
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great product!')
        self.assertTrue(review.is_approved)
        self.assertIn('Test Product', str(review))
        self.assertIn('testuser', str(review))
        self.assertIn('5', str(review))

    def test_review_verbose_name_plural(self):
        """
        Test review verbose name plural
        """

        self.assertEqual(
            str(Review._meta.verbose_name_plural),
            'Product Reviews'
        )
